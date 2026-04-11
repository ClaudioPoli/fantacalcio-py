"""
Pricing engine: calcolo prezzo congruo per ogni giocatore.

Approccio a 4 componenti pesate per ruolo:
1. Offensiva — gol, assist, xG, xA (peso alto per ATT)
2. Difensiva — clean sheet, gol subiti (peso alto per POR/DIF)
3. Affidabilità — presenze, minuti, infortuni, trend
4. Tecnica — 19 indici tecnici FSTATS pesati per ruolo

Il punteggio composito viene poi mappato a un prezzo in crediti
calibrato sul budget per ruolo.
"""

import numpy as np
import pandas as pd
from loguru import logger

from ..utils import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(series_or_val, default=0.0) -> float:
    """Estrae un float sicuro, gestendo NaN/None/-1."""
    if isinstance(series_or_val, pd.Series):
        series_or_val = series_or_val.iloc[0] if len(series_or_val) else default
    if pd.isna(series_or_val):
        return default
    try:
        v = float(series_or_val)
        return default if v == -1 else v
    except (ValueError, TypeError):
        return default


def _col(row: pd.Series, name: str, default=0.0) -> float:
    """Ottiene un valore numerico da una riga, cercando con e senza prefisso."""
    # Prova prima con prefisso fstats_, poi fpedia_, poi senza
    for prefix in ("fstats_", "fpedia_", ""):
        col = f"{prefix}{name}"
        if col in row.index:
            return _safe(row[col], default)
    return default


# ---------------------------------------------------------------------------
# Componenti di score
# ---------------------------------------------------------------------------

def _offensive_score(row: pd.Series, role: str) -> float:
    """Score offensivo: gol, assist, xG, xA."""
    goals = _col(row, "goals")
    assists = _col(row, "assists")
    xg = _col(row, "xgFromOpenPlays")
    xa = _col(row, "xA")
    goals_90 = _col(row, "goals90min")

    if role == "A":
        return goals * 4.0 + assists * 2.5 + xg * 2.0 + xa * 1.5 + goals_90 * 10.0
    elif role == "C":
        return goals * 3.5 + assists * 4.0 + xg * 1.5 + xa * 2.5 + goals_90 * 8.0
    elif role == "D":
        return goals * 5.0 + assists * 3.0 + xg * 1.0 + xa * 1.5
    else:  # P
        return goals * 8.0 + assists * 4.0


def _defensive_score(row: pd.Series, role: str) -> float:
    """Score difensivo: clean sheet, gol subiti, rigori parati."""
    clean_sheets = _col(row, "gkCleanSheets")
    conceded = _col(row, "gkConcededGoals")
    pen_saved = _col(row, "gkPenaltiesSaved")

    if role == "P":
        cs_score = clean_sheets * 3.0
        conceded_score = max(0.0, (20.0 - conceded) * 1.5) if conceded > 0 else 30.0
        return cs_score + conceded_score + pen_saved * 5.0
    elif role == "D":
        return clean_sheets * 2.0
    else:
        return clean_sheets * 0.5


def _reliability_score(row: pd.Series) -> float:
    """Score affidabilità: presenze, minuti, infortuni, trend."""
    presenze = _col(row, "Presenze")
    if presenze == 0:
        # Fallback su colonna FPEDIA
        presenze = _col(row, "Presenze campionato corrente")

    presence_ratio = min(presenze / 38.0, 1.0)
    score = presence_ratio * 15.0

    # Minuti giocati (normalizzati su ~3400 max)
    mins = _col(row, "mins_played")
    if mins > 0:
        score += min(mins / 3400.0, 1.0) * 5.0

    # Bonus titolare
    matches_start = _col(row, "matchesInStart")
    if matches_start > 0 and presenze > 0:
        start_ratio = matches_start / presenze
        score += start_ratio * 3.0

    # Malus infortunio (FPEDIA)
    infortunato = _col(row, "Infortunato")
    if infortunato:
        score -= 3.0

    # Bonus resistenza infortuni (FPEDIA, scala 0-100)
    resistenza = _col(row, "Resistenza infortuni")
    if resistenza > 0:
        score += (resistenza / 100.0) * 2.0

    # Trend (FPEDIA)
    for prefix in ("fpedia_", ""):
        col = f"{prefix}Trend"
        if col in row.index:
            trend = row[col]
            if trend == "UP":
                score += 1.5
            elif trend == "DOWN":
                score -= 1.0
            break

    return max(0.0, score)


def _technical_score(row: pd.Series, role: str) -> float:
    """Score tecnico basato sui 19 indici FSTATS pesati per ruolo."""
    weights = config.TECHNICAL_WEIGHTS_BY_ROLE.get(role, {})
    if not weights:
        return 0.0

    total = 0.0
    total_weight = 0.0

    for idx_name, weight in weights.items():
        # Gli indici FSTATS sono su scala 0-100
        value = _col(row, idx_name)
        if value > 0:
            total += (value / 100.0) * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalizza a scala 0-20
    return (total / total_weight) * 20.0


