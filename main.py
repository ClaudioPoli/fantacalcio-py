#!/usr/bin/env python3
"""
🏆 FANTACALCIO MAIN SCRIPT
Script principale per l'analisi completa dei giocatori di fantacalcio.

Questo script esegue automaticamente:
1. Scraping dati da FPEDIA e FSTATS (se necessario)
2. Creazione file fpedia_analysis.xlsx e FSTATS_analysis.xlsx
3. Calcolo prezzi calibrati su SOS Fanta
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

from src.fantacalcio.data.retriever import scrape_fpedia, fetch_FSTATS_data
from src.fantacalcio.data.processor import process_fpedia_data, process_FSTATS_data
from src.fantacalcio.analyzers.sos_calibrated_pricing import SOSCalibratedPricingCalculator


class FantacalcioMain:
    """Gestore principale per l'analisi fantacalcio completa."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.output_dir = os.path.join(data_dir, "output")
        
        # Crea le directory se non esistono
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # File paths
        self.fpedia_csv = os.path.join(self.raw_dir, "_giocatori.csv")
        self.fstats_csv = os.path.join(self.raw_dir, "_players.csv")
        self.fpedia_xlsx = os.path.join(self.data_dir, "fpedia_analysis.xlsx")
        self.fstats_xlsx = os.path.join(self.data_dir, "FSTATS_analysis.xlsx")
        self.sos_file = os.path.join(self.data_dir, "SOS Fanta 2025_26.xlsx")
        self.output_file = os.path.join(self.output_dir, "final_analysis.xlsx")
    
    def check_data_freshness(self) -> bool:
        """
        Verifica se i dati sono aggiornati (meno di 1 giorno).
        
        Returns:
            True se i dati sono freschi, False se devono essere aggiornati
        """
        files_to_check = [self.fpedia_csv, self.fstats_csv]
        
        for file in files_to_check:
            if not os.path.exists(file):
                logger.info(f"File {file} non trovato - scaricamento necessario")
                return False
            
            # Controlla età del file
            file_time = datetime.fromtimestamp(os.path.getmtime(file))
            age = datetime.now() - file_time
            
            if age > timedelta(days=1):
                logger.info(f"File {file} ha più di 1 giorno - scaricamento necessario")
                return False
        
        logger.info("I dati sono aggiornati (meno di 1 giorno)")
        return True
    
    def update_data(self):
        """Scarica i dati aggiornati da FPEDIA e FSTATS."""
        logger.info("=" * 60)
        logger.info("STEP 1: Scaricamento dati da FPEDIA e FSTATS")
        logger.info("=" * 60)
        
        try:
            logger.info("Scaricamento dati FPEDIA...")
            scrape_fpedia()
            logger.info("✅ Dati FPEDIA scaricati con successo")
        except Exception as e:
            logger.error(f"❌ Errore nello scaricamento FPEDIA: {e}")
            raise
        
        try:
            logger.info("Scaricamento dati FSTATS...")
            fetch_FSTATS_data()
            logger.info("✅ Dati FSTATS scaricati con successo")
        except Exception as e:
            logger.error(f"❌ Errore nello scaricamento FSTATS: {e}")
            raise
    
    def create_analysis_files(self):
        """Crea i file di analisi FPEDIA e FSTATS."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 2: Creazione file analisi FPEDIA e FSTATS")
        logger.info("=" * 60)
        
        # FPEDIA
        logger.info("Processamento dati FPEDIA...")
        if not os.path.exists(self.fpedia_csv):
            raise FileNotFoundError(f"File FPEDIA non trovato: {self.fpedia_csv}")
        
        df_fpedia = pd.read_csv(self.fpedia_csv)
        df_fpedia = process_fpedia_data(df_fpedia)
        df_fpedia = self._calculate_fpedia_scores(df_fpedia)
        df_fpedia.to_excel(self.fpedia_xlsx, index=False)
        logger.info(f"✅ File FPEDIA salvato: {self.fpedia_xlsx}")
        
        # FSTATS
        logger.info("Processamento dati FSTATS...")
        if not os.path.exists(self.fstats_csv):
            raise FileNotFoundError(f"File FSTATS non trovato: {self.fstats_csv}")
        
        df_fstats = pd.read_csv(self.fstats_csv, sep=";")
        df_fstats = process_FSTATS_data(df_fstats)
        df_fstats = self._calculate_fstats_scores(df_fstats)
        df_fstats.to_excel(self.fstats_xlsx, index=False)
        logger.info(f"✅ File FSTATS salvato: {self.fstats_xlsx}")
    
    def _calculate_fpedia_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcola i punteggi per i dati FPEDIA."""
        df_result = df.copy()
        
        def safe_numeric(col_name, default=0):
            if col_name in df_result.columns:
                return pd.to_numeric(df_result[col_name], errors='coerce').fillna(default)
            return default
        
        df_result['Convenienza'] = (
            safe_numeric('Punteggio') * 0.3 +
            safe_numeric('Fantamedia anno 2024-2025') * 0.4 +
            safe_numeric('Presenze 2024-2025') * 0.2 +
            safe_numeric('Gol previsti') * 0.1
        )
        
        df_result['Prezzo_Massimo_Consigliato'] = (df_result['Convenienza'] / 10).clip(1, 50)
        
        return df_result
    
    def _calculate_fstats_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcola i punteggi per i dati FSTATS."""
        df_result = df.copy()
        
        def safe_numeric(col_name, default=0):
            if col_name in df_result.columns:
                return pd.to_numeric(df_result[col_name], errors='coerce').fillna(default)
            return default
        
        df_result['Convenienza'] = (
            safe_numeric('Media voto') * 0.4 +
            safe_numeric('Gol fatti') * 0.3 +
            safe_numeric('Presenze') * 0.2 +
            safe_numeric('Assist') * 0.1
        )
        
        df_result['Prezzo_Massimo_Consigliato'] = (df_result['Convenienza'] / 5).clip(1, 50)
        
        return df_result
    
    def merge_and_calculate_prices(self):
        """Merge dei dati e calcolo prezzi calibrati."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 3: Merge dati e calcolo prezzi calibrati")
        logger.info("=" * 60)
        
        # Carica i file di analisi
        logger.info("Caricamento file FPEDIA e FSTATS...")
        df_fpedia = pd.read_excel(self.fpedia_xlsx)
        df_fstats = pd.read_excel(self.fstats_xlsx)
        
        # Merge dei dati
        logger.info("Merge dei dati...")
        df_merged = self._merge_dataframes(df_fpedia, df_fstats)
        
        # Calcolo prezzi calibrati
        if not os.path.exists(self.sos_file):
            logger.warning(f"File SOS non trovato: {self.sos_file}")
            logger.warning("Impossibile calcolare prezzi calibrati senza SOS Fanta")
            # Salva solo i dati merged
            df_merged.to_excel(self.output_file, index=False)
            logger.info(f"✅ File salvato (senza calibrazione SOS): {self.output_file}")
            return
        
        logger.info("Calcolo prezzi calibrati su SOS Fanta...")
        calculator = SOSCalibratedPricingCalculator()
        
        # Salva temporaneamente il merged
        temp_merged = os.path.join(self.output_dir, "_temp_merged.xlsx")
        df_merged.to_excel(temp_merged, index=False)
        
        # Calcola prezzi
        df_final = calculator.process_data(temp_merged, self.sos_file, self.output_file)
        
        # Rimuovi file temporaneo
        if os.path.exists(temp_merged):
            os.remove(temp_merged)
        
        logger.info(f"✅ File finale salvato: {self.output_file}")
        
        # Statistiche
        self._print_final_stats(df_final)
    
    def _merge_dataframes(self, df_fpedia: pd.DataFrame, df_fstats: pd.DataFrame) -> pd.DataFrame:
        """Merge intelligente dei due dataframes."""
        import re
        import unicodedata
        
        def normalize_name(name):
            if pd.isna(name):
                return ""
            
            name = str(name).strip()
            name = unicodedata.normalize('NFD', name)
            name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
            name = re.sub(r'[^\w\s]', ' ', name)
            name = re.sub(r'\s+', ' ', name).strip()
            name = name.lower()
            
            parts = name.split()
            if len(parts) >= 2:
                if len(parts[0]) > len(parts[-1]):
                    name = parts[-1] + " " + " ".join(parts[:-1])
            
            return name
        
        df_fpedia_clean = df_fpedia.copy()
        df_fstats_clean = df_fstats.copy()
        
        df_fpedia_clean['Nome_Clean'] = df_fpedia_clean['Nome'].apply(normalize_name)
        df_fstats_clean['Nome_Clean'] = df_fstats_clean['Nome'].apply(normalize_name)
        
        # Merge
        df_merged = pd.merge(
            df_fpedia_clean, 
            df_fstats_clean,
            on='Nome_Clean',
            how='outer',
            suffixes=('_FPEDIA', '_FSTATS')
        )
        
        # Risolvi conflitti
        df_merged['Nome'] = df_merged['Nome_FPEDIA'].fillna(df_merged['Nome_FSTATS'])
        df_merged['Ruolo'] = df_merged['Ruolo_FPEDIA'].fillna(df_merged['Ruolo_FSTATS'])
        
        if 'Squadra_FPEDIA' in df_merged.columns:
            df_merged['Squadra'] = df_merged['Squadra_FPEDIA'].fillna(df_merged.get('Squadra_FSTATS', ''))
        
        df_merged = df_merged.drop('Nome_Clean', axis=1, errors='ignore')
        
        logger.info(f"Merge completato: {len(df_merged)} giocatori totali")
        
        return df_merged
    
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
        Esegue il workflow completo.
        
        Args:
            force_update: Se True, forza il download dei dati anche se freschi
        """
        logger.info("🏆 FANTACALCIO ANALYSIS - AVVIO")
        logger.info("=" * 60)
        
        # Step 1: Verifica e aggiornamento dati
        if force_update or not self.check_data_freshness():
            self.update_data()
        else:
            logger.info("⏭️  STEP 1: Saltato (dati già aggiornati)")
        
        # Step 2: Creazione file analisi
        self.create_analysis_files()
        
        # Step 3: Merge e calcolo prezzi
        self.merge_and_calculate_prices()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ ANALISI COMPLETATA CON SUCCESSO!")
        logger.info("=" * 60)
        logger.info(f"File di output: {self.output_file}")
        logger.info("")


def main():
    """Entry point principale."""
    parser = argparse.ArgumentParser(
        description='Fantacalcio Analysis - Script principale',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
    python main.py                    # Esegue l'analisi completa (aggiorna solo se necessario)
    python main.py --force-update     # Forza l'aggiornamento dei dati
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
