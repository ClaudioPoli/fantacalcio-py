"""
Data processor: pulizia e normalizzazione dei dati da FSTATS e FPEDIA.

Responsabilità:
- Conversione tipi e gestione valori mancanti
- Normalizzazione colonne a nomi consistenti
- Normalizzazione ruoli al formato standard (P/D/C/A)
- Caricamento CSV con gestione errori
"""

import os
import pandas as pd
from loguru import logger

from ..utils import config


# ---------------------------------------------------------------------------
# Caricamento
# ---------------------------------------------------------------------------

def load_fstats() -> pd.DataFrame:
    """Carica il CSV FSTATS, ritorna DataFrame vuoto se non disponibile."""
    if not os.path.exists(config.PLAYERS_CSV) or os.path.getsize(config.PLAYERS_CSV) == 0:
        logger.warning(f"File FSTATS non trovato o vuoto: {config.PLAYERS_CSV}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(config.PLAYERS_CSV, sep=";")
        logger.info(f"FSTATS: caricati {len(df)} giocatori.")
        return df
    except Exception as exc:
        logger.error(f"Errore caricamento FSTATS: {exc}")
        return pd.DataFrame()


def load_fpedia() -> pd.DataFrame:
    """Carica il CSV FPEDIA, ritorna DataFrame vuoto se non disponibile."""
    if not os.path.exists(config.GIOCATORI_CSV) or os.path.getsize(config.GIOCATORI_CSV) == 0:
        logger.warning(f"File FPEDIA non trovato o vuoto: {config.GIOCATORI_CSV}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(config.GIOCATORI_CSV)
        logger.info(f"FPEDIA: caricati {len(df)} giocatori.")
        return df
    except Exception as exc:
        logger.error(f"Errore caricamento FPEDIA: {exc}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Normalizzazione ruoli
# ---------------------------------------------------------------------------

def _normalize_role(role_value: str) -> str:
    """Normalizza un ruolo al formato standard P/D/C/A."""
    if pd.isna(role_value):
        return ""
    role_str = str(role_value).strip()
    return config.ROLE_MAP.get(role_str, role_str)


# ---------------------------------------------------------------------------
# Processing FSTATS
# ---------------------------------------------------------------------------

def process_fstats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa e pulisce i dati FSTATS.

    Operazioni:
    - Rinomina colonne per consistenza
    - Normalizza ruoli
    - Converte colonne numeriche
    - Gestisce valori -1 (dato non disponibile in FSTATS)
    """
    if df.empty:
        return df

    logger.info("Processing dati FSTATS...")
    df = df.copy()

    # Rinomina colonne principali
    rename_map = {
        "name": "Nome",
        "team": "Squadra",
        "fantacalcioPosition": "Ruolo_raw",
        "appearances": "Presenze",
        "pagella": "Media_voto",
        "fantacalcioRanking": "Fanta_media",
        "fantacalcioFantaindex": "Fanta_index",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Normalizza ruoli
    if "Ruolo_raw" in df.columns:
        df["Ruolo"] = df["Ruolo_raw"].apply(_normalize_role)

    # Colonne numeriche da convertire
    numeric_cols = [
        "goals", "assists", "Presenze", "Media_voto", "Fanta_media",
        "Fanta_index", "yellowCards", "redCards",
        "xgFromOpenPlays", "xA", "goals90min",
        "matchesInStart", "mins_played",
        "gkPenaltiesSaved", "gkCleanSheets", "gkConcededGoals",
        "successfulPenalties", "penalties",
    ] + config.TECHNICAL_INDICES

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # -1 in FSTATS = dato non disponibile → NaN
            df[col] = df[col].replace(-1, pd.NA)

    # Estrai nome squadra dal dict-like string se necessario
    if "Squadra" in df.columns:
        df["Squadra"] = df["Squadra"].apply(_extract_team_name)

    logger.info(f"FSTATS: processing completato. {len(df)} giocatori, {len(df.columns)} colonne.")
    return df


def _extract_team_name(val) -> str:
    """Estrae il nome squadra dal formato FSTATS (es. \"{'name': 'inter'}\")."""
    if pd.isna(val):
        return ""
    s = str(val)
    if "'name'" in s:
        try:
            # Formato: {'uuid': '...', 'name': 'inter'}
            start = s.index("'name':") + len("'name':")
            rest = s[start:].strip().strip("'\" }")
            # Prendi fino al prossimo apice o fine
            name = rest.split("'")[1] if "'" in rest else rest
            return name.strip().title()
        except (ValueError, IndexError):
            pass
    return s.strip().title()


# ---------------------------------------------------------------------------
# Processing FPEDIA
# ---------------------------------------------------------------------------

def process_fpedia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa e pulisce i dati FPEDIA.

    Operazioni:
    - Normalizza ruoli
    - Converte colonne numeriche
    - Gestisce valori mancanti
    """
    if df.empty:
        return df

    logger.info("Processing dati FPEDIA...")
    df = df.copy()

    # Normalizza ruoli
    if "Ruolo" in df.columns:
        df["Ruolo"] = df["Ruolo"].apply(_normalize_role)

    # Colonne numeriche
    numeric_cols = [
        "Punteggio", "Buon investimento", "Resistenza infortuni",
        "Presenze campionato corrente", "Nuovo acquisto",
    ]
    # Aggiungi colonne fantamedia dinamiche
    fm_cols = [c for c in df.columns if c.startswith("Fantamedia anno")]
    numeric_cols.extend(fm_cols)
    # Aggiungi colonne di statistiche che possono variare
    extra_num = ["Presenze 2024-2025", "Fanta Media 2024-2025", "FM su tot gare 2024-2025"]
    numeric_cols.extend(extra_num)

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Skills: assicurati che sia stringa
    if "Skills" not in df.columns:
        df["Skills"] = "[]"
    else:
        df["Skills"] = df["Skills"].fillna("[]")

    # Squadra: normalizza
    if "Squadra" in df.columns:
        df["Squadra"] = df["Squadra"].str.strip().str.title()

    logger.info(f"FPEDIA: processing completato. {len(df)} giocatori, {len(df.columns)} colonne.")
    return df


# ---------------------------------------------------------------------------
# Retrocompatibilità
