"""
Modulo per la ricerca e l'analisi avanzata dei giocatori 
basata sui prezzi di mercato e le performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedPlayerAnalyzer:
    """
    Fornisce funzionalità avanzate per l'analisi e la ricerca dei giocatori
    basata sui dati di mercato, performance e convenienza.
    """
    
    def __init__(self, data_file: str = "data/output/perfect_merged_analysis.xlsx"):
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
