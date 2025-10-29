"""
Modulo per il calcolo autonomo dei prezzi consigliati basato esclusivamente
sulle statistiche avanzate e sui 19 indici tecnici, senza dipendenze da SOS Fanta.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StandalonePricingCalculator:
    """
    Calcola i prezzi consigliati basandosi esclusivamente su:
    1. Performance Score dai 19 indici tecnici
    2. Moltiplicatori specifici per ruolo
    3. Fattori di mercato calibrati
    4. Categorizzazione basata su performance assolute
    """
    
    def __init__(self):
        # Pesi per il calcolo performance score per ruolo
        self.technical_weights = {
            'POR': {
                'FSTATS_Defense_solidity_Index': 4.0,
                'FSTATS_gkCleanSheets': 3.5,
                'FSTATS_gkConcededGoals': -2.0,  # Negativo = meno gol subiti è meglio
                'FSTATS_presences': 2.5,
                'FSTATS_fantacalcioFantaindex': 3.0
            },
            'DIF': {
                'FSTATS_Defense_solidity_Index': 4.0,
                'FSTATS_gkCleanSheets': 3.0,
                'FSTATS_goals': 2.5,
                'FSTATS_assists': 2.0,
                'FSTATS_presences': 2.0,
                'FSTATS_fantacalcioFantaindex': 2.5,
                'FSTATS_Air_challenge_offensive_Index': 2.0
            },
            'CEN': {
                'FSTATS_Pass_leading_chances_Index': 3.5,
                'FSTATS_Offensive_actions_Index': 3.0,
                'FSTATS_goals': 2.5,
                'FSTATS_assists': 3.5,
                'FSTATS_presences': 2.0,
                'FSTATS_fantacalcioFantaindex': 2.5,
                'FSTATS_Pass_accuracy_Index': 3.0
            },
            'ATT': {
                'FSTATS_Shot_on_target_Index': 4.0,
                'FSTATS_goals': 4.5,
                'FSTATS_Offensive_actions_Index': 3.5,
                'FSTATS_assists': 2.5,
                'FSTATS_presences': 2.0,
                'FSTATS_fantacalcioFantaindex': 2.0,
                'FSTATS_xgFromOpenPlays': 3.0
            }
        }
        
        # Moltiplicatori di prezzo base per ruolo (calibrati su mercato generale)
        self.price_multipliers = {
            'POR': 2.5,  # Portieri: prezzo base più contenuto
            'DIF': 3.0,  # Difensori: range medio
            'CEN': 3.5,  # Centrocampisti: più varietà di prezzo
            'ATT': 4.0   # Attaccanti: prezzi più alti
        }
        
        # Soglie per categorizzazione (basate su performance assolute)
        self.category_thresholds = {
            'top_player': 15.0,         # Performance score > 15
            'excellent': 12.0,          # Performance score 12-15
            'good': 8.0,               # Performance score 8-12
            'average': 5.0,            # Performance score 5-8
            'below_average': 2.0,      # Performance score 2-5
            # < 2.0 = Poor
        }

    def get_technical_index_value(self, player_row: pd.Series, index_name: str) -> float:
        """Ottiene il valore di un indice tecnico, gestendo valori mancanti."""
        if index_name not in player_row or pd.isna(player_row[index_name]):
            return 0.0
        
        value = player_row[index_name]
        if value == -1:  # Valore placeholder per dati mancanti
            return 0.0
        
        # Normalizza i valori FSTATS che sono su scale diverse
        if 'Index' in index_name:
            # Gli indici sono già su scala 0-100, normalizza a 0-10
            return float(value) / 10.0
        elif index_name in ['FSTATS_goals', 'FSTATS_assists']:
            # Goals e assists: scala diretta ma limitiamo a 20 max
            return min(float(value), 20.0)
        elif index_name == 'FSTATS_presences':
            # Presenze: normalizza su base 38 partite (Serie A)
            return (float(value) / 38.0) * 10.0
        elif index_name == 'FSTATS_fantacalcioFantaindex':
            # FantaIndex: già su scala 0-100, normalizza
            return float(value) / 10.0
        elif index_name == 'FSTATS_xgFromOpenPlays':
            # xG: scala 0-20 expected
            return min(float(value), 20.0)
        elif index_name == 'FSTATS_gkCleanSheets':
            # Clean sheets per portieri: normalizza su 38 partite
            return (float(value) / 38.0) * 10.0
        elif index_name == 'FSTATS_gkConcededGoals':
            # Gol subiti: meno è meglio, inverti la scala
            goals_conceded = float(value)
            if goals_conceded <= 0:
                return 10.0
            # Normalizza: più gol subiti = score più basso
            return max(0.0, 10.0 - (goals_conceded / 3.0))
        
        return float(value)

    def calculate_performance_score(self, player_row: pd.Series) -> float:
        """Calcola il performance score basato sui 19 indici tecnici."""
        role = player_row.get('Ruolo', '').upper()
        
        # Mappa i ruoli alle categorie standard
        if role in ['P', 'POR']:
            role_key = 'POR'
        elif role in ['D', 'DIF']:
            role_key = 'DIF'
        elif role in ['C', 'CEN']:
            role_key = 'CEN'
        elif role in ['A', 'ATT']:
            role_key = 'ATT'
        else:
            logger.warning(f"Ruolo sconosciuto per {player_row.get('Nome', 'N/A')}: {role}")
            return 0.0
        
        if role_key not in self.technical_weights:
            return 0.0
        
        weights = self.technical_weights[role_key]
        total_score = 0.0
        total_weight = 0.0
        
        # Calcola score pesato per tutti gli indici disponibili
        for index_name, weight in weights.items():
            value = self.get_technical_index_value(player_row, index_name)
            total_score += value * weight
            total_weight += abs(weight)  # Usa valore assoluto per i pesi negativi
        
        # Normalizza il punteggio
        if total_weight > 0:
            normalized_score = (total_score / total_weight) * 2  # Scala a 0-20
            return max(0.0, min(20.0, normalized_score))  # Clamp tra 0 e 20
        
        return 0.0

    def calculate_standalone_price(self, player_row: pd.Series) -> float:
        """Calcola il prezzo consigliato basato solo su performance e ruolo."""
        performance_score = self.calculate_performance_score(player_row)
        role = player_row.get('Ruolo', '').upper()
        
        # Mappa ruolo
        if role in ['P', 'POR']:
            role_key = 'POR'
        elif role in ['D', 'DIF']:
            role_key = 'DIF'
        elif role in ['C', 'CEN']:
            role_key = 'CEN'
        elif role in ['A', 'ATT']:
            role_key = 'ATT'
        else:
            role_key = 'CEN'  # Default
        
        base_multiplier = self.price_multipliers[role_key]
        
        # Calcolo prezzo base
        base_price = performance_score * base_multiplier
        
        # Fattori di aggiustamento
        # Bonus per performance eccezionali
        if performance_score >= 18.0:
            base_price *= 1.4  # +40% per fenomeni
        elif performance_score >= 15.0:
            base_price *= 1.2  # +20% per top player
        elif performance_score >= 12.0:
            base_price *= 1.1  # +10% per ottimi giocatori
        
        # Penalità per performance scarse
        elif performance_score <= 2.0:
            base_price *= 0.3  # -70% per performance molto basse
        elif performance_score <= 5.0:
            base_price *= 0.6  # -40% per performance basse
        
        # Floor minimo e ceiling massimo realistici
        min_price = 1.0
        max_price = 150.0
        
        return max(min_price, min(max_price, base_price))

    def categorize_player(self, performance_score: float, price: float) -> str:
        """Categorizza il giocatore basandosi solo su performance assolute."""
        if performance_score >= self.category_thresholds['top_player']:
            return 'Top Player'
        elif performance_score >= self.category_thresholds['excellent']:
            return 'Eccellente'
        elif performance_score >= self.category_thresholds['good']:
            return 'Buono'
        elif performance_score >= self.category_thresholds['average']:
            return 'Nella Media'
        elif performance_score >= self.category_thresholds['below_average']:
            return 'Sottotono'
        else:
            return 'Scarso'

    def process_data(self, merged_file: str, output_file: str):
        """Processa i dati e calcola i prezzi autonomi."""
        logger.info("Avvio del calcolo prezzi autonomo (senza SOS)...")
        
        # Carica il dataset unificato
        merged_df = pd.read_excel(merged_file)
        logger.info(f"Caricati {len(merged_df)} giocatori dal file merged")
        
        # Calcola performance scores e prezzi
        logger.info("Calcolo performance scores e prezzi...")
        
        results = []
        for _, player in merged_df.iterrows():
            performance_score = self.calculate_performance_score(player)
            standalone_price = self.calculate_standalone_price(player)
            category = self.categorize_player(performance_score, standalone_price)
            
            result_row = player.copy()
            result_row['Performance_Score'] = performance_score
            result_row['Prezzo_Consigliato'] = standalone_price
            result_row['Categoria'] = category
            
            results.append(result_row)
        
        # Crea DataFrame finale
        result_df = pd.DataFrame(results)
        
        # Statistiche finali
        avg_performance = result_df['Performance_Score'].mean()
        avg_price = result_df['Prezzo_Consigliato'].mean()
        
        logger.info(f"Performance Score medio: {avg_performance:.2f}")
        logger.info(f"Prezzo medio calcolato: {avg_price:.1f}€")
        
        # Distribuzione per categoria
        logger.info("\nDistribuzione per categoria:")
        for category, count in result_df['Categoria'].value_counts().items():
            logger.info(f"  {category}: {count}")
        
        # Salva risultati
        result_df.to_excel(output_file, index=False)
        logger.info(f"Risultati salvati in: {output_file}")
        
        return result_df

    def get_top_players_by_role(self, df: pd.DataFrame, role: str, top_n: int = 10) -> pd.DataFrame:
        """Restituisce i migliori giocatori per ruolo."""
        role_df = df[df['Ruolo'].str.upper().isin([role, role.upper()])]
        return role_df.nlargest(top_n, 'Performance_Score')

    def get_best_value_players(self, df: pd.DataFrame, max_price: float = 10.0) -> pd.DataFrame:
        """Trova i giocatori con il miglior rapporto qualità/prezzo."""
        value_df = df[df['Prezzo_Consigliato'] <= max_price]
        value_df = value_df[value_df['Performance_Score'] >= 8.0]  # Almeno buona performance
        return value_df.sort_values('Performance_Score', ascending=False)


def main():
    """Funzione principale per test."""
    calculator = StandalonePricingCalculator()
    
    # Path dei file
    merged_file = "data/output/perfect_merged_analysis.xlsx"
    output_file = "data/output/standalone_pricing_analysis.xlsx"
    
    try:
        # Processa i dati
        df_result = calculator.process_data(merged_file, output_file)
        
        print("\n🏆 TOP 5 GIOCATORI PER RUOLO:")
        for role in ['ATT', 'CEN', 'DIF', 'POR']:
            top_players = calculator.get_top_players_by_role(df_result, role, 5)
            print(f"\n{role}:")
            for _, player in top_players.iterrows():
                print(f"  • {player['Nome']} - "
                      f"Performance: {player['Performance_Score']:.1f}, "
                      f"Prezzo: {player['Prezzo_Consigliato']:.1f}€")
        
        print("\n💰 MIGLIORI OCCASIONI (Performance >8, Prezzo <10€):")
        best_values = calculator.get_best_value_players(df_result, 10.0)
        for _, player in best_values.head(10).iterrows():
            print(f"  • {player['Nome']} ({player['Ruolo']}) - "
                  f"Performance: {player['Performance_Score']:.1f}, "
                  f"Prezzo: {player['Prezzo_Consigliato']:.1f}€")
        
    except Exception as e:
        logger.error(f"Errore durante il processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
