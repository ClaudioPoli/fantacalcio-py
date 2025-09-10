#!/usr/bin/env python3
"""
🏆 FANTACALCIO PRICING SYSTEM 2025-26
Sistema completo per l'analisi e il pricing intelligente dei giocatori di fantacalcio.

Integra:
- Prezzi di mercato da SOS Fanta 
- Statistiche avanzate da FPEDIA e FSTATS
- Algoritmi di performance scoring
- Suggerimenti tattici e di formazione
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market_based_pricing import MarketBasedPricingCalculator
from advanced_player_analyzer import AdvancedPlayerAnalyzer
import pandas as pd
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_prices():
    """Aggiorna i prezzi basandosi sui dati SOS Fanta."""
    print("🔄 Aggiornamento prezzi con dati di mercato SOS Fanta...")
    
    calculator = MarketBasedPricingCalculator()
    
    merged_file = "data/output/perfect_merged_analysis.xlsx"
    sos_file = "data/SOS Fanta 2025_26.xlsx"
    output_file = "data/output/market_based_analysis.xlsx"
    
    try:
        result_df = calculator.process_data(merged_file, sos_file, output_file)
        
        # Aggiorna il file originale
        original_df = pd.read_excel(merged_file)
        updated_df = original_df.merge(
            result_df[['Nome', 'Prezzo_Consigliato_Mercato', 'Prezzo', 'Differenza_SOS', 
                      'Performance_Score', 'Categoria_Mercato', 'Fascia', 'MV', 'FMV']],
            on='Nome', how='left', suffixes=('', '_market')
        )
        
        # Sostituisci prezzo consigliato
        updated_df['Prezzo_Consigliato_Originale'] = updated_df['Prezzo_Consigliato']
        updated_df['Prezzo_Consigliato'] = updated_df['Prezzo_Consigliato_Mercato'].fillna(updated_df['Prezzo_Consigliato'])
        
        # Riorganizza colonne
        market_cols = ['Nome', 'Ruolo', 'Squadra', 'Prezzo_Consigliato', 'Prezzo', 
                      'Performance_Score', 'Categoria_Mercato', 'Differenza_SOS']
        other_cols = [c for c in updated_df.columns if c not in market_cols]
        final_cols = market_cols + other_cols
        available_cols = [c for c in final_cols if c in updated_df.columns]
        
        updated_df[available_cols].to_excel(merged_file, index=False)
        
        print("✅ Prezzi aggiornati con successo!")
        return True
        
    except Exception as e:
        logger.error(f"Errore durante l'aggiornamento: {e}")
        return False

def analyze_players():
    """Esegue analisi avanzata dei giocatori."""
    print("📊 Esecuzione analisi avanzata...")
    
    try:
        analyzer = AdvancedPlayerAnalyzer()
        analyzer.print_summary_report()
        return True
    except Exception as e:
        logger.error(f"Errore durante l'analisi: {e}")
        return False

def find_opportunities(max_price=50, min_performance=8):
    """Trova le migliori opportunità di mercato."""
    print(f"💎 Ricerca opportunità (max {max_price}€, min performance {min_performance})...")
    
    try:
        analyzer = AdvancedPlayerAnalyzer()
        opportunities = analyzer.get_top_occasions(max_price, min_performance, 20)
        
        print("\n🎯 MIGLIORI OPPORTUNITÀ:")
        print("=" * 80)
        for i, (_, player) in enumerate(opportunities.iterrows(), 1):
            print(f"{i:2}. {player['Nome']:<25} ({player['Ruolo']}) "
                  f"{player['Squadra']:<12} - {player['Prezzo']:>6.1f}€ "
                  f"(Perf: {player['Performance_Score']:>5.1f}, Cat: {player['Categoria_Mercato']})")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Errore nella ricerca opportunità: {e}")
        return None

def suggest_formation(budget=500, formation="3-5-2"):
    """Suggerisce una formazione ottimale."""
    print(f"⚽ Suggerimento formazione {formation} con budget {budget}€...")
    
    try:
        analyzer = AdvancedPlayerAnalyzer()
        suggestion = analyzer.create_formation_suggestion(budget, formation)
        
        if 'error' in suggestion:
            print(f"❌ Errore: {suggestion['error']}")
            return None
        
        print(f"\n🏆 FORMAZIONE CONSIGLIATA {formation.upper()}")
        print("=" * 60)
        print(f"Budget: {budget}€ | Costo: {suggestion['total_cost']}€ | Rimanente: {suggestion['remaining_budget']}€")
        
        for role, players in suggestion['team'].items():
            print(f"\n{role}:")
            if isinstance(players, list):
                for player in players:
                    print(f"  • {player['nome']:<30} {player['prezzo']:>6.1f}€ (perf: {player['performance']:>5.1f})")
            else:
                print(f"  • {players['nome']:<30} {players['prezzo']:>6.1f}€ (perf: {players['performance']:>5.1f})")
        
        return suggestion
        
    except Exception as e:
        logger.error(f"Errore nel suggerimento formazione: {e}")
        return None

def export_custom_list(roles=None, max_price=None, min_performance=None, output_file=None):
    """Esporta una lista personalizzata di giocatori."""
    print("📋 Generazione lista personalizzata...")
    
    try:
        analyzer = AdvancedPlayerAnalyzer()
        
        filters = {}
        if roles:
            filters['ruolo'] = roles
        if max_price:
            filters['max_price'] = max_price
        if min_performance:
            filters['min_performance'] = min_performance
        
        if not output_file:
            output_file = "data/output/custom_player_list.xlsx"
        
        filtered_df = analyzer.export_filtered_list(filters, output_file)
        
        print(f"✅ Lista esportata in {output_file}")
        print(f"📊 Trovati {len(filtered_df)} giocatori che soddisfano i criteri")
        
        return filtered_df
        
    except Exception as e:
        logger.error(f"Errore nell'esportazione: {e}")
        return None

def interactive_mode():
    """Modalità interattiva per esplorare i dati."""
    print("\n🎮 MODALITÀ INTERATTIVA")
    print("=" * 50)
    
    analyzer = AdvancedPlayerAnalyzer()
    
    while True:
        print("\nOpzioni disponibili:")
        print("1. Analisi completa")
        print("2. Trova opportunità")
        print("3. Suggerisci formazione")
        print("4. Cerca giocatore")
        print("5. Analisi per ruolo")
        print("6. Esci")
        
        choice = input("\nScegli un'opzione (1-6): ").strip()
        
        if choice == '1':
            analyzer.print_summary_report()
            
        elif choice == '2':
            max_p = input("Prezzo massimo (default 50): ").strip()
            min_perf = input("Performance minima (default 8): ").strip()
            
            max_p = float(max_p) if max_p else 50
            min_perf = float(min_perf) if min_perf else 8
            
            find_opportunities(max_p, min_perf)
            
        elif choice == '3':
            budget = input("Budget totale (default 500): ").strip()
            form = input("Formazione (default 3-5-2): ").strip()
            
            budget = float(budget) if budget else 500
            form = form if form else "3-5-2"
            
            suggest_formation(budget, form)
            
        elif choice == '4':
            name = input("Nome giocatore da cercare: ").strip().upper()
            results = analyzer.df[analyzer.df['Nome'].str.contains(name, na=False)]
            
            if len(results) > 0:
                print(f"\n🔍 Trovati {len(results)} giocatori:")
                for _, player in results.iterrows():
                    price = f"{player['Prezzo']:.1f}€" if not pd.isna(player['Prezzo']) else "N/A"
                    print(f"  • {player['Nome']} ({player['Ruolo']}) {player['Squadra']} - "
                          f"Prezzo: {price}, Performance: {player['Performance_Score']:.1f}")
            else:
                print("❌ Nessun giocatore trovato")
                
        elif choice == '5':
            roles = ['POR', 'DIF', 'CEN', 'ATT']
            print("Ruoli disponibili:", ', '.join(roles))
            role = input("Inserisci ruolo: ").strip().upper()
            
            if role in roles:
                analysis = analyzer.get_role_analysis(role)
                if 'error' not in analysis:
                    print(f"\n📊 ANALISI RUOLO {role}")
                    print(f"Giocatori totali: {analysis['total_players']}")
                    print(f"Con prezzo SOS: {analysis['with_sos_price']}")
                    print(f"Prezzo medio: {analysis['avg_price']:.1f}€")
                    print(f"Performance media: {analysis['avg_performance']:.1f}")
                    
                    print("\n🏅 Top per fascia di prezzo:")
                    for band, player in analysis['top_by_price_band'].items():
                        print(f"  {band}: {player['nome']} - "
                              f"{player['prezzo']:.1f}€ (perf: {player['performance']:.1f})")
                else:
                    print(f"❌ {analysis['error']}")
            else:
                print("❌ Ruolo non valido")
                
        elif choice == '6':
            print("👋 Arrivederci!")
            break
            
        else:
            print("❌ Opzione non valida")

def main():
    """Funzione principale con gestione argomenti da riga di comando."""
    parser = argparse.ArgumentParser(description='Sistema di Pricing Fantacalcio 2025-26')
    parser.add_argument('--update', action='store_true', help='Aggiorna i prezzi con dati SOS Fanta')
    parser.add_argument('--analyze', action='store_true', help='Esegui analisi completa')
    parser.add_argument('--opportunities', action='store_true', help='Trova opportunità di mercato')
    parser.add_argument('--formation', type=str, default='3-5-2', help='Suggerisci formazione (es. 3-5-2)')
    parser.add_argument('--budget', type=float, default=500, help='Budget per formazione')
    parser.add_argument('--max-price', type=float, help='Prezzo massimo per ricerca')
    parser.add_argument('--min-performance', type=float, help='Performance minima per ricerca')
    parser.add_argument('--interactive', action='store_true', help='Modalità interattiva')
    
    args = parser.parse_args()
    
    print("🏆 FANTACALCIO PRICING SYSTEM 2025-26")
    print("=" * 50)
    
    # Se nessun argomento, modalità interattiva
    if not any(vars(args).values()) or args.interactive:
        interactive_mode()
        return
    
    if args.update:
        if not update_prices():
            return 1
    
    if args.analyze:
        if not analyze_players():
            return 1
    
    if args.opportunities:
        max_p = args.max_price or 50
        min_perf = args.min_performance or 8
        find_opportunities(max_p, min_perf)
    
    if args.formation:
        suggest_formation(args.budget, args.formation)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
