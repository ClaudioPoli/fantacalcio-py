"""
Modulo per il calcolo dei prezzi consigliati basato sui prezzi di mercato SOS Fanta
e sulle statistiche avanzate contenute nell'analisi merged.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketBasedPricingCalculator:
    """
    Calcola i prezzi consigliati considerando:
    1. Prezzi di mercato da SOS Fanta
    2. Statistiche di performance da FPEDIA e FSTATS
    3. Peso specifico per ruolo delle diverse metriche
    """
    
    def __init__(self):
        self.role_weights = {
            'P': {
                'clean_sheets_weight': 0.25,
                'saves_weight': 0.20,
                'consistency_weight': 0.25,
                'presences_weight': 0.20,
                'injury_resistance_weight': 0.10
            },
            'D': {
                'clean_sheets_weight': 0.15,
                'goals_weight': 0.15,
                'assists_weight': 0.10,
                'consistency_weight': 0.25,
                'presences_weight': 0.20,
                'defensive_solidity_weight': 0.15
            },
            'C': {
                'goals_weight': 0.15,
                'assists_weight': 0.20,
                'consistency_weight': 0.20,
                'presences_weight': 0.15,
                'offensive_actions_weight': 0.15,
                'creativity_weight': 0.15
            },
            'A': {
                'goals_weight': 0.30,
                'assists_weight': 0.15,
                'consistency_weight': 0.20,
                'presences_weight': 0.15,
                'shot_efficiency_weight': 0.20
            }
        }
    
    def load_sos_fanta_data(self, file_path: str) -> pd.DataFrame:
        """Carica e unifica i dati SOS Fanta da tutti i fogli."""
        logger.info("Caricamento dati SOS Fanta...")
        
        all_players = []
        roles = ['P', 'D', 'C', 'A']
        
        for role in roles:
            try:
                df_role = pd.read_excel(file_path, sheet_name=role)
                # Filtra solo i giocatori con prezzo (esclude righe vuote/header)
                df_role = df_role[df_role['Prezzo'].notna() & (df_role['Prezzo'] > 0)]
                all_players.append(df_role)
                logger.info(f"Caricati {len(df_role)} giocatori per ruolo {role}")
            except Exception as e:
                logger.error(f"Errore nel caricamento del ruolo {role}: {e}")
        
        sos_data = pd.concat(all_players, ignore_index=True)
        logger.info(f"Totale giocatori SOS Fanta: {len(sos_data)}")
        
        return sos_data
    
    def clean_player_name(self, name: str) -> str:
        """Pulisce il nome del giocatore per il matching."""
        if pd.isna(name):
            return ""
        
        # Rimuovi caratteri speciali e converti in maiuscolo
        name = str(name).upper()
        name = re.sub(r'[^\w\s]', '', name)
        # Rimuovi spazi multipli
        name = ' '.join(name.split())
        
        return name
    
    def extract_surname_and_initial(self, full_name: str) -> str:
        """Estrae cognome e iniziale del nome per il matching con SOS format."""
        if pd.isna(full_name):
            return ""
        
        full_name = self.clean_player_name(full_name)
        parts = full_name.split()
        
        if len(parts) == 0:
            return ""
        elif len(parts) == 1:
            return parts[0]  # Solo cognome
        else:
            # Il cognome è la prima parola, il nome la seconda
            surname = parts[0]
            name_initial = parts[1][0] if len(parts) > 1 and parts[1] else ""
            
            if name_initial:
                return f"{surname} {name_initial}."
            else:
                return surname
    
    def match_players(self, merged_df: pd.DataFrame, sos_df: pd.DataFrame) -> pd.DataFrame:
        """Match tra i giocatori del file merged e SOS Fanta."""
        logger.info("Matching dei giocatori...")
        
        # Pulisci i nomi per il matching
        merged_df['Nome_Clean'] = merged_df['Nome'].apply(self.clean_player_name)
        sos_df['Nome_Clean'] = sos_df['Nome'].apply(self.clean_player_name)
        
        # Crea versioni con cognome + iniziale e solo cognome per matching con formato SOS
        merged_df['Nome_SOS_Format'] = merged_df['Nome'].apply(self.extract_surname_and_initial)
        merged_df['Nome_Surname_Only'] = merged_df['Nome'].apply(lambda x: self.clean_player_name(x).split()[0] if self.clean_player_name(x) else "")
        
        # Prova prima il match esatto
        matched = merged_df.merge(
            sos_df[['Nome_Clean', 'Prezzo', 'Ruolo', 'Team', 'Fascia', 'MV', 'FMV', 
                   'Presenze', 'Titolarità', 'Affidabilità', 'Integrità']],
            on='Nome_Clean',
            how='left',
            suffixes=('', '_SOS')
        )
        
        # Per i non matchati, prova il match con formato SOS (Cognome + Iniziale)
        unmatched_mask = matched['Prezzo'].isna()
        unmatched_indices = matched[unmatched_mask].index
        
        if len(unmatched_indices) > 0:
            logger.info(f"Tentativo match con formato SOS per {len(unmatched_indices)} giocatori non matchati...")
            
            # Match su formato SOS con iniziale
            for idx in unmatched_indices:
                nome_sos_format = matched.loc[idx, 'Nome_SOS_Format']
                nome_surname_only = matched.loc[idx, 'Nome_Surname_Only']
                
                # Prova prima con cognome + iniziale
                sos_match = sos_df[sos_df['Nome_Clean'] == nome_sos_format]
                
                # Se non trova match, prova solo con cognome
                if sos_match.empty and nome_surname_only:
                    sos_match = sos_df[sos_df['Nome_Clean'] == nome_surname_only]
                
                # Se trova un match, aggiorna i dati
                if not sos_match.empty:
                    row = sos_match.iloc[0]  # Prendi il primo match
                    matched.loc[idx, 'Prezzo'] = row['Prezzo']
                    matched.loc[idx, 'Ruolo_SOS'] = row['Ruolo']
                    matched.loc[idx, 'Team'] = row['Team']
                    matched.loc[idx, 'Fascia'] = row['Fascia']
                    matched.loc[idx, 'MV'] = row['MV']
                    matched.loc[idx, 'FMV'] = row['FMV']
                    matched.loc[idx, 'Presenze'] = row['Presenze']
                    matched.loc[idx, 'Titolarità'] = row['Titolarità']
                    matched.loc[idx, 'Affidabilità'] = row['Affidabilità']
                    matched.loc[idx, 'Integrità'] = row['Integrità']
        
        matches_found = matched['Prezzo'].notna().sum()
        logger.info(f"Trovati {matches_found} match su {len(merged_df)} giocatori totali")
        
        # Log di alcuni esempi di match trovati
        matched_examples = matched[matched['Prezzo'].notna()].head(5)
        logger.info("Esempi di match trovati:")
        for _, row in matched_examples.iterrows():
            logger.info(f"  {row['Nome']} -> Prezzo SOS: {row['Prezzo']}€")
        
        return matched
    
    def get_technical_index_value(self, player_row: pd.Series, index_name: str) -> float:
        """Estrae il valore di un indice tecnico, gestendo i valori -1 (non applicabili)."""
        try:
            value = float(player_row.get(index_name, 0) or 0)
            return value if value > 0 else 0.0  # -1 diventa 0
        except (ValueError, TypeError):
            return 0.0

    def calculate_technical_bonus(self, player_row: pd.Series, role: str) -> float:
        """Calcola il bonus basato sugli indici tecnici specifici per ruolo."""
        technical_bonus = 0.0
        
        try:
            if role == 'ATT':
                # INDICI OFFENSIVI (peso principale per attaccanti)
                shot_on_goal = self.get_technical_index_value(player_row, 'FSTATS_Shot_on_goal_Index')
                shot_on_target = self.get_technical_index_value(player_row, 'FSTATS_Shot_on_target_Index')
                offensive_actions = self.get_technical_index_value(player_row, 'FSTATS_Offensive_actions_Index')
                attacking_area = self.get_technical_index_value(player_row, 'FSTATS_Attacking_area_Index')
                dribbles = self.get_technical_index_value(player_row, 'FSTATS_Dribbles_successful_Index')
                deep_runs = self.get_technical_index_value(player_row, 'FSTATS_Deep_runs_Index')
                
                # Normalizza gli indici (assumendo scala 0-100) e applica pesi
                technical_bonus += (shot_on_goal / 100) * 1.5      # Tiri in porta molto importanti
                technical_bonus += (shot_on_target / 100) * 1.8    # Precisione ancora più importante  
                technical_bonus += (offensive_actions / 100) * 1.2  # Azioni offensive
                technical_bonus += (attacking_area / 100) * 1.0    # Presenza in area
                technical_bonus += (dribbles / 100) * 0.8          # Dribbling
                technical_bonus += (deep_runs / 100) * 1.0         # Inserimenti
                
            elif role == 'CEN':
                # INDICI CREATIVI E OFFENSIVI (bilanciati per centrocampisti)
                pass_leading_chances = self.get_technical_index_value(player_row, 'FSTATS_Pass_leading_chances_Index')
                offensive_vertical = self.get_technical_index_value(player_row, 'FSTATS_Offensive_verticalization_Index')
                cross_accuracy = self.get_technical_index_value(player_row, 'FSTATS_Cross_accuracy_Index')
                pass_forward = self.get_technical_index_value(player_row, 'FSTATS_Pass_forward_accuracy_Index')
                offensive_actions = self.get_technical_index_value(player_row, 'FSTATS_Offensive_actions_Index')
                accompany_offensive = self.get_technical_index_value(player_row, 'FSTATS_Accompany_the_offensive_action_Index')
                
                # Pesi specifici per centrocampisti
                technical_bonus += (pass_leading_chances / 100) * 1.5    # Passaggi che creano occasioni
                technical_bonus += (offensive_vertical / 100) * 1.2      # Verticalizzazione offensiva
                technical_bonus += (cross_accuracy / 100) * 1.0          # Precisione nei cross
                technical_bonus += (pass_forward / 100) * 1.1            # Passaggi in avanti
                technical_bonus += (offensive_actions / 100) * 1.0       # Azioni offensive
                technical_bonus += (accompany_offensive / 100) * 0.8     # Supporto all'offesa
                
            elif role == 'DIF':
                # INDICI DIFENSIVI E BONUS OFFENSIVI (difensori che segnano valgono molto)
                defense_solidity = self.get_technical_index_value(player_row, 'FSTATS_Defense_solidity_Index')
                air_challenge = self.get_technical_index_value(player_row, 'FSTATS_Air_challenge_offensive_Index')
                pass_forward = self.get_technical_index_value(player_row, 'FSTATS_Pass_forward_accuracy_Index')
                set_piece_attack = self.get_technical_index_value(player_row, 'FSTATS_Set_piece_attack_Index')
                cross_accuracy = self.get_technical_index_value(player_row, 'FSTATS_Cross_accuracy_Index')
                
                # Pesi specifici per difensori
                technical_bonus += (defense_solidity / 100) * 1.5        # Solidità difensiva principale
                technical_bonus += (air_challenge / 100) * 1.2           # Gioco aereo importante
                technical_bonus += (pass_forward / 100) * 0.8            # Impostazione
                technical_bonus += (set_piece_attack / 100) * 1.3        # Calci piazzati offensivi
                technical_bonus += (cross_accuracy / 100) * 0.7          # Cross per terzini
                
            elif role == 'POR':
                # Per i portieri, usiamo principalmente difesa e gestione palla
                defense_solidity = self.get_technical_index_value(player_row, 'FSTATS_Defense_solidity_Index')
                pass_accuracy = self.get_technical_index_value(player_row, 'FSTATS_Pass_accuracy_Index')
                
                technical_bonus += (defense_solidity / 100) * 2.0        # Solidità difensiva fondamentale
                technical_bonus += (pass_accuracy / 100) * 0.5           # Precisione nei passaggi
            
            # Bonus universali per tutti i ruoli
            pass_accuracy = self.get_technical_index_value(player_row, 'FSTATS_Pass_accuracy_Index')
            technical_bonus += (pass_accuracy / 100) * 0.3  # Bonus generale per precisione
            
        except Exception as e:
            logger.debug(f"Errore nel calcolo technical bonus per {player_row.get('Nome', 'Unknown')}: {e}")
            technical_bonus = 0.0
        
        return technical_bonus

    def calculate_performance_score(self, player_row: pd.Series) -> float:
        """Calcola uno score di performance basato sulle statistiche disponibili e indici tecnici."""
        role = player_row.get('Ruolo', '')
        if pd.isna(role):
            role = player_row.get('Ruolo_SOS', '')
        
        score = 0.0
        
        try:
            # Metriche base per tutti i ruoli (peso ridotto per fare spazio agli indici tecnici)
            fantamedia = float(player_row.get('FPEDIA_Fantamedia anno 2024-2025', 0) or 0)
            presences = float(player_row.get('FPEDIA_Presenze campionato corrente', 0) or 0)
            fstats_avg = float(player_row.get('FSTATS_fanta_avg', 0) or 0)
            
            # CORREZIONE: Gestisci il valore -1 di FSTATS che indica dato non disponibile
            if fstats_avg == -1:
                fstats_avg = 0
            
            # Score base dalla fantamedia (peso ridotto)
            if fantamedia > 0:
                score += fantamedia * 0.6  # Ridotto da 0.8 a 0.6
            elif fstats_avg > 0:
                score += fstats_avg * 0.6
            
            # CORREZIONE: Se non abbiamo dati base, assegna uno score minimo per evitare 0.0
            if fantamedia == 0 and fstats_avg <= 0:
                # Se non ci sono dati, assegna uno score basso ma non 0
                score = 1.0
                logger.debug(f"Nessun dato base per {player_row.get('Nome', 'Unknown')}, score minimo assegnato")
            
            # Bonus per presenze (scala migliorata ma ridotta)
            if presences >= 25:
                score += 1.5
            elif presences >= 20:
                score += 1.2
            elif presences >= 15:
                score += 0.8
            elif presences >= 10:
                score += 0.4
            
            # Metriche specifiche per ruolo (peso ridotto)
            if role == 'POR':
                clean_sheets = float(player_row.get('FSTATS_gkCleanSheets', 0) or 0)
                goals_conceded = float(player_row.get('FSTATS_gkConcededGoals', 0) or 0)
                score += clean_sheets * 0.2  # Ridotto da 0.3
                if goals_conceded > 0:
                    score += max(0, (15 - goals_conceded) * 0.08)  # Ridotto da 0.1
                
            elif role in ['DIF', 'CEN', 'ATT']:
                goals = float(player_row.get('FSTATS_goals', 0) or 0)
                assists = float(player_row.get('FSTATS_assists', 0) or 0)
                
                if role == 'ATT':
                    score += goals * 0.3 + assists * 0.15  # Ridotto
                elif role == 'CEN':
                    score += goals * 0.25 + assists * 0.25  # Ridotto
                elif role == 'DIF':
                    score += goals * 0.4 + assists * 0.15  # Ridotto
                    # Bonus per clean sheet dei difensori
                    clean_sheets = float(player_row.get('FSTATS_gkCleanSheets', 0) or 0)
                    score += clean_sheets * 0.08  # Ridotto
            
            # NUOVO: Bonus tecnico basato sugli indici specializzati
            technical_bonus = self.calculate_technical_bonus(player_row, role)
            score += technical_bonus
            
            # CORREZIONE: Se tutti gli indici tecnici sono -1 o nulli, riduci lo score
            all_technical_null = True
            technical_indices = [
                'FSTATS_Shot_on_goal_Index', 'FSTATS_Shot_on_target_Index',
                'FSTATS_Offensive_actions_Index', 'FSTATS_Pass_leading_chances_Index',
                'FSTATS_Defense_solidity_Index'
            ]
            
            for idx_col in technical_indices:
                if idx_col in player_row.index:
                    val = player_row.get(idx_col, -1)
                    if val > 0:  # Se almeno un indice è valido
                        all_technical_null = False
                        break
            
            if all_technical_null and technical_bonus == 0:
                # Se non ci sono dati tecnici, penalizza leggermente
                score *= 0.8
                logger.debug(f"Nessun dato tecnico per {player_row.get('Nome', 'Unknown')}, score ridotto")
            
            # Non limitare il punteggio massimo, che sia realistico
            score = max(0, score)
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Errore nel calcolo performance per {player_row.get('Nome', 'Unknown')}: {e}")
            score = 2.0  # Score minimo invece di 5.0 per giocatori con errori
        
        return score
    
    def calculate_market_adjusted_price(self, player_row: pd.Series) -> float:
        """Calcola il prezzo consigliato considerando mercato e performance."""
        sos_price = player_row.get('Prezzo', None)
        current_price = player_row.get('Prezzo_Consigliato', 1.0)
        
        # Calcola performance score
        performance_score = self.calculate_performance_score(player_row)
        
        if pd.isna(sos_price) or sos_price <= 0:
            # CASO 1: Nessun prezzo SOS - usa solo performance score per stimare
            if performance_score >= 15:
                base_price = 80.0  # Top performer meritano prezzo alto
            elif performance_score >= 12:
                base_price = 40.0  
            elif performance_score >= 10:
                base_price = 20.0
            elif performance_score >= 8:
                base_price = 10.0
            elif performance_score >= 6:
                base_price = 5.0
            else:
                base_price = 1.0
                
            # Applica un adjustment basato su performance fine-tuning
            performance_multiplier = max(0.5, performance_score / 10)
            final_price = base_price * performance_multiplier
            
            # Limita il prezzo massimo senza SOS
            final_price = min(final_price, 120.0)
            
        else:
            # CASO 2: Con prezzo SOS - logica migliorata
            sos_price = float(sos_price)
            
            # CORREZIONE: Gestisci meglio le performance molto basse
            if performance_score <= 2:
                # Performance gravemente insufficiente - forte penalità
                performance_factor = 0.40  # 60% di sconto
            elif performance_score <= 4:
                performance_factor = 0.70  # 30% di sconto
            elif performance_score <= 6:
                performance_factor = 0.85  # 15% di sconto
            elif performance_score >= 15:
                performance_factor = 1.30  # 30% premium per top performer
            elif performance_score >= 12:
                performance_factor = 1.20  # 20% premium
            elif performance_score >= 10:
                performance_factor = 1.10  # 10% premium
            elif performance_score >= 8:
                performance_factor = 1.05  # 5% premium
            else:
                performance_factor = 0.95   # 5% sconto per performance medio-basse
            
            # Calcola prezzo finale come media pesata tra SOS e performance adjustment
            adjusted_sos = sos_price * performance_factor
            
            # CORREZIONE: Meno peso al prezzo SOS originale per performance molto basse/alte
            if performance_score <= 3 or performance_score >= 14:
                # Per performance estreme, dai più peso al nostro calcolo
                final_price = (adjusted_sos * 0.9) + (sos_price * 0.1)
            else:
                # Per performance normali, bilanciamento standard
                final_price = (adjusted_sos * 0.8) + (sos_price * 0.2)
        
        # Assicurati che il prezzo sia ragionevole
        final_price = max(1.0, min(final_price, 200.0))
        
        return round(final_price, 1)
    
    def add_market_insights(self, matched_df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge insights di mercato al dataframe."""
        logger.info("Aggiunta di insights di mercato...")
        
        # Calcola nuovo prezzo consigliato
        matched_df['Prezzo_Consigliato_Mercato'] = matched_df.apply(
            self.calculate_market_adjusted_price, axis=1
        )
        
        # Calcola differenza con prezzo SOS
        matched_df['Differenza_SOS'] = matched_df.apply(
            lambda row: (row['Prezzo_Consigliato_Mercato'] - row['Prezzo']) 
            if not pd.isna(row['Prezzo']) else 0, axis=1
        )
        
        # Calcola performance score
        matched_df['Performance_Score'] = matched_df.apply(
            self.calculate_performance_score, axis=1
        )
        
        # Categoria di convenienza
        def get_convenience_category(row):
            if pd.isna(row['Prezzo']):
                return 'Non in SOS'
            
            diff = row['Differenza_SOS']
            perf = row['Performance_Score']
            sos_price = row['Prezzo']
            
            # Logica migliorata per la categorizzazione
            if perf >= 8 and diff <= 0:
                return 'Top Occasione'  # Performance alta, prezzo uguale/minore
            elif perf >= 8:
                return 'Top Player'     # Performance alta (anche se costoso)
            elif diff <= -10:
                return 'Occasione'      # Prezzo molto più basso del nostro calcolo
            elif diff >= 10:
                return 'Sopravvalutato' # Prezzo molto più alto
            elif perf <= 4:
                return 'Rischio'        # Performance bassa
            else:
                return 'Normale'        # Tutto il resto
        
        matched_df['Categoria_Mercato'] = matched_df.apply(get_convenience_category, axis=1)
        
        return matched_df
    
    def process_data(self, merged_file: str, sos_file: str, output_file: str):
        """Processo principale di elaborazione dei dati."""
        logger.info("Avvio del processo di pricing basato sul mercato...")
        
        # Carica i dati
        merged_df = pd.read_excel(merged_file)
        sos_df = self.load_sos_fanta_data(sos_file)
        
        logger.info(f"Caricati {len(merged_df)} giocatori dal file merged")
        logger.info(f"Caricati {len(sos_df)} giocatori da SOS Fanta")
        
        # Match dei giocatori
        matched_df = self.match_players(merged_df, sos_df)
        
        # Aggiungi insights di mercato
        final_df = self.add_market_insights(matched_df)
        
        # Riordina le colonne per mettere le nuove informazioni all'inizio
        new_columns = [
            'Nome', 'Ruolo', 'Squadra',
            'Prezzo_Consigliato_Mercato',  # Nuovo prezzo
            'Prezzo',  # Prezzo SOS Fanta
            'Prezzo_Consigliato',  # Prezzo originale
            'Differenza_SOS',
            'Performance_Score',
            'Categoria_Mercato',
            'Fascia', 'MV', 'FMV', 'Titolarità', 'Affidabilità'
        ]
        
        # Aggiungi le colonne rimanenti
        remaining_columns = [col for col in final_df.columns if col not in new_columns]
        final_columns = new_columns + remaining_columns
        
        # Seleziona solo le colonne esistenti
        available_columns = [col for col in final_columns if col in final_df.columns]
        final_df_ordered = final_df[available_columns]
        
        # Salva il risultato
        final_df_ordered.to_excel(output_file, index=False)
        
        # Statistiche finali
        matched_players = final_df['Prezzo'].notna().sum()
        logger.info(f"Processo completato! Salvato in {output_file}")
        logger.info(f"Giocatori matchati con SOS: {matched_players}/{len(final_df)}")
        
        # Statistiche per categoria
        category_stats = final_df['Categoria_Mercato'].value_counts()
        logger.info("\nDistribuzione per categoria:")
        for cat, count in category_stats.items():
            logger.info(f"  {cat}: {count}")
        
        return final_df_ordered


def main():
    """Funzione principale per l'esecuzione del modulo."""
    calculator = MarketBasedPricingCalculator()
    
    merged_file = "data/output/perfect_merged_analysis.xlsx"
    sos_file = "data/SOS Fanta 2025_26.xlsx" 
    output_file = "data/output/market_based_analysis.xlsx"
    
    try:
        result_df = calculator.process_data(merged_file, sos_file, output_file)
        print(f"\n✅ Analisi completata! File salvato: {output_file}")
        
        # Mostra alcuni esempi
        print("\n📊 Primi 10 giocatori con migliore convenienza:")
        top_convenience = result_df[result_df['Prezzo'].notna()].nsmallest(10, 'Differenza_SOS')
        for _, player in top_convenience.iterrows():
            print(f"  {player['Nome']} ({player['Ruolo']}) - "
                  f"Consigliato: {player['Prezzo_Consigliato_Mercato']}€, "
                  f"SOS: {player['Prezzo']}€, "
                  f"Diff: {player['Differenza_SOS']:+.1f}€")
        
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {e}")
        raise


if __name__ == "__main__":
    main()
