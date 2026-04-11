"""
Data retriever: scaricamento automatico dati da FSTATS (API) e FPEDIA (scraping).

Supporta:
- Refresh automatico basato sull'età del file (config.DATA_MAX_AGE_HOURS)
- Flag force per forzare il riscrittura
- Retry con backoff esponenziale
- Validazione dei dati scaricati
"""

import os
import time
from datetime import datetime, timedelta
from random import randint

import concurrent.futures
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

from ..utils import config

load_dotenv()


# ---------------------------------------------------------------------------
# Utilità
# ---------------------------------------------------------------------------

def _is_stale(filepath: str, max_age_hours: int = None) -> bool:
    """Ritorna True se il file non esiste o è più vecchio di max_age_hours."""
    if max_age_hours is None:
        max_age_hours = config.DATA_MAX_AGE_HOURS
    if not os.path.exists(filepath):
        return True
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
    return datetime.now() - mtime > timedelta(hours=max_age_hours)


def _request_with_retry(method: str, url: str, max_retries: int = None, **kwargs) -> requests.Response:
    """Esegue una richiesta HTTP con retry e backoff esponenziale."""
    if max_retries is None:
        max_retries = config.MAX_RETRIES
    last_exc = None
    for attempt in range(max_retries):
        try:
            resp = requests.request(method, url, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                wait = config.RETRY_BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {exc}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"All {max_retries} attempts failed for {url}: {exc}")
    raise last_exc


# ---------------------------------------------------------------------------
# FSTATS (fantagoat API)
# ---------------------------------------------------------------------------

def fetch_fstats_data(force: bool = False) -> pd.DataFrame | None:
    """
    Scarica i dati giocatori dall'API FSTATS (fantagoat).

    Args:
        force: se True, scarica anche se il file è recente.

    Returns:
        DataFrame con i dati scaricati, o None se il download è saltato / fallito.
    """
    if not force and not _is_stale(config.PLAYERS_CSV):
        logger.info("FSTATS: dati aggiornati, download saltato.")
        return pd.read_csv(config.PLAYERS_CSV, sep=";")

    user = os.getenv("FSTATS_MAIL")
    password = os.getenv("FSTATS_PASSWORD")
    if not user or not password:
        logger.error("FSTATS: credenziali non trovate in .env (FSTATS_MAIL / FSTATS_PASSWORD).")
        return None

    # 1. Login
    logger.info("FSTATS: login in corso...")
    login_payload = {"username": user, "password": password}
    try:
        resp = _request_with_retry(
            "POST", config.FSTATS_LOGIN_URL,
            json=login_payload,
            headers={"content-type": "application/json"},
        )
        token = resp.json()["access_token"]
        logger.info("FSTATS: login riuscito.")
    except (requests.RequestException, KeyError) as exc:
        logger.error(f"FSTATS: login fallito: {exc}")
        return None

    # 2. Download dati giocatori
    logger.info("FSTATS: scaricamento dati giocatori...")
    try:
        resp = _request_with_retry(
            "GET", config.FSTATS_PLAYERS_URL,
            headers={"authorization": f"Bearer {token}"},
        )
        players = resp.json()["results"]
    except (requests.RequestException, KeyError) as exc:
        logger.error(f"FSTATS: download fallito: {exc}")
        return None

    df = pd.DataFrame(players)

    # 3. Validazione
    if df.empty:
        logger.error("FSTATS: nessun giocatore ricevuto dall'API.")
        return None
    if len(df) < 100:
        logger.warning(f"FSTATS: solo {len(df)} giocatori ricevuti (attesi ~500). Possibile problema API.")

    # 4. Salva
    os.makedirs(os.path.dirname(config.PLAYERS_CSV), exist_ok=True)
    df.to_csv(config.PLAYERS_CSV, index=False, sep=";")
    logger.info(f"FSTATS: {len(df)} giocatori salvati in {config.PLAYERS_CSV}")
    return df


