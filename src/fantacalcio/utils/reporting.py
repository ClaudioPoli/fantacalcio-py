"""
Generazione report per l'analisi fantacalcio.

Produce un riepilogo testuale e un Excel formattato
a partire dal DataFrame finale (output di pricing_engine).
"""

import pandas as pd
from loguru import logger


# ---------------------------------------------------------------------------
# Report testuale
# ---------------------------------------------------------------------------

def print_summary(df: pd.DataFrame) -> None:
    """Stampa un riepilogo sintetico dei risultati."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("RIEPILOGO")
    logger.info("=" * 60)

    logger.info(f"Giocatori totali: {len(df)}")
    if "_source" in df.columns:
        for src, count in df["_source"].value_counts().items():
            logger.info(f"  {src}: {count}")

    if "prezzo_consigliato" not in df.columns:
        return

    logger.info("")
    for role in ["P", "D", "C", "A"]:
        role_df = df[df["Ruolo"] == role]
        if role_df.empty:
            continue
        top3 = role_df.nlargest(3, "prezzo_consigliato")
        logger.info(f"Top 3 {role}:")
        for _, p in top3.iterrows():
            logger.info(
                f"  {p['Nome']} ({p.get('Squadra', '?')}) — "
                f"€{p['prezzo_consigliato']:.0f} [{p['categoria']}] "
                f"score={p['score_composite']:.1f}"
            )
        logger.info("")


# ---------------------------------------------------------------------------
# Salvataggio Excel
# ---------------------------------------------------------------------------

_EXPORT_COLUMNS = [
    "Nome", "Ruolo", "Squadra", "_source",
    "prezzo_consigliato", "categoria",
    "score_composite", "score_offensive", "score_defensive",
    "score_reliability", "score_technical", "score_historical",
]


def save_excel(df: pd.DataFrame, path: str) -> None:
    """
    Salva il DataFrame finale in Excel ordinato per ruolo e prezzo.

    Args:
        df: DataFrame con prezzi calcolati.
        path: percorso file di output.
    """
    role_order = {"P": 0, "D": 1, "C": 2, "A": 3}
    out = df.copy()
    out["_role_order"] = out["Ruolo"].map(role_order).fillna(4)
    out = out.sort_values(["_role_order", "prezzo_consigliato"], ascending=[True, False])
    out = out.drop(columns=["_role_order"])

    out.to_excel(path, index=False)
    logger.info(f"File Excel salvato: {path}")


def save_summary_excel(df: pd.DataFrame, path: str) -> None:
    """
    Salva un Excel sintetico con solo le colonne principali.

    Args:
        df: DataFrame con prezzi calcolati.
        path: percorso file di output.
    """
    cols = [c for c in _EXPORT_COLUMNS if c in df.columns]
    out = df[cols].copy()

    role_order = {"P": 0, "D": 1, "C": 2, "A": 3}
    out["_role_order"] = out["Ruolo"].map(role_order).fillna(4)
    out = out.sort_values(["_role_order", "prezzo_consigliato"], ascending=[True, False])
    out = out.drop(columns=["_role_order"])

    out.to_excel(path, index=False)
    logger.info(f"Riepilogo Excel salvato: {path}")