def _historical_bonus(row: pd.Series) -> float:
    """
    Bonus basato sulle fantamedie storiche (FPEDIA).
    Una fantamedia in crescita negli anni indica un giocatore in miglioramento.
    """
    # Cerca fantamedie storiche
    fm_values = []
    for col in row.index:
        if "Fantamedia anno" in str(col):
            v = _safe(row[col])
            if v > 0:
                fm_values.append(v)

    if not fm_values:
        return 0.0

    # Media fantamedie storiche (bonus se > 6, la sufficienza)
    avg_fm = sum(fm_values) / len(fm_values)
    bonus = (avg_fm - 5.0) * 3.0  # 3 punti per ogni punto sopra il 5

    # Bonus trend crescente (ultima > penultima)
    if len(fm_values) >= 2 and fm_values[-1] > fm_values[-2]:
        bonus += 1.5

    # Punteggio FPEDIA /100 (bonus proporzionale)
    punteggio = _col(row, "Punteggio")
    if punteggio > 0:
        bonus += (punteggio / 100.0) * 3.0

    # Buon investimento (FPEDIA, scala 0-100)
    buon_inv = _col(row, "Buon investimento")
    if buon_inv > 0:
        bonus += (buon_inv / 100.0) * 2.0

    return max(0.0, bonus)


# ---------------------------------------------------------------------------
# Score composito e prezzo
# ---------------------------------------------------------------------------

def _composite_score(row: pd.Series) -> dict:
    """Calcola tutti i sotto-score e il composito per una riga."""
    role = str(row.get("Ruolo", "")).strip()
    if role not in config.PRICING_WEIGHTS:
        role = "C"  # fallback

    weights = config.PRICING_WEIGHTS[role]

    off = _offensive_score(row, role)
    dfs = _defensive_score(row, role)
    rel = _reliability_score(row)
    tech = _technical_score(row, role)
    hist = _historical_bonus(row)

    # Composito pesato
    composite = (
        off * weights["offensive"]
        + dfs * weights["defensive"]
        + rel * weights["reliability"]
        + tech * weights["technical"]
        + hist * 0.15  # bonus storico trasversale
    )

    return {
        "score_offensive": round(off, 2),
        "score_defensive": round(dfs, 2),
        "score_reliability": round(rel, 2),
        "score_technical": round(tech, 2),
        "score_historical": round(hist, 2),
        "score_composite": round(composite, 2),
    }


def _score_to_price(score: float, role: str, percentile: float, max_score: float) -> float:
    """
    Mappa uno score composito a un prezzo usando normalizzazione per ruolo.

    Args:
        score: score composito
        role: ruolo (P/D/C/A)
        percentile: posizione percentile nel ruolo (0.0 = peggiore, 1.0 = migliore)
        max_score: score massimo nel ruolo (per normalizzazione)
    """
    budget = config.BUDGET.get(role, 100)

    if score <= 0 or max_score <= 0:
        return 1.0

    # Normalizza sullo score massimo effettivo del ruolo
    normalized = min(score / max_score, 1.0)

    # Curva: combina normalizzazione score e percentile
    # Score normalizzato dà il valore assoluto, percentile differenzia i pari merito
    combined = 0.7 * normalized + 0.3 * percentile

    # Esponente 2.5: concentra budget sui top player
    price = budget * (combined ** 2.5)

    # Floor e ceiling
    return max(1.0, min(round(price, 0), budget))


def _categorize(score: float) -> str:
    """Categorizza il giocatore in base allo score composito."""
    if score >= 25:
        return "Top Player"
    elif score >= 18:
        return "Eccellente"
    elif score >= 12:
        return "Buono"
    elif score >= 7:
        return "Nella Media"
    elif score >= 3:
        return "Sottotono"
    else:
        return "Scarso"


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def calculate_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola il prezzo consigliato per ogni giocatore nel DataFrame integrato.

    Args:
        df: DataFrame output di integrator.integrate()

    Returns:
        DataFrame con colonne aggiuntive:
        - score_offensive, score_defensive, score_reliability, score_technical, score_historical
        - score_composite
        - prezzo_consigliato
        - categoria
    """
    if df.empty:
        return df

    logger.info(f"Calcolo prezzi per {len(df)} giocatori...")

    # Step 1: calcola score compositi
    scores_list = []
    for idx, row in df.iterrows():
        scores = _composite_score(row)
        scores["_role"] = str(row.get("Ruolo", "C")).strip()
        if scores["_role"] not in config.PRICING_WEIGHTS:
            scores["_role"] = "C"
        scores["categoria"] = _categorize(scores["score_composite"])
        scores_list.append(scores)

    scores_df = pd.DataFrame(scores_list, index=df.index)

    # Step 2: calcola percentili per ruolo e mappa a prezzo
    prices = []
    for role in ["P", "D", "C", "A"]:
        role_mask = scores_df["_role"] == role
        role_scores = scores_df.loc[role_mask, "score_composite"]
        if role_scores.empty:
            continue
        # Percentile rank (0=peggiore, 1=migliore)
        ranked = role_scores.rank(pct=True)
        max_score = role_scores.max()
        for idx in role_scores.index:
            prices.append({
                "_idx": idx,
                "prezzo_consigliato": _score_to_price(
                    role_scores[idx], role, ranked[idx], max_score
                ),
            })

    prices_df = pd.DataFrame(prices).set_index("_idx")
    scores_df = scores_df.join(prices_df)
    scores_df.drop(columns=["_role"], inplace=True)

    result = pd.concat([df, scores_df], axis=1)

    # Statistiche
    for role in ["P", "D", "C", "A"]:
        role_df = result[result["Ruolo"] == role]
        if not role_df.empty:
            avg_score = role_df["score_composite"].mean()
            avg_price = role_df["prezzo_consigliato"].mean()
            max_price = role_df["prezzo_consigliato"].max()
            logger.info(
                f"  {role}: {len(role_df)} giocatori, "
                f"score medio={avg_score:.1f}, "
                f"prezzo medio={avg_price:.0f}, max={max_price:.0f}"
            )

    cat_counts = result["categoria"].value_counts()
    logger.info(f"Distribuzione categorie: {cat_counts.to_dict()}")

    return result