# ---------------------------------------------------------------------------
# FPEDIA (fantacalciopedia.com scraping)
# ---------------------------------------------------------------------------

def _get_player_urls(force: bool = False) -> list[str]:
    """Recupera la lista di URL dei giocatori da FPEDIA."""
    if not force and os.path.exists(config.GIOCATORI_URLS_FILE):
        logger.info("FPEDIA: caricamento URL dalla cache.")
        with open(config.GIOCATORI_URLS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]

    logger.info("FPEDIA: scraping URL giocatori dalle pagine ruolo...")
    urls: list[str] = []
    for ruolo in tqdm(config.RUOLI, desc="Ruoli FPEDIA"):
        page_url = config.FPEDIA_URL + ruolo.lower() + "/"
        try:
            resp = _request_with_retry("GET", page_url, headers=config.HEADERS)
            soup = BeautifulSoup(resp.content, "html.parser")
            for article in soup.find_all("article"):
                link = article.find("a")
                if link and link.get("href"):
                    urls.append(link["href"])
        except requests.RequestException as exc:
            logger.error(f"FPEDIA: errore scraping ruolo '{ruolo}': {exc}")

    if not urls:
        logger.error("FPEDIA: nessun URL giocatore trovato. Struttura del sito cambiata?")
        return []

    with open(config.GIOCATORI_URLS_FILE, "w") as f:
        f.write("\n".join(urls))
    logger.info(f"FPEDIA: {len(urls)} URL salvati.")
    return urls


def _scrape_player(url: str) -> dict | None:
    """Scrapea la pagina di un singolo giocatore FPEDIA."""
    time.sleep(randint(1000, 5000) / 1000)  # rate limiting
    try:
        resp = _request_with_retry("GET", url.strip(), headers=config.HEADERS)
        soup = BeautifulSoup(resp.content, "html.parser")
    except requests.RequestException as exc:
        logger.warning(f"FPEDIA: errore pagina {url}: {exc}")
        return None

    attr: dict = {}
    try:
        attr["Nome"] = soup.select_one("h1").get_text().strip()
    except AttributeError:
        logger.warning(f"FPEDIA: nome non trovato per {url}")
        return None

    # Punteggio /100
    try:
        sel = "div.col_one_fourth:nth-of-type(1) span.stickdan"
        attr["Punteggio"] = soup.select_one(sel).text.strip().replace("/100", "")
    except AttributeError:
        attr["Punteggio"] = ""

    # Fantamedie storiche
    sel = "\tdiv.col_one_fourth:nth-of-type(n+2) div"
    elements = soup.select(sel)
    for el in elements:
        try:
            media = el.find("span").text.strip()
            anno = el.find("strong").text.split(" ")[-1].strip()
            attr[f"Fantamedia anno {anno}"] = media
        except AttributeError:
            pass

    # Statistiche ultimo anno
    try:
        sel = "div.col_one_third:nth-of-type(2) div"
        stats_el = soup.select_one(sel)
        if stats_el:
            keys = [e.text.strip().replace(":", "") for e in stats_el.find_all("strong")]
            vals = [e.text.strip() for e in stats_el.find_all("span")]
            attr.update(dict(zip(keys, vals)))
    except Exception:
        pass

    # Previsioni
    try:
        sel = ".col_one_third.col_last div"
        pred_el = soup.select_one(sel)
        if pred_el:
            keys = [e.text.strip().replace(":", "") for e in pred_el.find_all("strong")]
            vals = [e.text.strip() for e in pred_el.find_all("span")]
            attr.update(dict(zip(keys, vals)))
    except Exception:
        pass

    # Ruolo
    try:
        attr["Ruolo"] = soup.select_one(".label12 span.label").get_text().strip()
    except AttributeError:
        attr["Ruolo"] = ""

    # Skills
    attr["Skills"] = [el.text for el in soup.select("span.stickdanpic")]

    # Buon investimento / Resistenza infortuni
    progress = soup.select("div.progress-percent")
    try:
        attr["Buon investimento"] = progress[2].text.replace("%", "")
    except (IndexError, AttributeError):
        attr["Buon investimento"] = ""
    try:
        attr["Resistenza infortuni"] = progress[3].text.replace("%", "")
    except (IndexError, AttributeError):
        attr["Resistenza infortuni"] = ""

    # Consigliato / Infortunato
    try:
        inf_img = soup.select_one("img.inf_calc")
        title = inf_img.get("title", "") if inf_img else ""
        attr["Consigliato prossima giornata"] = "Consigliato per la giornata" in title
        attr["Infortunato"] = "Infortunato" in title
    except Exception:
        attr["Consigliato prossima giornata"] = False
        attr["Infortunato"] = False

    # Nuovo acquisto
    attr["Nuovo acquisto"] = soup.select_one("span.new_calc") is not None

    # Squadra
    try:
        sel = (
            "#content > div > div.section.nobg.nomargin > div > div > div:nth-child(2) "
            "> div.col_three_fifth > div.promo.promo-border.promo-light.row "
            "> div:nth-child(3) > div:nth-child(1) > div > img"
        )
        attr["Squadra"] = soup.select_one(sel).get("title").split(":")[1].strip()
    except (AttributeError, IndexError):
        attr["Squadra"] = ""

    # Trend
    try:
        sel = "\tdiv.col_one_fourth:nth-of-type(n+2) div"
        trend_class = soup.select(sel)[0].find("i").get("class")[1]
        attr["Trend"] = "UP" if trend_class == "icon-arrow-up" else "DOWN"
    except Exception:
        attr["Trend"] = "STABLE"

    # Presenze campionato corrente
    try:
        sel = "div.col_one_fourth:nth-of-type(2) span.rouge"
        attr["Presenze campionato corrente"] = soup.select_one(sel).text
    except AttributeError:
        attr["Presenze campionato corrente"] = ""

    return attr


