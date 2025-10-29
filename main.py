#!/usr/bin/env python3
"""
🏆 FANTACALCIO MAIN SCRIPT
Script principale per l'analisi completa dei giocatori di fantacalcio.

Questo script esegue automaticamente:
1. Scaricamento dati FSTATS (se necessario)
2. Creazione file FSTATS_analysis.xlsx
3. Calcolo prezzi basati su statistiche FSTATS
4. Output finale con tutte le metriche e prezzi consigliati
"""

import sys
import os
from pathlib import Path
import pandas as pd
import argparse
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Aggiungi la root al path per gli import
sys.path.insert(0, str(Path(__file__).parent))

from src.fantacalcio.data.retriever import fetch_FSTATS_data
from src.fantacalcio.data.processor import process_FSTATS_data
from src.fantacalcio.analyzers.sos_calibrated_pricing import SOSCalibratedPricingCalculator


class FantacalcioMain:
    """Gestore principale per l'analisi fantacalcio basata su FSTATS."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.output_dir = os.path.join(data_dir, "output")
        
        # Crea le directory se non esistono
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # File paths - Solo FSTATS
        self.fstats_csv = os.path.join(self.raw_dir, "_players.csv")
        self.fstats_xlsx = os.path.join(self.data_dir, "FSTATS_analysis.xlsx")
        self.sos_file = os.path.join(self.data_dir, "SOS Fanta 2025_26.xlsx")
        self.output_file = os.path.join(self.output_dir, "final_analysis.xlsx")
    
    def check_data_freshness(self) -> bool:
        """
        Verifica se i dati FSTATS sono aggiornati (meno di 1 giorno).
        
        Returns:
            True se i dati sono freschi, False se devono essere aggiornati
        """
        if not os.path.exists(self.fstats_csv):
            logger.info(f"File FSTATS non trovato - scaricamento necessario")
            return False
        
        # Controlla età del file
        file_time = datetime.fromtimestamp(os.path.getmtime(self.fstats_csv))
        age = datetime.now() - file_time
        
        if age > timedelta(days=1):
            logger.info(f"File FSTATS ha più di 1 giorno - scaricamento necessario")
            return False
        
        logger.info("I dati FSTATS sono aggiornati (meno di 1 giorno)")
        return True
    
    def update_data(self):
        """Scarica i dati aggiornati da FSTATS."""
        logger.info("=" * 60)
        logger.info("STEP 1: Scaricamento dati FSTATS")
        logger.info("=" * 60)
        
        try:
            logger.info("Scaricamento dati FSTATS...")
            fetch_FSTATS_data()
            logger.info("✅ Dati FSTATS scaricati con successo")
        except Exception as e:
            logger.error(f"❌ Errore nello scaricamento FSTATS: {e}")
            raise
    
    def create_analysis_files(self):
        """Crea il file di analisi FSTATS."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 2: Creazione file analisi FSTATS")
        logger.info("=" * 60)
        
        # FSTATS
        logger.info("Processamento dati FSTATS...")
        if not os.path.exists(self.fstats_csv):
            raise FileNotFoundError(f"File FSTATS non trovato: {self.fstats_csv}")
        
        df_fstats = pd.read_csv(self.fstats_csv, sep=";")
        df_fstats = process_FSTATS_data(df_fstats)
        df_fstats = self._calculate_fstats_scores(df_fstats)
        df_fstats.to_excel(self.fstats_xlsx, index=False)
        logger.info(f"✅ File FSTATS salvato: {self.fstats_xlsx}")
    
    def _calculate_fstats_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcola i punteggi per i dati FSTATS."""
        df_result = df.copy()
        
        def safe_numeric(col_name, default=0):
            if col_name in df_result.columns:
                return pd.to_numeric(df_result[col_name], errors='coerce').fillna(default)
            return default
        
        # Score basato su statistiche FSTATS
        df_result['Convenienza'] = (
            safe_numeric('Media voto') * 0.4 +
            safe_numeric('Gol fatti') * 0.3 +
            safe_numeric('Presenze') * 0.2 +
            safe_numeric('Assist') * 0.1
        )
        
        df_result['Prezzo_Massimo_Consigliato'] = (df_result['Convenienza'] / 5).clip(1, 50)
        
        return df_result
    
    def calculate_prices(self):
        """Calcola prezzi basati su FSTATS."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 3: Calcolo prezzi basati su statistiche FSTATS")
        logger.info("=" * 60)
        
        # Carica il file FSTATS
        logger.info("Caricamento file FSTATS...")
        df_fstats = pd.read_excel(self.fstats_xlsx)
        
        # Calcolo prezzi calibrati
        if not os.path.exists(self.sos_file):
            logger.warning(f"File SOS non trovato: {self.sos_file}")
            logger.warning("Calcolo prezzi senza calibrazione SOS")
            # Usa solo le statistiche FSTATS
            df_fstats.to_excel(self.output_file, index=False)
            logger.info(f"✅ File salvato (senza calibrazione SOS): {self.output_file}")
            return
        
        logger.info("Calcolo prezzi calibrati su SOS Fanta...")
        calculator = SOSCalibratedPricingCalculator()
        
        # Calcola prezzi usando solo FSTATS
        df_final = calculator.process_data(self.fstats_xlsx, self.sos_file, self.output_file)
        
        logger.info(f"✅ File finale salvato: {self.output_file}")
        
        # Statistiche
        self._print_final_stats(df_final)
    
    def _print_final_stats(self, df: pd.DataFrame):
        """Stampa statistiche finali."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("STATISTICHE FINALI")
        logger.info("=" * 60)
        
        total = len(df)
        matched = df['Prezzo'].notna().sum() if 'Prezzo' in df.columns else 0
        
        logger.info(f"Giocatori totali: {total}")
        logger.info(f"Giocatori matchati con SOS: {matched}")
        
        if 'Prezzo_Calibrato' in df.columns:
            avg_price = df['Prezzo_Calibrato'].mean()
            logger.info(f"Prezzo calibrato medio: {avg_price:.1f}€")
        
        if 'Ruolo' in df.columns:
            logger.info("\nDistribuzione per ruolo:")
            for role, count in df['Ruolo'].value_counts().head(10).items():
                pct = (count / total) * 100
                logger.info(f"  {role}: {count} ({pct:.1f}%)")
        
        if 'Prezzo_Calibrato' in df.columns:
            logger.info("\nTop 5 giocatori per prezzo:")
            top5 = df.nlargest(5, 'Prezzo_Calibrato')
            for _, p in top5.iterrows():
                logger.info(f"  {p['Nome']} ({p.get('Ruolo', 'N/A')}) - {p['Prezzo_Calibrato']:.1f}€")
    
    def run(self, force_update: bool = False):
        """
        Esegue il workflow completo basato solo su FSTATS.
        
        Args:
            force_update: Se True, forza il download dei dati anche se freschi
        """
        logger.info("🏆 FANTACALCIO ANALYSIS - AVVIO (Solo FSTATS)")
        logger.info("=" * 60)
        
        # Step 1: Verifica e aggiornamento dati FSTATS
        if force_update or not self.check_data_freshness():
            self.update_data()
        else:
            logger.info("⏭️  STEP 1: Saltato (dati già aggiornati)")
        
        # Step 2: Creazione file analisi FSTATS
        self.create_analysis_files()
        
        # Step 3: Calcolo prezzi
        self.calculate_prices()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ ANALISI COMPLETATA CON SUCCESSO!")
        logger.info("=" * 60)
        logger.info(f"File di output: {self.output_file}")
        logger.info("")


def main():
    """Entry point principale - Analisi basata solo su FSTATS."""
    parser = argparse.ArgumentParser(
        description='Fantacalcio Analysis - Analisi basata su FSTATS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
    python main.py                    # Esegue l'analisi FSTATS completa (aggiorna solo se necessario)
    python main.py --force-update     # Forza l'aggiornamento dei dati FSTATS
    python main.py --data-dir /path   # Usa una directory dati personalizzata
        """
    )
    
    parser.add_argument(
        '--force-update',
        action='store_true',
        help='Forza il download dei dati anche se sono freschi'
    )
    
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Directory contenente i dati (default: data)'
    )
    
    args = parser.parse_args()
    
    try:
        app = FantacalcioMain(args.data_dir)
        app.run(force_update=args.force_update)
        return 0
    except Exception as e:
        logger.error(f"❌ Errore durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
