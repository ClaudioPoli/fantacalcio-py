#!/usr/bin/env python3
"""
🏆 FANTACALCIO ANALYSIS WORKFLOW 2025-26
Sistema ristrutturato per l'analisi e il pricing dei giocatori di fantacalcio.

Flusso di lavoro:
1. Recupero dati FPEDIA e FSTATS (opzionale)
2. Creazione file fpedia_analysis.xlsx e FSTATS_analysis.xlsx (interim)
3. Merge in perfect_merged_analysis.xlsx (interim)
4. Calcolo prezzi finale in output/
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
import os
from typing import Optional

# Aggiungi la root al path per gli import
sys.path.insert(0, str(Path(__file__).parent))

# Import moduli dal package src
from src.fantacalcio.data.retriever import scrape_fpedia, fetch_FSTATS_data
from src.fantacalcio.data.processor import process_fpedia_data, process_FSTATS_data


class FantacalcioWorkflow:
    """Gestisce il flusso di lavoro completo dell'analisi fantacalcio."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.interim_dir = os.path.join(data_dir, "interim")
        self.output_dir = os.path.join(data_dir, "output")

        # Assicurati che le directory esistano
        os.makedirs(self.interim_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def run_complete_workflow(
        self,
        update_data: bool = False,
        use_market_pricing: bool = True,
        use_sos_calibrated: bool = True,
    ) -> None:
        """
        Esegue il flusso di lavoro completo.

        Args:
            update_data: Se True, aggiorna i dati FPEDIA e FSTATS
            use_market_pricing: Se True, usa il pricing basato su mercato SOS (legacy)
            use_sos_calibrated: Se True, usa il pricing calibrato su SOS (raccomandato)
        """
        print("🚀 AVVIO WORKFLOW COMPLETO FANTACALCIO")
        print("=" * 60)

        # Step 1: Recupero dati (opzionale)
        if update_data:
            print("\n📥 STEP 1: Recupero dati FPEDIA e FSTATS")
            self._update_source_data()
        else:
            print("\n⏭️  STEP 1: Saltato (usando dati esistenti)")

        # Step 2: Creazione analisi individuali (interim)
        print("\n📊 STEP 2: Creazione analisi individuali")
        fpedia_file = self._create_fpedia_analysis()
        fstats_file = self._create_fstats_analysis()

        # Step 3: Merge delle analisi (interim)
        print("\n🔗 STEP 3: Merge delle analisi")
        merged_file = self._create_merged_analysis(fpedia_file, fstats_file)

        # Step 4: Calcolo prezzi finale (output)
        print("\n💰 STEP 4: Calcolo prezzi finale")
        if use_sos_calibrated:
            final_file = self._create_sos_calibrated_pricing(merged_file)
        elif use_market_pricing:
            final_file = self._create_market_based_pricing(merged_file)
        else:
            final_file = self._create_standalone_pricing(merged_file)

        print(f"\n✅ WORKFLOW COMPLETATO!")
        print(f"   📁 File finale: {final_file}")

        # Mostra statistiche finali
        self._show_final_stats(final_file)

    def _update_source_data(self) -> None:
        """Aggiorna i dati da FPEDIA e FSTATS."""
        try:
            print("   🔄 Recupero dati FPEDIA...")
            scrape_fpedia()

            print("   🔄 Recupero dati FSTATS...")
            fetch_FSTATS_data()

            print("   ✅ Dati aggiornati con successo")
        except Exception as e:
            print(f"   ❌ Errore nell'aggiornamento dati: {e}")
            raise

    def _create_fpedia_analysis(self) -> str:
        """Crea il file fpedia_analysis.xlsx nella cartella interim."""
        print("   📊 Processando dati FPEDIA...")

        # Carica e processa i dati FPEDIA
        # Recupera e processa i dati FPEDIA
        fpedia_csv = os.path.join(self.data_dir, "raw", "_giocatori.csv")
        if not os.path.exists(fpedia_csv):
            raise FileNotFoundError(f"File FPEDIA non trovato: {fpedia_csv}")

        df_fpedia = pd.read_csv(fpedia_csv)
        df_fpedia = process_fpedia_data(df_fpedia)

        # Applica l'analisi FPEDIA (semplificata)
        df_analyzed = self._calculate_fpedia_scores(df_fpedia)

        # Salva nella cartella interim
        output_file = os.path.join(self.interim_dir, "fpedia_analysis.xlsx")
        df_analyzed.to_excel(output_file, index=False)

        print(f"   ✅ File FPEDIA salvato: interim/fpedia_analysis.xlsx")
        return output_file

    def _create_fstats_analysis(self) -> str:
        """Crea il file FSTATS_analysis.xlsx nella cartella interim."""
        print("   📊 Processando dati FSTATS...")

        # Carica e processa i dati FSTATS
        # Recupera e processa i dati FSTATS
        fstats_csv = os.path.join(self.data_dir, "raw", "_players.csv")
        if not os.path.exists(fstats_csv):
            raise FileNotFoundError(f"File FSTATS non trovato: {fstats_csv}")

        df_fstats = pd.read_csv(fstats_csv, sep=";")
        df_fstats = process_FSTATS_data(df_fstats)

        # Applica l'analisi FSTATS (semplificata)
        df_analyzed = self._calculate_fstats_scores(df_fstats)

        # Salva nella cartella interim
        output_file = os.path.join(self.interim_dir, "FSTATS_analysis.xlsx")
        df_analyzed.to_excel(output_file, index=False)

        print(f"   ✅ File FSTATS salvato: interim/FSTATS_analysis.xlsx")
        return output_file

    def _create_merged_analysis(self, fpedia_file: str, fstats_file: str) -> str:
        """Merge delle due analisi in perfect_merged_analysis.xlsx."""
        print("   🔗 Merging analisi FPEDIA e FSTATS...")

        # Carica i file
        df_fpedia = pd.read_excel(fpedia_file)
        df_fstats = pd.read_excel(fstats_file)

        # Esegue un merge semplice sui nomi
        df_merged = self._merge_dataframes(df_fpedia, df_fstats)

        # Calcola score combinato
        df_merged = self._calculate_combined_scores(df_merged)

        # Salva nella cartella interim
        output_file = os.path.join(self.interim_dir, "perfect_merged_analysis.xlsx")
        df_merged.to_excel(output_file, index=False)

        print(f"   ✅ File merged salvato: interim/perfect_merged_analysis.xlsx")
        return output_file

    def _merge_dataframes(
        self, df_fpedia: pd.DataFrame, df_fstats: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge intelligente dei due dataframes con normalizzazione avanzata e fuzzy matching."""

        def normalize_name(name):
            """
            Normalizza un nome per il matching.
            Gestisce diversi formati: 'COGNOME NOME' -> 'nome cognome'
            """
            if pd.isna(name):
                return ""

            name = str(name).strip()

            # Rimuovi caratteri speciali, accenti e doppi spazi
            import re
            import unicodedata

            # Rimuovi accenti
            name = unicodedata.normalize("NFD", name)
            name = "".join(c for c in name if unicodedata.category(c) != "Mn")

            name = re.sub(r"[^\w\s]", " ", name)
            name = re.sub(r"\s+", " ", name).strip()

            # Converti in lowercase
            name = name.lower()

            # Se il nome sembra essere in formato "COGNOME NOME", prova a invertire
            parts = name.split()
            if len(parts) >= 2:
                # Se la prima parte è più lunga, probabilmente è il cognome
                if len(parts[0]) > len(parts[-1]):
                    # Inverti: COGNOME NOME -> NOME COGNOME
                    name = parts[-1] + " " + " ".join(parts[:-1])

            return name

        def fuzzy_match_names(fpedia_names, fstats_names, threshold=0.75):
            """Trova match fuzzy con strategie multiple e soglia più bassa."""
            import difflib

            matches = {}
            used_fstats = set()

            # Strategia 1: Match fuzzy standard (soglia ridotta)
            for fp_name in fpedia_names:
                if fp_name in matches:
                    continue

                available_fstats = [
                    name for name in fstats_names if name not in used_fstats
                ]
                best_matches = difflib.get_close_matches(
                    fp_name, available_fstats, n=1, cutoff=threshold
                )

                if best_matches:
                    fs_name = best_matches[0]
                    similarity = difflib.SequenceMatcher(None, fp_name, fs_name).ratio()
                    if similarity >= threshold:
                        matches[fp_name] = fs_name
                        used_fstats.add(fs_name)

            # Strategia 2: Match per inversione nome/cognome
            for fp_name in fpedia_names:
                if fp_name in matches:
                    continue

                fp_parts = fp_name.split()
                if len(fp_parts) < 2:
                    continue

                # Prova inversioni
                fp_inverted = f"{fp_parts[-1]} {' '.join(fp_parts[:-1])}"

                for fs_name in fstats_names:
                    if fs_name in used_fstats:
                        continue

                    # Match diretto con inversione
                    if fp_inverted == fs_name:
                        matches[fp_name] = fs_name
                        used_fstats.add(fs_name)
                        break

                    # Match fuzzy con inversione
                    similarity = difflib.SequenceMatcher(
                        None, fp_inverted, fs_name
                    ).ratio()
                    if similarity >= 0.8:
                        matches[fp_name] = fs_name
                        used_fstats.add(fs_name)
                        break

            # Strategia 3: Match per cognome + similarità nome
            for fp_name in fpedia_names:
                if fp_name in matches:
                    continue

                fp_parts = fp_name.split()
                if len(fp_parts) < 2:
                    continue

                fp_surname = fp_parts[-1]

                for fs_name in fstats_names:
                    if fs_name in used_fstats:
                        continue

                    fs_parts = fs_name.split()
                    if len(fs_parts) < 2:
                        continue

                    # Controlla se condividono il cognome (anche parzialmente)
                    surname_match = False
                    for fs_part in fs_parts:
                        if (
                            difflib.SequenceMatcher(None, fp_surname, fs_part).ratio()
                            > 0.85
                        ):
                            surname_match = True
                            break

                    if surname_match:
                        # Controlla similarità generale
                        overall_similarity = difflib.SequenceMatcher(
                            None, fp_name, fs_name
                        ).ratio()
                        if overall_similarity > 0.6:
                            matches[fp_name] = fs_name
                            used_fstats.add(fs_name)
                            break

            # Strategia 4: Match solo per cognome (molto permissivo)
            for fp_name in fpedia_names:
                if fp_name in matches:
                    continue

                fp_parts = fp_name.split()
                if len(fp_parts) < 2:
                    continue

                fp_surname = fp_parts[-1]

                for fs_name in fstats_names:
                    if fs_name in used_fstats:
                        continue

                    # Match esatto del cognome
                    if fp_surname in fs_name:
                        matches[fp_name] = fs_name
                        used_fstats.add(fs_name)
                        break

            return matches

        # Crea versioni normalizzate dei nomi
        df_fpedia_clean = df_fpedia.copy()
        df_fstats_clean = df_fstats.copy()

        df_fpedia_clean["Nome_Clean"] = df_fpedia_clean["Nome"].apply(normalize_name)
        df_fstats_clean["Nome_Clean"] = df_fstats_clean["Nome"].apply(normalize_name)

        # Match esatti
        fpedia_nomi = set(df_fpedia_clean["Nome_Clean"].dropna())
        fstats_nomi = set(df_fstats_clean["Nome_Clean"].dropna())
        exact_matches = fpedia_nomi & fstats_nomi

        # Match fuzzy per i rimanenti (soglia più bassa)
        only_fpedia = fpedia_nomi - exact_matches
        only_fstats = fstats_nomi - exact_matches

        fuzzy_matches = fuzzy_match_names(only_fpedia, only_fstats, threshold=0.75)

        print(f"   🔍 Debug matching avanzato:")
        print(
            f"   FPEDIA examples: {df_fpedia_clean[['Nome', 'Nome_Clean']].head(3).to_dict('records')}"
        )
        print(
            f"   FSTATS examples: {df_fstats_clean[['Nome', 'Nome_Clean']].head(3).to_dict('records')}"
        )
        print(f"   🎯 Match esatti: {len(exact_matches)}")
        print(f"   🎯 Match fuzzy trovati: {len(fuzzy_matches)}")

        # Mostra alcuni esempi di match fuzzy
        if fuzzy_matches:
            print(f"   💡 Esempi match fuzzy:")
            for i, (fp_clean, fs_clean) in enumerate(list(fuzzy_matches.items())[:3]):
                fp_orig = df_fpedia_clean[df_fpedia_clean["Nome_Clean"] == fp_clean][
                    "Nome"
                ].iloc[0]
                fs_orig = df_fstats_clean[df_fstats_clean["Nome_Clean"] == fs_clean][
                    "Nome"
                ].iloc[0]
                print(f'      • "{fp_orig}" ↔ "{fs_orig}"')

        # Applica i match fuzzy creando nomi unificati
        for fp_clean, fs_clean in fuzzy_matches.items():
            # Unifica i nomi usando quello FPEDIA come riferimento
            df_fstats_clean.loc[
                df_fstats_clean["Nome_Clean"] == fs_clean, "Nome_Clean"
            ] = fp_clean

        total_matches = len(exact_matches) + len(fuzzy_matches)
        print(f"   � Match totali dopo fuzzy: {total_matches}")

        # Merge principale sui nomi normalizzati (ora include fuzzy matches)
        df_merged = pd.merge(
            df_fpedia_clean,
            df_fstats_clean,
            on="Nome_Clean",
            how="outer",
            suffixes=("_FPEDIA", "_FSTATS"),
        )

        # Risolvi conflitti di base
        df_merged["Nome"] = df_merged["Nome_FPEDIA"].fillna(df_merged["Nome_FSTATS"])
        df_merged["Ruolo"] = df_merged["Ruolo_FPEDIA"].fillna(df_merged["Ruolo_FSTATS"])

        # Se esiste squadra in entrambe, prendi FPEDIA
        if "Squadra_FPEDIA" in df_merged.columns:
            df_merged["Squadra"] = df_merged["Squadra_FPEDIA"].fillna(
                df_merged.get("Squadra_FSTATS", "")
            )

        # Media delle convenienza dove disponibili
        conv_fpedia = df_merged.get("Convenienza_FPEDIA", 0)
        conv_fstats = df_merged.get("Convenienza_FSTATS", 0)
        df_merged["Convenienza"] = (conv_fpedia.fillna(0) + conv_fstats.fillna(0)) / 2

        # Pulisci colonne temporanee
        df_merged = df_merged.drop("Nome_Clean", axis=1, errors="ignore")

        # Filtra righe troppo vuote (solo per il file finale)
        df_merged = self._clean_empty_rows(df_merged)

        return df_merged

    def _clean_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rimuove righe con troppi valori mancanti per il file finale."""

        # Priorità: giocatori presenti in entrambe le fonti
        both_sources = (~df["Nome_FPEDIA"].isna()) & (~df["Nome_FSTATS"].isna())

        # Seconda priorità: giocatori con dati sufficienti da una fonte
        essential_cols = [
            col
            for col in df.columns
            if col not in ["Nome_FPEDIA", "Nome_FSTATS", "Nome", "Ruolo"]
            and not col.endswith("_FPEDIA")
            and not col.endswith("_FSTATS")
        ]

        if len(essential_cols) > 0:
            threshold = len(essential_cols) * 0.5  # Almeno 50% dati essenziali
            non_null_counts = df[essential_cols].notna().sum(axis=1)
            sufficient_data = non_null_counts >= threshold
        else:
            sufficient_data = pd.Series([True] * len(df))

        # Combina i criteri: preferisci giocatori matchati, poi quelli con dati sufficienti
        keep_rows = both_sources | sufficient_data

        before = len(df)
        df_clean = df[keep_rows].copy()
        after = len(df_clean)

        if before != after:
            print(
                f"   🧹 Rimosse {before - after} righe con dati insufficienti ({both_sources.sum()} matchati + {(sufficient_data & ~both_sources).sum()} con dati sufficienti)"
            )

        return df_clean

    def _calculate_fpedia_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcola i punteggi per i dati FPEDIA."""
        df_result = df.copy()

        # Converte le colonne numeriche e gestisce i valori non numerici
        def safe_numeric(col_name, default=0):
            if col_name in df_result.columns:
                return pd.to_numeric(df_result[col_name], errors="coerce").fillna(
                    default
                )
            return default

        # Calcolo semplificato di convenienza basato sui dati disponibili
        df_result["Convenienza"] = (
            safe_numeric("Punteggio") * 0.3
            + safe_numeric("Fantamedia anno 2024-2025") * 0.4
            + safe_numeric("Presenze 2024-2025") * 0.2
            + safe_numeric("Gol previsti") * 0.1
        )

        # Prezzo massimo consigliato semplificato
        df_result["Prezzo_Massimo_Consigliato"] = (df_result["Convenienza"] / 10).clip(
            1, 50
        )

        return df_result

    def _calculate_fstats_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcola i punteggi per i dati FSTATS."""
        df_result = df.copy()

        # Converte le colonne numeriche e gestisce i valori non numerici
        def safe_numeric(col_name, default=0):
            if col_name in df_result.columns:
                return pd.to_numeric(df_result[col_name], errors="coerce").fillna(
                    default
                )
            return default

        # Calcolo semplificato di convenienza basato sui dati FSTATS
        df_result["Convenienza"] = (
            safe_numeric("Media voto") * 0.4
            + safe_numeric("Gol fatti") * 0.3
            + safe_numeric("Presenze") * 0.2
            + safe_numeric("Assist") * 0.1
        )

        # Prezzo massimo consigliato semplificato
        df_result["Prezzo_Massimo_Consigliato"] = (df_result["Convenienza"] / 5).clip(
            1, 50
        )

        return df_result

    def _calculate_combined_scores(self, df_merged: pd.DataFrame) -> pd.DataFrame:
        """Calcola score combinati dalle due fonti."""

        # Performance Score semplice basato sulla convenienza
        df_merged["Performance_Score"] = (
            df_merged["Convenienza"].fillna(0) * 20
        ).round(2)

        # Prezzo consigliato finale (media dei due se disponibili)
        prezzo_fpedia = df_merged.get("Prezzo_Massimo_Consigliato_FPEDIA", 1)
        prezzo_fstats = df_merged.get("Prezzo_Massimo_Consigliato_FSTATS", 1)

        if (
            "Prezzo_Massimo_Consigliato_FPEDIA" in df_merged.columns
            and "Prezzo_Massimo_Consigliato_FSTATS" in df_merged.columns
        ):
            df_merged["Prezzo_Consigliato"] = (
                (prezzo_fpedia.fillna(1) + prezzo_fstats.fillna(1)) / 2
            ).round(1)
        elif "Prezzo_Massimo_Consigliato_FPEDIA" in df_merged.columns:
            df_merged["Prezzo_Consigliato"] = prezzo_fpedia.fillna(1)
        elif "Prezzo_Massimo_Consigliato_FSTATS" in df_merged.columns:
            df_merged["Prezzo_Consigliato"] = prezzo_fstats.fillna(1)
        else:
            df_merged["Prezzo_Consigliato"] = 1

        return df_merged

    def _create_sos_calibrated_pricing(self, merged_file: str) -> str:
        """Calcola i prezzi calibrati su SOS Fanta e salva in output."""
        print("   💰 Calcolo prezzi calibrati su SOS Fanta...")

        sos_file = os.path.join(self.data_dir, "SOS Fanta 2025_26.xlsx")
        if not os.path.exists(sos_file):
            print(f"   ⚠️  File SOS non trovato: {sos_file}")
            print("   🔄 Fallback a pricing autonomo...")
            return self._create_standalone_pricing(merged_file)

        try:
            from src.fantacalcio.analyzers.sos_calibrated_pricing import (
                SOSCalibratedPricingCalculator,
            )

            calculator = SOSCalibratedPricingCalculator()
            output_file = os.path.join(self.output_dir, "sos_calibrated_pricing.xlsx")

            # Processa i dati
            calculator.process_data(merged_file, sos_file, output_file)

            print(f"   ✅ File finale salvato: output/sos_calibrated_pricing.xlsx")
            return output_file

        except Exception as e:
            print(f"   ❌ Errore nel pricing calibrato: {e}")
            import traceback

            traceback.print_exc()
            return self._create_standalone_pricing(merged_file)

    def _create_market_based_pricing(self, merged_file: str) -> str:
        """Calcola i prezzi basati su mercato SOS e salva in output."""
        print("   💰 Calcolo prezzi basati su mercato SOS (legacy)...")

        sos_file = os.path.join(self.data_dir, "SOS Fanta 2025_26.xlsx")
        if not os.path.exists(sos_file):
            print(f"   ⚠️  File SOS non trovato: {sos_file}")
            print("   🔄 Fallback a pricing autonomo...")
            return self._create_standalone_pricing(merged_file)

        try:
            # Carica i dati merged
            df_merged = pd.read_excel(merged_file)

            # Carica i dati SOS
            df_sos = pd.read_excel(sos_file)

            # Merge con i dati SOS
            df_final = self._merge_with_sos_data(df_merged, df_sos)

            # Salva file finale
            output_file = os.path.join(self.output_dir, "final_market_analysis.xlsx")
            df_final.to_excel(output_file, index=False)

            print(f"   ✅ File finale salvato: output/final_market_analysis.xlsx")
            return output_file

        except Exception as e:
            print(f"   ❌ Errore nel pricing di mercato: {e}")
            return self._create_standalone_pricing(merged_file)

    def _create_standalone_pricing(self, merged_file: str) -> str:
        """Calcola i prezzi autonomi e salva in output."""
        print("   💰 Calcolo prezzi autonomi...")

        # Carica i dati merged
        df_merged = pd.read_excel(merged_file)

        # Usa semplicemente il prezzo consigliato già calcolato
        df_final = df_merged.copy()

        # Salva file finale
        output_file = os.path.join(self.output_dir, "final_standalone_analysis.xlsx")
        df_final.to_excel(output_file, index=False)

        print(f"   ✅ File finale salvato: output/final_standalone_analysis.xlsx")
        return output_file

    def _merge_with_sos_data(
        self, df_merged: pd.DataFrame, df_sos: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge con i dati SOS Fanta."""
        # Semplice merge per nome (assume colonna Nome in entrambi)
        df_final = pd.merge(
            df_merged, df_sos, on="Nome", how="left", suffixes=("", "_SOS")
        )

        # Se esiste una colonna prezzo SOS, usala come riferimento
        if "Prezzo_SOS" in df_final.columns:
            df_final["Prezzo_Mercato"] = df_final["Prezzo_SOS"]
            # Calcola differenza
            df_final["Differenza_SOS"] = (
                df_final["Prezzo_Consigliato"] - df_final["Prezzo_Mercato"]
            )

        return df_final

    def _show_final_stats(self, final_file: str) -> None:
        """Mostra statistiche finali del file generato."""
        try:
            df = pd.read_excel(final_file)

            total = len(df)

            # Determina quale colonna prezzo usare
            price_col = None
            if "Prezzo_Calibrato" in df.columns:
                price_col = "Prezzo_Calibrato"
            elif "Prezzo_Consigliato" in df.columns:
                price_col = "Prezzo_Consigliato"

            if price_col:
                avg_price = df[price_col].mean()
            else:
                avg_price = 0

            print(f"\n📈 STATISTICHE FINALI:")
            print(f"   👥 Giocatori analizzati: {total}")
            print(f"   💰 Prezzo medio: {avg_price:.1f}€")

            # Distribuzione per ruolo
            if "Ruolo" in df.columns:
                print(f"\n📊 DISTRIBUZIONE PER RUOLO:")
                for role, count in df["Ruolo"].value_counts().items():
                    percentage = (count / total) * 100
                    print(f"   • {role}: {count} ({percentage:.1f}%)")

            # Top 5 più costosi
            if price_col:
                print(f"\n🏆 TOP 5 PIÙ COSTOSI:")
                top_expensive = df.nlargest(5, price_col)
                for _, p in top_expensive.iterrows():
                    print(
                        f"   • {p.get('Nome', 'N/A')} ({p.get('Ruolo', 'N/A')}) - "
                        f"{p.get(price_col, 0):.1f}€"
                    )

        except Exception as e:
            print(f"   ⚠️  Impossibile mostrare statistiche: {e}")


def main():
    """Main entry point del workflow."""
    parser = argparse.ArgumentParser(
        description="Workflow Fantacalcio 2025-26",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
    python main_workflow.py                                  # Usa dati esistenti con pricing calibrato SOS (default)
    python main_workflow.py --update-data                    # Aggiorna dati e calcola prezzi calibrati SOS
    python main_workflow.py --no-sos-calibrated              # Usa pricing legacy basato su mercato
    python main_workflow.py --standalone                     # Usa solo pricing autonomo  
    python main_workflow.py --update-data --standalone       # Aggiorna dati e pricing autonomo
        """,
    )

    parser.add_argument(
        "--update-data", action="store_true", help="Aggiorna i dati FPEDIA e FSTATS"
    )

    parser.add_argument(
        "--no-market",
        action="store_true",
        help="Usa pricing autonomo invece di quello basato su mercato (legacy)",
    )

    parser.add_argument(
        "--no-sos-calibrated",
        action="store_true",
        help="Disabilita il pricing calibrato su SOS (usa legacy market pricing)",
    )

    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Usa solo pricing autonomo (nessun riferimento a SOS)",
    )

    parser.add_argument(
        "--data-dir", default="data", help="Directory contenente i dati (default: data)"
    )

    args = parser.parse_args()

    try:
        workflow = FantacalcioWorkflow(args.data_dir)

        # Determina la modalità di pricing
        use_sos_calibrated = not args.no_sos_calibrated and not args.standalone
        use_market_pricing = (
            not args.no_market and not args.standalone and not use_sos_calibrated
        )

        workflow.run_complete_workflow(
            update_data=args.update_data,
            use_market_pricing=use_market_pricing,
            use_sos_calibrated=use_sos_calibrated,
        )
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