def fetch_fpedia_data(force: bool = False) -> pd.DataFrame | None:
    """
    Scrapea tutti i giocatori da FPEDIA.

    Args:
        force: se True, riscrape anche se il file è recente.

    Returns:
        DataFrame con i dati, o None se il download fallisce.
    """
    if not force and not _is_stale(config.GIOCATORI_CSV):
        logger.info("FPEDIA: dati aggiornati, scraping saltato.")
        return pd.read_csv(config.GIOCATORI_CSV)

    urls = _get_player_urls(force=force)
    if not urls:
        return None

    logger.info(f"FPEDIA: scraping {len(urls)} giocatori...")
    players: list[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        future_map = {executor.submit(_scrape_player, url): url for url in urls}
        for future in tqdm(concurrent.futures.as_completed(future_map), total=len(urls), desc="FPEDIA"):
            url = future_map[future]
            try:
                result = future.result()
                if result:
                    players.append(result)
            except Exception as exc:
                logger.error(f"FPEDIA: errore per {url}: {exc}")

    if not players:
        logger.error("FPEDIA: nessun giocatore scaricato.")
        return None

    df = pd.DataFrame(players)

    # Validazione
    if len(df) < 100:
        logger.warning(f"FPEDIA: solo {len(df)} giocatori (attesi ~500). Possibile problema.")

    os.makedirs(os.path.dirname(config.GIOCATORI_CSV), exist_ok=True)
    df.to_csv(config.GIOCATORI_CSV, index=False)
    logger.info(f"FPEDIA: {len(df)} giocatori salvati in {config.GIOCATORI_CSV}")
    return df


# ---------------------------------------------------------------------------
# Interfaccia pubblica
# ---------------------------------------------------------------------------

def fetch_all(force: bool = False) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Scarica dati da entrambe le fonti. Ritorna (df_fstats, df_fpedia)."""
    df_fstats = fetch_fstats_data(force=force)
    df_fpedia = fetch_fpedia_data(force=force)
    return df_fstats, df_fpedia

