#!/usr/bin/env python3
"""
Fantacalcio — Entry point principale.

Workflow:
1. Scarica dati da FSTATS (API) e FPEDIA (scraping) se necessario
2. Processa e normalizza i dati
3. Integra le due fonti con name matching robusto
4. Calcola il prezzo consigliato per ogni giocatore
5. Salva il risultato in Excel
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from src.fantacalcio.analyzers.pricing_engine import calculate_prices
from src.fantacalcio.data.integrator import integrate
from src.fantacalcio.data.processor import load_fpedia, load_fstats, process_fpedia, process_fstats
from src.fantacalcio.data.retriever import fetch_fpedia_data, fetch_fstats_data
from src.fantacalcio.utils import config
from src.fantacalcio.utils.reporting import print_summary, save_excel, save_summary_excel


def run(force_update: bool = False, skip_fpedia: bool = False) -> pd.DataFrame:
    """
    Esegue il workflow completo.

    Args:
        force_update: forza il riscrittura dei dati anche se recenti.
        skip_fpedia: salta lo scraping FPEDIA (usa solo FSTATS).

    Returns:
        DataFrame con prezzi calcolati.
    """
    os.makedirs(config.RAW_DIR, exist_ok=True)
    os.makedirs(config.INTERIM_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # --- Step 1: Download ---
    logger.info("=" * 60)
    logger.info("STEP 1: Scaricamento dati")
    logger.info("=" * 60)

    df_fstats_raw = fetch_fstats_data(force=force_update)
    if df_fstats_raw is None:
        df_fstats_raw = load_fstats()
        if df_fstats_raw.empty:
            logger.error("Nessun dato FSTATS disponibile. Impossibile procedere.")
            return pd.DataFrame()

    df_fpedia_raw = pd.DataFrame()
    if not skip_fpedia:
        result = fetch_fpedia_data(force=force_update)
        if result is not None:
            df_fpedia_raw = result
        else:
            df_fpedia_raw = load_fpedia()
            if df_fpedia_raw.empty:
                logger.warning("Nessun dato FPEDIA. Si procede solo con FSTATS.")
    else:
        logger.info("FPEDIA: saltato (--skip-fpedia)")

    # --- Step 2: Processing ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 2: Processing dati")
    logger.info("=" * 60)

    df_fstats = process_fstats(df_fstats_raw)
    df_fpedia = process_fpedia(df_fpedia_raw) if not df_fpedia_raw.empty else pd.DataFrame()

    # --- Step 3: Integrazione ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 3: Integrazione dati")
    logger.info("=" * 60)

    df_integrated = integrate(df_fstats, df_fpedia)

    # --- Step 4: Pricing ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 4: Calcolo prezzi")
    logger.info("=" * 60)

    df_final = calculate_prices(df_integrated)

    # --- Step 5: Output ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 5: Output")
    logger.info("=" * 60)

    save_excel(df_final, config.OUTPUT_EXCEL)
    summary_path = os.path.join(config.OUTPUT_DIR, "riepilogo.xlsx")
    save_summary_excel(df_final, summary_path)
    print_summary(df_final)

    return df_final


def main():
    parser = argparse.ArgumentParser(description="Fantacalcio — Analisi e pricing")
    parser.add_argument(
        "--force-update", action="store_true",
        help="Forza il download dei dati anche se recenti",
    )
    parser.add_argument(
        "--skip-fpedia", action="store_true",
        help="Salta lo scraping FPEDIA (usa solo FSTATS)",
    )
    args = parser.parse_args()
    run(force_update=args.force_update, skip_fpedia=args.skip_fpedia)


if __name__ == "__main__":
    main()
