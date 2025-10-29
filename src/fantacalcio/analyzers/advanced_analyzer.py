"""
Modulo per l'analisi avanzata dei giocatori di fantacalcio.
Gestisce l'elaborazione dei dati FPEDIA e FSTATS e il loro merge.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import sys
from pathlib import Path

# Aggiungi la root del progetto al path per importare i moduli legacy
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from convenienza_calculator import (
    calcola_convenienza_fpedia, 
    calcola_convenienza_FSTATS,
    calcola_prezzo_massimo_consigliato,
    calcola_score_fpedia,
    calcola_score_fstats
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedAnalyzer:
    """
    Gestisce l'analisi avanzata dei dati FPEDIA e FSTATS,
    incluso il calcolo delle convenienza e il merge delle fonti.
    """
    
    def __init__(self):
        self.logger = logger
    
    def analyze_fpedia_data(self, df_fpedia: pd.DataFrame) -> pd.DataFrame:
        """
        Analizza i dati FPEDIA calcolando convenienza e prezzi consigliati.
        
        Args:
            df_fpedia: DataFrame con i dati FPEDIA
            
        Returns:
            DataFrame analizzato con colonne aggiuntive per convenienza e prezzi
        """
        logger.info("Iniziando analisi dati FPEDIA...")
        
        try:
            # Calcola convenienza FPEDIA
            df_analyzed = calcola_convenienza_fpedia(df_fpedia.copy())
            
            # Calcola score FPEDIA per ogni ruolo
            df_analyzed['Score_FPEDIA'] = 0.0
            for ruolo in df_analyzed['Ruolo'].unique():
                if pd.isna(ruolo):
                    continue
                mask = df_analyzed['Ruolo'] == ruolo
                df_ruolo = df_analyzed[mask]
                scores = calcola_score_fpedia(df_ruolo, ruolo)
                df_analyzed.loc[mask, 'Score_FPEDIA'] = scores
            
            # Calcola prezzo massimo consigliato
            df_analyzed = calcola_prezzo_massimo_consigliato(df_analyzed)
            
            # Aggiungi metadati
            df_analyzed['Fonte'] = 'FPEDIA'
            df_analyzed['Data_Analisi'] = pd.Timestamp.now()
            
            logger.info(f"Analisi FPEDIA completata per {len(df_analyzed)} giocatori")
            return df_analyzed
            
        except Exception as e:
            logger.error(f"Errore nell'analisi FPEDIA: {e}")
            raise
    
    def analyze_fstats_data(self, df_fstats: pd.DataFrame) -> pd.DataFrame:
        """
        Analizza i dati FSTATS calcolando convenienza e prezzi consigliati.
        
        Args:
            df_fstats: DataFrame con i dati FSTATS
            
        Returns:
            DataFrame analizzato con colonne aggiuntive per convenienza e prezzi
        """
        logger.info("Iniziando analisi dati FSTATS...")
        
        try:
            # Calcola convenienza FSTATS
            df_analyzed = calcola_convenienza_FSTATS(df_fstats.copy())
            
            # Calcola score FSTATS per ogni ruolo
            df_analyzed['Score_FSTATS'] = 0.0
            for ruolo in df_analyzed['Ruolo'].unique():
                if pd.isna(ruolo):
                    continue
                mask = df_analyzed['Ruolo'] == ruolo
                df_ruolo = df_analyzed[mask]
                scores = calcola_score_fstats(df_ruolo, ruolo)
                df_analyzed.loc[mask, 'Score_FSTATS'] = scores
            
            # Calcola prezzo massimo consigliato
            df_analyzed = calcola_prezzo_massimo_consigliato(df_analyzed)
            
            # Aggiungi metadati
            df_analyzed['Fonte'] = 'FSTATS'
            df_analyzed['Data_Analisi'] = pd.Timestamp.now()
            
            logger.info(f"Analisi FSTATS completata per {len(df_analyzed)} giocatori")
            return df_analyzed
            
        except Exception as e:
            logger.error(f"Errore nell'analisi FSTATS: {e}")
            raise
    
    def merge_analyses(self, df_fpedia: pd.DataFrame, df_fstats: pd.DataFrame) -> pd.DataFrame:
        """
        Merge intelligente delle analisi FPEDIA e FSTATS.
        
        Args:
            df_fpedia: DataFrame analizzato FPEDIA
            df_fstats: DataFrame analizzato FSTATS
            
        Returns:
            DataFrame merged con le migliori informazioni da entrambe le fonti
        """
        logger.info("Iniziando merge delle analisi...")
        
        try:
            # Pulizia nomi per il match
            df_fpedia_clean = df_fpedia.copy()
            df_fstats_clean = df_fstats.copy()
            
            df_fpedia_clean['Nome_Clean'] = df_fpedia_clean['Nome'].str.strip().str.lower()
            df_fstats_clean['Nome_Clean'] = df_fstats_clean['Nome'].str.strip().str.lower()
            
            # Merge principale sui nomi
            df_merged = pd.merge(
                df_fpedia_clean, 
                df_fstats_clean,
                on='Nome_Clean',
                how='outer',
                suffixes=('_FPEDIA', '_FSTATS')
            )
            
            # Risolvi conflitti e crea colonne unificate
            df_merged = self._resolve_merge_conflicts(df_merged)
            
            # Calcola score combinato
            df_merged = self._calculate_combined_scores(df_merged)
            
            # Pulisci colonne temporanee
            df_merged = df_merged.drop('Nome_Clean', axis=1, errors='ignore')
            
            logger.info(f"Merge completato: {len(df_merged)} giocatori nel dataset unificato")
            return df_merged
            
        except Exception as e:
            logger.error(f"Errore nel merge: {e}")
            raise
    
    def _resolve_merge_conflicts(self, df_merged: pd.DataFrame) -> pd.DataFrame:
        """Risolve i conflitti tra le colonne delle due fonti."""
        
        # Colonne da unificare con priorità
        column_priorities = {
            'Nome': 'FPEDIA',  # FPEDIA ha nomi più puliti
            'Ruolo': 'FPEDIA',
            'Squadra': 'FPEDIA',
            'Convenienza': 'average',  # Media delle due fonti
            'Prezzo_Massimo_Consigliato': 'average'
        }
        
        for col, priority in column_priorities.items():
            col_fpedia = f"{col}_FPEDIA"
            col_fstats = f"{col}_FSTATS"
            
            if col_fpedia in df_merged.columns and col_fstats in df_merged.columns:
                if priority == 'FPEDIA':
                    df_merged[col] = df_merged[col_fpedia].fillna(df_merged[col_fstats])
                elif priority == 'FSTATS':
                    df_merged[col] = df_merged[col_fstats].fillna(df_merged[col_fpedia])
                elif priority == 'average':
                    df_merged[col] = df_merged[[col_fpedia, col_fstats]].mean(axis=1, skipna=True)
            elif col_fpedia in df_merged.columns:
                df_merged[col] = df_merged[col_fpedia]
            elif col_fstats in df_merged.columns:
                df_merged[col] = df_merged[col_fstats]
        
        return df_merged
    
    def _calculate_combined_scores(self, df_merged: pd.DataFrame) -> pd.DataFrame:
        """Calcola score combinati dalle due fonti."""
        
        # Performance Score combinato (se disponibili entrambi i score)
        if 'Score_FPEDIA' in df_merged.columns and 'Score_FSTATS' in df_merged.columns:
            # Normalizza i punteggi (0-20 range)
            score_fpedia_norm = df_merged['Score_FPEDIA'].fillna(0) / 100 * 20
            score_fstats_norm = df_merged['Score_FSTATS'].fillna(0) / 100 * 20
            
            # Media pesata: FPEDIA 40%, FSTATS 60% (più oggettivo)
            df_merged['Performance_Score'] = (
                score_fpedia_norm * 0.4 + 
                score_fstats_norm * 0.6
            ).round(2)
        elif 'Score_FPEDIA' in df_merged.columns:
            df_merged['Performance_Score'] = (df_merged['Score_FPEDIA'].fillna(0) / 100 * 20).round(2)
        elif 'Score_FSTATS' in df_merged.columns:
            df_merged['Performance_Score'] = (df_merged['Score_FSTATS'].fillna(0) / 100 * 20).round(2)
        else:
            df_merged['Performance_Score'] = 10.0  # Score neutro
        
        # Convenienza combinata
        conv_fpedia = df_merged.get('Convenienza_FPEDIA', pd.Series(0, index=df_merged.index))
        conv_fstats = df_merged.get('Convenienza_FSTATS', pd.Series(0, index=df_merged.index))
        
        df_merged['Convenienza_Combinata'] = (
            (conv_fpedia.fillna(0) * 0.4 + conv_fstats.fillna(0) * 0.6)
        ).round(3)
        
        # Prezzo consigliato finale
        prezzo_fpedia = df_merged.get('Prezzo_Massimo_Consigliato_FPEDIA', pd.Series(1, index=df_merged.index))
        prezzo_fstats = df_merged.get('Prezzo_Massimo_Consigliato_FSTATS', pd.Series(1, index=df_merged.index))
        
        df_merged['Prezzo_Consigliato'] = (
            (prezzo_fpedia.fillna(1) + prezzo_fstats.fillna(1)) / 2
        ).round(1)
        
        return df_merged


class AdvancedPlayerAnalyzer(AdvancedAnalyzer):
    """
    Mantiene compatibilità con il codice esistente.
    Fornisce funzionalità avanzate per l'analisi e la ricerca dei giocatori.
    """
    
    def __init__(self, data_file: str = "data/output/perfect_merged_analysis.xlsx"):
        super().__init__()
        self.data_file = data_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Carica i dati dall'Excel."""
        try:
            self.df = pd.read_excel(self.data_file)
            logger.info(f"Caricati {len(self.df)} giocatori da {self.data_file}")
        except Exception as e:
            logger.error(f"Errore nel caricamento del file {self.data_file}: {e}")
            raise
    
    def get_top_occasions(self, max_price: float = 50, min_performance: float = 8, top_n: int = 20) -> pd.DataFrame:
        """Trova le migliori occasioni di mercato."""
        filtered = self.df[
            (self.df['Prezzo'].notna()) &
            (self.df['Prezzo'] <= max_price) &
            (self.df['Performance_Score'] >= min_performance)
        ].copy()
        
        # Calcola un score di convenienza
        filtered['Convenience_Score'] = (
            filtered['Performance_Score'] * 0.6 + 
            ((max_price - filtered['Prezzo']) / max_price * 10) * 0.4
        )
        
        return filtered.nlargest(top_n, 'Convenience_Score')[
            ['Nome', 'Ruolo', 'Squadra', 'Prezzo', 'Performance_Score', 
             'Categoria_Mercato', 'Convenience_Score']
        ]
    
    def get_role_analysis(self, role: str) -> Dict:
        """Analisi approfondita per un ruolo specifico."""
        role_df = self.df[self.df['Ruolo'] == role].copy()
        
        if len(role_df) == 0:
            return {"error": f"Nessun giocatore trovato per il ruolo {role}"}
        
        # Statistiche generali
        stats = {
            "total_players": len(role_df),
            "with_sos_price": role_df['Prezzo'].notna().sum(),
            "avg_price": role_df['Prezzo'].mean(),
            "avg_performance": role_df['Performance_Score'].mean(),
            "price_range": {
                "min": role_df['Prezzo'].min(),
                "max": role_df['Prezzo'].max()
            }
        }
        
        # Top performer per fascia di prezzo
        price_bands = [
            ("Budget", 0, 10),
            ("Medio", 10, 30), 
            ("Alto", 30, 80),
            ("Premium", 80, 200)
        ]
        
        top_by_price_band = {}
        for band_name, min_p, max_p in price_bands:
            band_players = role_df[
                (role_df['Prezzo'] >= min_p) & 
                (role_df['Prezzo'] <= max_p) &
                (role_df['Prezzo'].notna())
            ]
            
            if len(band_players) > 0:
                top_player = band_players.nlargest(1, 'Performance_Score')
                if len(top_player) > 0:
                    player = top_player.iloc[0]
                    top_by_price_band[band_name] = {
                        "nome": player['Nome'],
                        "prezzo": player['Prezzo'],
                        "performance": player['Performance_Score'],
                        "categoria": player.get('Categoria_Mercato', 'N/A')
                    }
        
        stats['top_by_price_band'] = top_by_price_band
        return stats
    
    def find_hidden_gems(self, max_price: float = 15, min_performance: float = 6) -> pd.DataFrame:
        """Trova i 'gioielli nascosti' - giocatori economici ma con buone performance."""
        gems = self.df[
            (self.df['Prezzo'].notna()) &
            (self.df['Prezzo'] <= max_price) &
            (self.df['Performance_Score'] >= min_performance)
        ].copy()
        
        # Score basato su rapporto qualità/prezzo
        gems['Value_Score'] = gems['Performance_Score'] / gems['Prezzo'] * 10
        
        return gems.nlargest(15, 'Value_Score')[
            ['Nome', 'Ruolo', 'Squadra', 'Prezzo', 'Performance_Score', 
             'Value_Score', 'Categoria_Mercato']
        ]
    
    def get_team_analysis(self, team: str) -> Dict:
        """Analisi per squadra."""
        team_df = self.df[self.df['Squadra'] == team].copy()
        
        if len(team_df) == 0:
            return {"error": f"Nessun giocatore trovato per la squadra {team}"}
        
        stats = {
            "total_players": len(team_df),
            "avg_performance": team_df['Performance_Score'].mean(),
            "top_player": None,
            "best_value": None,
            "role_distribution": team_df['Ruolo'].value_counts().to_dict()
        }
        
        # Top performer della squadra
        if len(team_df) > 0:
            top = team_df.nlargest(1, 'Performance_Score').iloc[0]
            stats['top_player'] = {
                "nome": top['Nome'],
                "ruolo": top['Ruolo'],
                "prezzo": top.get('Prezzo', 'N/A'),
                "performance": top['Performance_Score']
            }
        
        # Miglior rapporto qualità/prezzo
        value_players = team_df[team_df['Prezzo'].notna()]
        if len(value_players) > 0:
            value_players = value_players.copy()
            value_players['Value_Score'] = value_players['Performance_Score'] / value_players['Prezzo']
            best_value = value_players.nlargest(1, 'Value_Score').iloc[0]
            stats['best_value'] = {
                "nome": best_value['Nome'],
                "ruolo": best_value['Ruolo'],
                "prezzo": best_value['Prezzo'],
                "performance": best_value['Performance_Score'],
                "value_score": best_value['Value_Score']
            }
        
        return stats
    
    def create_formation_suggestion(self, budget: float, formation: str = "3-5-2") -> Dict:
        """Suggerisce una formazione ottimale dato un budget."""
        # Parse della formazione
        formation_parts = formation.split('-')
        if len(formation_parts) != 3:
            return {"error": "Formato formazione non valido. Usa formato come '3-5-2'"}
        
        try:
            defenders = int(formation_parts[0])
            midfielders = int(formation_parts[1])
            attackers = int(formation_parts[2])
        except ValueError:
            return {"error": "Numeri non validi nella formazione"}
        
        # Budget allocation (percentuali tipiche)
        budget_allocation = {
            'POR': budget * 0.08,  # 8% portiere
            'DIF': budget * 0.25,  # 25% difensori
            'CEN': budget * 0.37,  # 37% centrocampisti
            'ATT': budget * 0.30   # 30% attaccanti
        }
        
        suggested_team = {}
        total_cost = 0
        
        # Portiere (sempre 1)
        por_budget = budget_allocation['POR']
        portieri = self.df[
            (self.df['Ruolo'] == 'POR') & 
            (self.df['Prezzo'].notna()) & 
            (self.df['Prezzo'] <= por_budget * 1.5)  # Flessibilità del 50%
        ].nlargest(1, 'Performance_Score')
        
        if len(portieri) > 0:
            por = portieri.iloc[0]
            suggested_team['POR'] = {
                "nome": por['Nome'],
                "prezzo": por['Prezzo'],
                "performance": por['Performance_Score']
            }
            total_cost += por['Prezzo']
        
        # Difensori
        def_budget_per_player = budget_allocation['DIF'] / defenders
        difensori = self.df[
            (self.df['Ruolo'] == 'DIF') & 
            (self.df['Prezzo'].notna()) & 
            (self.df['Prezzo'] <= def_budget_per_player * 2)
        ].nlargest(defenders, 'Performance_Score')
        
        suggested_team['DIF'] = []
        for _, dif in difensori.iterrows():
            suggested_team['DIF'].append({
                "nome": dif['Nome'],
                "prezzo": dif['Prezzo'],
                "performance": dif['Performance_Score']
            })
            total_cost += dif['Prezzo']
        
        # Centrocampisti
        cen_budget_per_player = budget_allocation['CEN'] / midfielders
        centrocampisti = self.df[
            (self.df['Ruolo'] == 'CEN') & 
            (self.df['Prezzo'].notna()) & 
            (self.df['Prezzo'] <= cen_budget_per_player * 2)
        ].nlargest(midfielders, 'Performance_Score')
        
        suggested_team['CEN'] = []
        for _, cen in centrocampisti.iterrows():
            suggested_team['CEN'].append({
                "nome": cen['Nome'],
                "prezzo": cen['Prezzo'],
                "performance": cen['Performance_Score']
            })
            total_cost += cen['Prezzo']
        
        # Attaccanti
        att_budget_per_player = budget_allocation['ATT'] / attackers
        attaccanti = self.df[
            (self.df['Ruolo'] == 'ATT') & 
            (self.df['Prezzo'].notna()) & 
            (self.df['Prezzo'] <= att_budget_per_player * 2)
        ].nlargest(attackers, 'Performance_Score')
        
        suggested_team['ATT'] = []
        for _, att in attaccanti.iterrows():
            suggested_team['ATT'].append({
                "nome": att['Nome'],
                "prezzo": att['Prezzo'],
                "performance": att['Performance_Score']
            })
            total_cost += att['Prezzo']
        
        return {
            "formation": formation,
            "budget": budget,
            "total_cost": round(total_cost, 1),
            "remaining_budget": round(budget - total_cost, 1),
            "team": suggested_team
        }
    
    def export_filtered_list(self, filters: Dict, output_file: str = None) -> pd.DataFrame:
        """Esporta una lista filtrata di giocatori."""
        filtered_df = self.df.copy()
        
        # Applica i filtri
        if 'ruolo' in filters:
            filtered_df = filtered_df[filtered_df['Ruolo'].isin(filters['ruolo'])]
        
        if 'max_price' in filters:
            filtered_df = filtered_df[filtered_df['Prezzo'] <= filters['max_price']]
        
        if 'min_performance' in filters:
            filtered_df = filtered_df[filtered_df['Performance_Score'] >= filters['min_performance']]
        
        if 'categoria' in filters:
            filtered_df = filtered_df[filtered_df['Categoria_Mercato'].isin(filters['categoria'])]
        
        if 'squadre' in filters:
            filtered_df = filtered_df[filtered_df['Squadra'].isin(filters['squadre'])]
        
        # Ordina per performance score
        filtered_df = filtered_df.sort_values('Performance_Score', ascending=False)
        
        # Salva se richiesto
        if output_file:
            filtered_df.to_excel(output_file, index=False)
            logger.info(f"Lista filtrata salvata in {output_file}")
        
        return filtered_df
    
    def print_summary_report(self):
        """Stampa un report riassuntivo completo."""
        print("=" * 60)
        print("🏆 REPORT RIASSUNTIVO FANTACALCIO 2025-26")
        print("=" * 60)
        
        total_players = len(self.df)
        with_price = self.df['Prezzo'].notna().sum()
        
        print(f"📊 STATISTICHE GENERALI:")
        print(f"  • Giocatori totali: {total_players}")
        print(f"  • Con prezzo SOS Fanta: {with_price} ({with_price/total_players*100:.1f}%)")
        print(f"  • Media performance: {self.df['Performance_Score'].mean():.1f}")
        
        print(f"\n📈 DISTRIBUZIONE CATEGORIE:")
        for cat, count in self.df['Categoria_Mercato'].value_counts().items():
            print(f"  • {cat}: {count}")
        
        print(f"\n⚽ DISTRIBUZIONE RUOLI:")
        for role, count in self.df['Ruolo'].value_counts().items():
            avg_price = self.df[self.df['Ruolo'] == role]['Prezzo'].mean()
            print(f"  • {role}: {count} giocatori (prezzo medio: {avg_price:.1f}€)")
        
        print(f"\n🏅 TOP 5 PERFORMANCE:")
        top_performers = self.df.nlargest(5, 'Performance_Score')
        for i, (_, player) in enumerate(top_performers.iterrows(), 1):
            price = player['Prezzo'] if not pd.isna(player['Prezzo']) else 'N/A'
            print(f"  {i}. {player['Nome']} ({player['Ruolo']}) - "
                  f"Perf: {player['Performance_Score']:.1f}, Prezzo: {price}€")
        
        print(f"\n💎 TOP 5 OCCASIONI (rapporto qualità/prezzo):")
        value_players = self.df[self.df['Prezzo'].notna()].copy()
        value_players['Value_Ratio'] = value_players['Performance_Score'] / value_players['Prezzo']
        top_value = value_players.nlargest(5, 'Value_Ratio')
        for i, (_, player) in enumerate(top_value.iterrows(), 1):
            print(f"  {i}. {player['Nome']} ({player['Ruolo']}) - "
                  f"Prezzo: {player['Prezzo']}€, Perf: {player['Performance_Score']:.1f}")
        
        print("=" * 60)


