#!/usr/bin/env python3
"""
Fantacalcio Analysis System - Standalone Entry Point

Sistema autonomo per l'analisi dei giocatori di fantacalcio.
Calcola prezzi consigliati basandosi esclusivamente su 19 indici tecnici,
senza dipendenze da dati di mercato esterni.
"""

import sys
import argparse
import pandas as pd
from pathlib import Path

# Aggiungi src al path per gli import
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import del nuovo sistema autonomo
from src.fantacalcio.analyzers.standalone_pricing import StandalonePricingCalculator

def main():
    parser = argparse.ArgumentParser(
        description='Sistema di Analisi Fantacalcio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
    python main.py --mode analysis           # Analisi completa autonoma
    python main.py --interactive             # Modalità interattiva
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['analysis'],
        default='analysis',
        help='Modalità di esecuzione'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Modalità interattiva'
    )
    
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Directory contenente i dati (default: data)'
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        run_interactive_mode()
    else:
        run_standalone_analysis(args.data_dir)


def run_interactive_mode():
    """Esegue il sistema in modalità interattiva."""
    print("🚀 SISTEMA ANALISI FANTACALCIO AUTONOMO")
    print("=" * 50)
    
    while True:
        print("\n📊 Scegli un'operazione:")
        print("1. 🧮 Calcolo prezzi autonomo (senza SOS)")
        print("2. 🏆 Analisi top player per ruolo") 
        print("3. 💰 Trova migliori occasioni")
        print("4. ❌ Esci")
        
        choice = input("\nSelezione (1-4): ").strip()
        
        if choice == '1':
            run_standalone_analysis()
        elif choice == '2':
            show_top_players_by_role()
        elif choice == '3':
            show_best_value_players()
        elif choice == '4':
            print("👋 Arrivederci!")
            break
        else:
            print("❌ Scelta non valida. Riprova.")


def run_standalone_analysis(data_dir: str = 'data'):
    """Esegue l'analisi autonoma dei prezzi."""
    print("\n🧮 AVVIO CALCOLO PREZZI AUTONOMO...")
    
    try:
        calculator = StandalonePricingCalculator()
        
        # File paths
        merged_file = f"{data_dir}/output/perfect_merged_analysis.xlsx"
        output_file = f"{data_dir}/output/standalone_pricing_analysis.xlsx"
        
        # Verifica che il file merged esista
        if not Path(merged_file).exists():
            print(f"❌ File non trovato: {merged_file}")
            print("   Assicurati di aver prima generato il file merged con i dati FPEDIA/FSTATS")
            return
        
        # Processa i dati
        df_result = calculator.process_data(merged_file, output_file)
        
        # Mostra statistiche rapide
        total = len(df_result)
        avg_perf = df_result['Performance_Score'].mean()
        avg_price = df_result['Prezzo_Consigliato'].mean()
        
        print(f"\n✅ ANALISI AUTONOMA COMPLETATA!")
        print(f"   📁 File salvato: {output_file}")
        print(f"   👥 Giocatori analizzati: {total}")
        print(f"   📊 Performance media: {avg_perf:.2f}/20")
        print(f"   💰 Prezzo medio calcolato: {avg_price:.1f}€")
        
        # Mostra distribuzione categorie
        print(f"\n📈 DISTRIBUZIONE CATEGORIE:")
        for category, count in df_result['Categoria'].value_counts().items():
            percentage = (count / total) * 100
            print(f"   • {category}: {count} ({percentage:.1f}%)")
        
        # Mostra top 5 per ruolo
        print(f"\n🏆 TOP 5 PER RUOLO:")
        for role in ['ATT', 'CEN', 'DIF', 'POR']:
            top_players = calculator.get_top_players_by_role(df_result, role, 5)
            if len(top_players) > 0:
                print(f"\n   {role}:")
                for _, p in top_players.iterrows():
                    print(f"     • {p['Nome']} - "
                          f"Perf: {p['Performance_Score']:.1f}, "
                          f"Prezzo: {p['Prezzo_Consigliato']:.1f}€")
        
        # Mostra migliori occasioni
        print(f"\n💎 MIGLIORI OCCASIONI (Performance >8, Prezzo <15€):")
        best_values = calculator.get_best_value_players(df_result, 15.0)
        for _, p in best_values.head(10).iterrows():
            print(f"   • {p['Nome']} ({p['Ruolo']}) - "
                  f"Perf: {p['Performance_Score']:.1f}, "
                  f"Prezzo: {p['Prezzo_Consigliato']:.1f}€")
        
    except Exception as e:
        print(f"❌ Errore durante l'analisi autonoma: {e}")
        import traceback
        traceback.print_exc()


def show_top_players_by_role(data_dir: str = 'data'):
    """Mostra i migliori giocatori per ruolo."""
    try:
        output_file = f"{data_dir}/output/standalone_pricing_analysis.xlsx"
        if not Path(output_file).exists():
            print("❌ Devi prima eseguire l'analisi autonoma!")
            return
            
        df = pd.read_excel(output_file)
        calculator = StandalonePricingCalculator()
        
        print("\n🏆 TOP 10 GIOCATORI PER RUOLO:")
        for role in ['ATT', 'CEN', 'DIF', 'POR']:
            top_players = calculator.get_top_players_by_role(df, role, 10)
            if len(top_players) > 0:
                print(f"\n{role} (Top 10):")
                for i, (_, p) in enumerate(top_players.iterrows(), 1):
                    print(f"  {i:2d}. {p['Nome']} - "
                          f"Perf: {p['Performance_Score']:.1f}, "
                          f"Prezzo: {p['Prezzo_Consigliato']:.1f}€, "
                          f"Cat: {p['Categoria']}")
                          
    except Exception as e:
        print(f"❌ Errore: {e}")


def show_best_value_players(data_dir: str = 'data'):
    """Mostra i giocatori con miglior rapporto qualità/prezzo."""
    try:
        output_file = f"{data_dir}/output/standalone_pricing_analysis.xlsx"
        if not Path(output_file).exists():
            print("❌ Devi prima eseguire l'analisi autonoma!")
            return
            
        df = pd.read_excel(output_file)
        calculator = StandalonePricingCalculator()
        
        print("\n💰 MIGLIORI RAPPORTI QUALITÀ/PREZZO:")
        
        # Diverse fasce di prezzo
        price_ranges = [
            (0, 5, "FASCIA LOW COST (0-5€)"),
            (5, 15, "FASCIA MEDIA (5-15€)"),
            (15, 30, "FASCIA ALTA (15-30€)"),
            (30, 100, "FASCIA TOP (30€+)")
        ]
        
        for min_price, max_price, label in price_ranges:
            range_players = df[
                (df['Prezzo_Consigliato'] >= min_price) & 
                (df['Prezzo_Consigliato'] <= max_price) &
                (df['Performance_Score'] >= 6.0)  # Almeno performance decente
            ].sort_values('Performance_Score', ascending=False)
            
            if len(range_players) > 0:
                print(f"\n{label}:")
                for _, p in range_players.head(5).iterrows():
                    ratio = p['Performance_Score'] / max(p['Prezzo_Consigliato'], 1)
                    print(f"  • {p['Nome']} ({p['Ruolo']}) - "
                          f"Perf: {p['Performance_Score']:.1f}, "
                          f"Prezzo: {p['Prezzo_Consigliato']:.1f}€, "
                          f"Ratio: {ratio:.2f}")
                          
    except Exception as e:
        print(f"❌ Errore: {e}")


if __name__ == "__main__":
    main()
