"""
Modulo per il calcolo dei prezzi consigliati calibrati su SOS Fanta 2025,
utilizzando i dati tecnici completi da perfect_merged_analysis.xlsx.

Questo modulo prende i prezzi SOS come riferimento base e li calibra
basandosi su tutti i parametri statistici disponibili, con particolare
enfasi su:
- Pericolosità in zona goal (gol, assist, xG, tiri in porta)
- Affidabilità (presenze, minuti giocati, infortuni)
- Performance tecnica (19 indici FSTATS)
- Bonus/malus basati su statistiche reali
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging
import re
import unicodedata

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SOSCalibratedPricingCalculator:
    """
    Calcola i prezzi consigliati usando SOS Fanta come baseline,
    calibrando in base a tutte le statistiche tecniche disponibili.
    """
    
    def __init__(self):
        # Pesi per le diverse categorie di statistiche per ruolo
        self.role_category_weights = {
            'POR': {
                'defensive': 0.45,      # Solidità difensiva, porte inviolate
                'reliability': 0.30,     # Presenze, minuti
                'technical': 0.15,       # Indici tecnici specifici
                'offensive': 0.10        # Contributo offensivo minimo
            },
            'DIF': {
                'defensive': 0.30,      # Solidità difensiva
                'reliability': 0.25,     # Presenze, minuti
                'technical': 0.20,       # Indici tecnici
                'offensive': 0.25        # Gol, assist (molto importanti per difensori)
            },
            'CEN': {
                'defensive': 0.10,      # Supporto difensivo
                'reliability': 0.20,     # Presenze, minuti
                'technical': 0.35,       # Creatività, passaggi
                'offensive': 0.35        # Gol, assist, azioni offensive
            },
            'ATT': {
                'defensive': 0.05,      # Quasi irrilevante
                'reliability': 0.15,     # Presenze, minuti
                'technical': 0.30,       # Efficienza sotto porta
                'offensive': 0.50        # Gol, assist, pericolosità (priorità massima)
            }
        }
        
        # Pesi specifici degli indici tecnici per ruolo
        self.technical_index_weights = {
            'POR': {
                'Defense_solidity_Index': 5.0,
                'Pass_accuracy_Index': 2.0,
            },
            'DIF': {
                'Defense_solidity_Index': 4.5,
                'Air_challenge_offensive_Index': 3.0,
                'Set_piece_attack_Index': 2.5,
                'Pass_forward_accuracy_Index': 2.0,
                'Cross_accuracy_Index': 1.5,
            },
            'CEN': {
                'Pass_leading_chances_Index': 4.0,
                'Offensive_actions_Index': 3.5,
                'Pass_accuracy_Index': 3.0,
                'Offensive_verticalization_Index': 2.5,
                'Accompany_the_offensive_action_Index': 2.0,
                'Cross_accuracy_Index': 2.0,
                'Dribbles_successful_Index': 1.5,
            },
            'ATT': {
                'Shot_on_target_Index': 5.0,
                'Shot_on_goal_Index': 4.5,
                'Offensive_actions_Index': 4.0,
                'Attacking_area_Index': 3.5,
                'Deep_runs_Index': 2.5,
                'Dribbles_successful_Index': 2.0,
                'Set_piece_attack_Index': 1.5,
            }
        }
        
        # Moltiplicatori per calibrazione finale
        self.calibration_multipliers = {
            'POR': 1.0,
            'DIF': 1.0,
            'CEN': 1.0,
            'ATT': 1.0
        }
    
    def normalize_name(self, name):
        """Normalizza un nome per il matching."""
        if pd.isna(name):
            return ""
        
        name = str(name).strip()
        
        # Rimuovi accenti
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        
        # Rimuovi caratteri speciali e normalizza spazi
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Converti in uppercase per matching case-insensitive
        name = name.upper()
        
        return name
    
    def extract_surname(self, full_name):
        """
        Estrae il cognome dal nome completo.
        Formato merged: "COGNOME NOME" o "Cognome Nome"
        Formato SOS: "COGNOME" (solo cognome)
        """
        normalized = self.normalize_name(full_name)
        if not normalized:
            return ""
        
        # Prendi la prima parola (che dovrebbe essere il cognome)
        parts = normalized.split()
        if len(parts) > 0:
            return parts[0]
        return normalized
    
    def load_sos_fanta_data(self, file_path: str) -> pd.DataFrame:
        """Carica i dati SOS Fanta da tutti i fogli."""
        logger.info("Caricamento dati SOS Fanta...")
        
        all_players = []
        roles = ['P', 'D', 'C', 'A']
        
        for role in roles:
            try:
                df_role = pd.read_excel(file_path, sheet_name=role)
                # Filtra solo i giocatori con prezzo valido
                df_role = df_role[df_role['Prezzo'].notna() & (df_role['Prezzo'] > 0)]
                df_role['Ruolo_SOS'] = role
                all_players.append(df_role)
                logger.info(f"Caricati {len(df_role)} giocatori per ruolo {role}")
            except Exception as e:
                logger.error(f"Errore nel caricamento del ruolo {role}: {e}")
        
        sos_data = pd.concat(all_players, ignore_index=True)
        logger.info(f"Totale giocatori SOS Fanta: {len(sos_data)}")
        
        return sos_data
    
    def match_with_sos(self, merged_df: pd.DataFrame, sos_df: pd.DataFrame) -> pd.DataFrame:
        """Match tra perfect_merged_analysis e SOS Fanta."""
        logger.info("Matching giocatori con SOS Fanta...")
        
        # Per merged: estrai cognome (prima parola)
        # Per SOS: normalizza il nome (già solo cognome)
        merged_df['Surname'] = merged_df['Nome'].apply(self.extract_surname)
        sos_df['Surname'] = sos_df['Nome'].apply(self.normalize_name)
        
        # Merge sul cognome
        matched = merged_df.merge(
            sos_df[['Surname', 'Prezzo', 'Ruolo_SOS', 'Team', 'Fascia', 
                   'MV', 'FMV', 'Titolarità', 'Affidabilità', 'Integrità',
                   'Presenze', 'Gol', 'Assist']],
            on='Surname',
            how='left',
            suffixes=('', '_SOS_Data')
        )
        
        matches_found = matched['Prezzo'].notna().sum()
        logger.info(f"Trovati {matches_found} match su {len(merged_df)} giocatori totali")
        
        # Log alcuni esempi di match
        if matches_found > 0:
            matched_examples = matched[matched['Prezzo'].notna()].head(5)
            logger.info("Esempi di match trovati:")
            for _, row in matched_examples.iterrows():
                logger.info(f"  {row['Nome']} ({row['Surname']}) -> SOS Prezzo: {row['Prezzo']}€")
        
        return matched
    
    def get_value_safe(self, player_row: pd.Series, column: str, default=0.0) -> float:
        """Ottiene un valore numerico in modo sicuro, gestendo -1 e NaN."""
        if column not in player_row or pd.isna(player_row[column]):
            return default
        
        value = player_row[column]
        
        # -1 indica dato non disponibile in FSTATS
        if value == -1:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def calculate_offensive_score(self, player_row: pd.Series, role: str) -> float:
        """
        Calcola il punteggio offensivo basato su gol, assist, xG, tiri, etc.
        Questo è il parametro più importante per valutare la "pericolosità".
        """
        score = 0.0
        
        # Statistiche di base (peso molto alto)
        goals = self.get_value_safe(player_row, 'goals', 0)
        assists = self.get_value_safe(player_row, 'assists', 0)
        
        # Expected goals (indica pericolosità anche senza gol segnati)
        xg = self.get_value_safe(player_row, 'xgFromOpenPlays', 0)
        xg_90 = self.get_value_safe(player_row, 'xgFromOpenPlays/90min', 0)
        
        # Expected assists
        xa = self.get_value_safe(player_row, 'xA', 0)
        
        # Pesi diversi per ruolo
        if role == 'ATT':
            # Attaccanti: gol sono fondamentali
            score += goals * 5.0
            score += assists * 3.0
            score += xg * 2.5
            score += xg_90 * 15.0  # xG per 90 minuti normalizzato
            score += xa * 2.0
        elif role == 'CEN':
            # Centrocampisti: balance tra gol e assist
            score += goals * 4.0
            score += assists * 4.5
            score += xg * 2.0
            score += xg_90 * 12.0
            score += xa * 3.0
        elif role == 'DIF':
            # Difensori: contributo offensivo è un super-bonus
            score += goals * 6.0  # Gol di un difensore vale moltissimo
            score += assists * 4.0
            score += xg * 1.5
            score += xa * 2.0
        else:  # POR
            # Portieri: quasi nessun contributo offensivo
            score += goals * 10.0  # Rarissimo, vale tantissimo
            score += assists * 5.0
        
        return score
    
    def calculate_defensive_score(self, player_row: pd.Series, role: str) -> float:
        """Calcola il punteggio difensivo."""
        score = 0.0
        
        if role == 'POR':
            # Portieri: porte inviolate e gol subiti
            clean_sheets = self.get_value_safe(player_row, 'gkCleanSheets', 0)
            conceded = self.get_value_safe(player_row, 'gkConcededGoals', 0)
            penalties_saved = self.get_value_safe(player_row, 'gkPenaltiesSaved', 0)
            
            score += clean_sheets * 3.0
            score += max(0, (20 - conceded) * 1.5)  # Meno gol subiti = meglio
            score += penalties_saved * 5.0
            
        elif role == 'DIF':
            # Difensori: porte inviolate
            clean_sheets = self.get_value_safe(player_row, 'gkCleanSheets', 0)
            score += clean_sheets * 2.5
        
        return score
    
    def calculate_reliability_score(self, player_row: pd.Series) -> float:
        """
        Calcola l'affidabilità basata su presenze, minuti, infortuni.
        Giocatori più affidabili valgono di più.
        """
        score = 0.0
        
        # Presenze (normalizzate su 38 partite)
        presences = self.get_value_safe(player_row, 'presences', 0)
        presence_ratio = min(presences / 38.0, 1.0)
        score += presence_ratio * 15.0
        
        # Percentuale di partite da titolare
        perc_started = self.get_value_safe(player_row, 'perc_matchesStarted', 0)
        if perc_started > 0:
            score += (perc_started / 100.0) * 10.0
        
        # Minuti giocati
        perc_mins = self.get_value_safe(player_row, 'percMinsPlayed', 0)
        if perc_mins > 0:
            score += (perc_mins / 100.0) * 8.0
        
        # Penalità per cartellini
        red_cards = self.get_value_safe(player_row, 'redCards', 0)
        yellow_cards = self.get_value_safe(player_row, 'yellowCards', 0)
        
        score -= red_cards * 3.0
        score -= yellow_cards * 0.5
        
        return max(0, score)
    
    def calculate_technical_score(self, player_row: pd.Series, role: str) -> float:
        """Calcola il punteggio basato sugli indici tecnici FSTATS."""
        if role not in self.technical_index_weights:
            return 0.0
        
        score = 0.0
        weights = self.technical_index_weights[role]
        
        for index_name, weight in weights.items():
            value = self.get_value_safe(player_row, index_name, 0)
            
            if value > 0:
                # Gli indici sono su scala 0-100, normalizziamo
                normalized = value / 100.0
                score += normalized * weight
        
        return score
    
    def calculate_comprehensive_score(self, player_row: pd.Series, role: str) -> Dict[str, float]:
        """
        Calcola tutti i punteggi componenti per un giocatore.
        Restituisce un dizionario con i vari score.
        """
        # Mappa il ruolo
        role_map = {
            'P': 'POR', 'POR': 'POR',
            'D': 'DIF', 'DIF': 'DIF',
            'C': 'CEN', 'CEN': 'CEN',
            'A': 'ATT', 'ATT': 'ATT'
        }
        role_key = role_map.get(role, 'CEN')
        
        scores = {
            'offensive': self.calculate_offensive_score(player_row, role_key),
            'defensive': self.calculate_defensive_score(player_row, role_key),
            'reliability': self.calculate_reliability_score(player_row),
            'technical': self.calculate_technical_score(player_row, role_key),
        }
        
        # Calcola score totale pesato per ruolo
        weights = self.role_category_weights[role_key]
        total_score = (
            scores['offensive'] * weights['offensive'] +
            scores['defensive'] * weights['defensive'] +
            scores['reliability'] * weights['reliability'] +
            scores['technical'] * weights['technical']
        )
        
        scores['total'] = total_score
        scores['role'] = role_key
        
        return scores
    
    def calculate_calibrated_price(self, player_row: pd.Series, scores: Dict[str, float]) -> float:
        """
        Calcola il prezzo calibrato basandosi su SOS e i punteggi calcolati.
        """
        sos_price = self.get_value_safe(player_row, 'Prezzo', None)
        role = scores['role']
        total_score = scores['total']
        
        if sos_price is None or sos_price <= 0:
            # Nessun prezzo SOS: stima basata solo sui punteggi
            base_multiplier = {
                'POR': 2.0,
                'DIF': 2.5,
                'CEN': 3.0,
                'ATT': 4.0
            }[role]
            
            estimated_price = total_score * base_multiplier
            return max(1.0, min(estimated_price, 150.0))
        
        # Abbiamo un prezzo SOS: lo calibriamo
        sos_price = float(sos_price)
        
        # Calcola il fattore di adjustment basato sul punteggio
        # Score alto = prezzo più alto, score basso = prezzo più basso
        
        # Normalizza il total_score (valori tipici: 0-50)
        normalized_score = total_score / 40.0  # Valore medio atteso
        
        # Calcola adjustment factor
        if normalized_score >= 1.5:
            # Performance eccezionale: +40-80%
            adjustment = 1.0 + min((normalized_score - 1.0) * 0.8, 0.8)
        elif normalized_score >= 1.2:
            # Performance ottima: +20-40%
            adjustment = 1.0 + (normalized_score - 1.0) * 0.4
        elif normalized_score >= 0.8:
            # Performance nella media: -10% a +10%
            adjustment = 0.9 + (normalized_score - 0.8) * 0.5
        elif normalized_score >= 0.5:
            # Performance sotto media: -20% a -10%
            adjustment = 0.7 + (normalized_score - 0.5) * 0.67
        else:
            # Performance scarsa: -50% a -20%
            adjustment = 0.5 + normalized_score
        
        # Applica adjustment
        calibrated_price = sos_price * adjustment
        
        # Bonus specifici per gol e assist (pericolosità)
        goals = self.get_value_safe(player_row, 'goals', 0)
        assists = self.get_value_safe(player_row, 'assists', 0)
        
        # Bonus progressivo per gol
        if goals >= 15:
            calibrated_price *= 1.3
        elif goals >= 10:
            calibrated_price *= 1.2
        elif goals >= 7:
            calibrated_price *= 1.1
        
        # Bonus per assist
        if assists >= 10:
            calibrated_price *= 1.15
        elif assists >= 6:
            calibrated_price *= 1.08
        
        # Limiti realistici
        calibrated_price = max(1.0, min(calibrated_price, 200.0))
        
        return calibrated_price
    
    def categorize_player(self, scores: Dict[str, float], price: float) -> str:
        """Categorizza il giocatore in base a score e prezzo."""
        total_score = scores['total']
        
        if total_score >= 50.0:
            return 'Fenomeno'
        elif total_score >= 40.0:
            return 'Top Player'
        elif total_score >= 30.0:
            return 'Eccellente'
        elif total_score >= 20.0:
            return 'Buono'
        elif total_score >= 12.0:
            return 'Nella Media'
        elif total_score >= 6.0:
            return 'Sottotono'
        else:
            return 'Scarso'
    
    def process_data(self, merged_file: str, sos_file: str, output_file: str):
        """Processa i dati e calcola i prezzi calibrati su SOS."""
        logger.info("Avvio calcolo prezzi calibrati su SOS Fanta...")
        
        # Carica i dati
        merged_df = pd.read_excel(merged_file)
        sos_df = self.load_sos_fanta_data(sos_file)
        
        logger.info(f"Caricati {len(merged_df)} giocatori dal file merged")
        logger.info(f"Caricati {len(sos_df)} giocatori da SOS Fanta")
        
        # Match con SOS
        matched_df = self.match_with_sos(merged_df, sos_df)
        
        # Calcola scores e prezzi
        logger.info("Calcolo scores e prezzi calibrati...")
        
        results = []
        for _, player in matched_df.iterrows():
            role = player.get('Ruolo', player.get('Ruolo_SOS', 'C'))
            
            # Calcola tutti gli score
            scores = self.calculate_comprehensive_score(player, role)
            
            # Calcola prezzo calibrato
            calibrated_price = self.calculate_calibrated_price(player, scores)
            
            # Categorizza
            category = self.categorize_player(scores, calibrated_price)
            
            # Prepara riga risultato
            result_row = player.copy()
            result_row['Offensive_Score'] = scores['offensive']
            result_row['Defensive_Score'] = scores['defensive']
            result_row['Reliability_Score'] = scores['reliability']
            result_row['Technical_Score'] = scores['technical']
            result_row['Total_Score'] = scores['total']
            result_row['Prezzo_Calibrato'] = calibrated_price
            result_row['Categoria_Performance'] = category
            
            # Differenza con SOS (se disponibile)
            if pd.notna(player.get('Prezzo')):
                result_row['Differenza_vs_SOS'] = calibrated_price - player['Prezzo']
            else:
                result_row['Differenza_vs_SOS'] = None
            
            results.append(result_row)
        
        # Crea DataFrame finale
        result_df = pd.DataFrame(results)
        
        # Riordina colonne per mettere le più importanti all'inizio
        priority_cols = [
            'Nome', 'Ruolo', 'Squadra',
            'Prezzo_Calibrato',
            'Prezzo',  # Prezzo SOS originale
            'Differenza_vs_SOS',
            'Total_Score',
            'Offensive_Score',
            'Defensive_Score',
            'Reliability_Score',
            'Technical_Score',
            'Categoria_Performance',
            'goals', 'assists', 'presences'
        ]
        
        # Aggiungi colonne rimanenti
        remaining_cols = [col for col in result_df.columns if col not in priority_cols]
        final_cols = [col for col in priority_cols if col in result_df.columns] + remaining_cols
        result_df = result_df[final_cols]
        
        # Salva risultati
        result_df.to_excel(output_file, index=False)
        logger.info(f"Risultati salvati in: {output_file}")
        
        # Statistiche finali
        self._print_statistics(result_df)
        
        return result_df
    
    def _print_statistics(self, df: pd.DataFrame):
        """Stampa statistiche sui risultati."""
        matched_count = df['Prezzo'].notna().sum()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"STATISTICHE FINALI")
        logger.info(f"{'='*60}")
        logger.info(f"Giocatori totali: {len(df)}")
        logger.info(f"Giocatori matchati con SOS: {matched_count}")
        logger.info(f"Prezzo calibrato medio: {df['Prezzo_Calibrato'].mean():.1f}€")
        logger.info(f"Score medio: {df['Total_Score'].mean():.1f}")
        
        logger.info(f"\nDistribuzione per categoria:")
        for cat, count in df['Categoria_Performance'].value_counts().items():
            pct = (count / len(df)) * 100
            logger.info(f"  {cat}: {count} ({pct:.1f}%)")
        
        logger.info(f"\nTop 10 giocatori per score totale:")
        top10 = df.nlargest(10, 'Total_Score')
        for _, p in top10.iterrows():
            logger.info(f"  {p['Nome']} ({p['Ruolo']}) - "
                       f"Score: {p['Total_Score']:.1f}, "
                       f"Prezzo: {p['Prezzo_Calibrato']:.1f}€")
        
        # Maggiori differenze vs SOS
        if matched_count > 0:
            df_matched = df[df['Prezzo'].notna()].copy()
            logger.info(f"\nMaggiori aumenti rispetto a SOS:")
            top_increases = df_matched.nlargest(5, 'Differenza_vs_SOS')
            for _, p in top_increases.iterrows():
                logger.info(f"  {p['Nome']} ({p['Ruolo']}) - "
                           f"SOS: {p['Prezzo']:.0f}€ → Calibrato: {p['Prezzo_Calibrato']:.0f}€ "
                           f"(+{p['Differenza_vs_SOS']:.0f}€)")
            
            logger.info(f"\nMaggiori riduzioni rispetto a SOS:")
            top_decreases = df_matched.nsmallest(5, 'Differenza_vs_SOS')
            for _, p in top_decreases.iterrows():
                logger.info(f"  {p['Nome']} ({p['Ruolo']}) - "
                           f"SOS: {p['Prezzo']:.0f}€ → Calibrato: {p['Prezzo_Calibrato']:.0f}€ "
                           f"({p['Differenza_vs_SOS']:.0f}€)")


def main():
    """Funzione principale per test."""
    calculator = SOSCalibratedPricingCalculator()
    
    # Path dei file
    merged_file = "data/interim/perfect_merged_analysis.xlsx"
    sos_file = "data/SOS Fanta 2025_26.xlsx"
    output_file = "data/output/sos_calibrated_pricing.xlsx"
    
    try:
        # Processa i dati
        df_result = calculator.process_data(merged_file, sos_file, output_file)
        
        print(f"\n✅ Analisi completata con successo!")
        print(f"📁 File salvato: {output_file}")
        
    except Exception as e:
        logger.error(f"Errore durante il processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