def main():
    """Funzione di esempio per l'uso del modulo."""
    analyzer = AdvancedPlayerAnalyzer()
    
    # Report completo
    analyzer.print_summary_report()
    
    print(f"\n🔍 MIGLIORI OCCASIONI (< 50€, performance >= 8):")
    occasioni = analyzer.get_top_occasions(max_price=50, min_performance=8)
    print(occasioni.to_string(index=False))
    
    print(f"\n💎 GIOIELLI NASCOSTI (< 15€, performance >= 6):")
    gems = analyzer.find_hidden_gems(max_price=15, min_performance=6)
    print(gems.to_string(index=False))
    
    print(f"\n📋 SUGGERIMENTO FORMAZIONE 3-5-2 con budget 500€:")
    formation = analyzer.create_formation_suggestion(budget=500, formation="3-5-2")
    if 'error' not in formation:
        print(f"Costo totale: {formation['total_cost']}€ (rimanente: {formation['remaining_budget']}€)")
        for role, players in formation['team'].items():
            print(f"\n{role}:")
            if isinstance(players, list):
                for player in players:
                    print(f"  • {player['nome']} - {player['prezzo']}€ (perf: {player['performance']:.1f})")
            else:
                print(f"  • {players['nome']} - {players['prezzo']}€ (perf: {players['performance']:.1f})")
    else:
        print(f"Errore: {formation['error']}")


if __name__ == "__main__":
    main()
