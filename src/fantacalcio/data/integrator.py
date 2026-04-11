"""
Data integrator: merge strutturato dei dati FSTATS e FPEDIA.

Strategia di matching:
1. Normalizzazione nomi (accenti, case, ordine parti)
2. Match esatto su nome+squadra normalizzati
3. Match esatto solo nome normalizzato
4. Fuzzy matching con SequenceMatcher (soglia 0.85)
5. Match cognome + squadra come fallback

Output: DataFrame unificato con prefisso colonne (fstats_ / fpedia_)
e colonne unificate per i campi comuni.
"""

import difflib
import re
import unicodedata
from typing import Optional

import pandas as pd
from loguru import logger

from ..utils import config


# ---------------------------------------------------------------------------
# Normalizzazione nomi
# ---------------------------------------------------------------------------

def normalize_name(name) -> str:
    """
    Normalizza un nome per il matching.

    - Rimuove accenti (NFD)
    - Uppercase
    - Rimuove caratteri non alfanumerici
    - Normalizza spazi
    """
    if pd.isna(name) or not name:
        return ""
    s = str(name).strip()

    # Rimuovi accenti
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")

    # Solo alfanumerici e spazi
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Ordina parti alfabeticamente (gestisce COGNOME NOME vs NOME COGNOME)
    parts = sorted(s.upper().split())
    return " ".join(parts)


def _name_parts(normalized: str) -> list[str]:
    """Ritorna le parti del nome ordinate (per matching indipendente dall'ordine)."""
    return sorted(normalized.split())


def _surname(normalized: str) -> str:
    """Estrae il cognome (prima parola, euristica per il formato italiano COGNOME NOME)."""
    parts = normalized.split()
    return parts[0] if parts else ""


# ---------------------------------------------------------------------------
# Matching engine
# ---------------------------------------------------------------------------

def _build_match_map(
    fpedia_df: pd.DataFrame,
    fstats_df: pd.DataFrame,
) -> dict[int, int]:
    """
    Costruisce una mappa fpedia_idx -> fstats_idx usando strategie incrementali.

    Ritorna un dict che mappa l'indice di riga FPEDIA all'indice di riga FSTATS matchato.
    """
    # Prepara lookup
    fpedia_keys = fpedia_df[["_norm_name", "_norm_squadra"]].copy()
    fstats_keys = fstats_df[["_norm_name", "_norm_squadra"]].copy()

    matched: dict[int, int] = {}
    used_fstats: set[int] = set()

    # --- Strategia 1: match esatto nome + squadra ---
    fstats_name_team = {}
    for idx, row in fstats_keys.iterrows():
        key = (row["_norm_name"], row["_norm_squadra"])
        if key not in fstats_name_team:
            fstats_name_team[key] = idx

    for fp_idx, fp_row in fpedia_keys.iterrows():
        key = (fp_row["_norm_name"], fp_row["_norm_squadra"])
        fs_idx = fstats_name_team.get(key)
        if fs_idx is not None and fs_idx not in used_fstats:
            matched[fp_idx] = fs_idx
            used_fstats.add(fs_idx)

    logger.info(f"Matching strategia 1 (nome+squadra esatto): {len(matched)}")

    # --- Strategia 2: match esatto solo nome ---
    fstats_name_only = {}
    for idx, row in fstats_keys.iterrows():
        if idx in used_fstats:
            continue
        name = row["_norm_name"]
        if name and name not in fstats_name_only:
            fstats_name_only[name] = idx

    for fp_idx, fp_row in fpedia_keys.iterrows():
        if fp_idx in matched:
            continue
        name = fp_row["_norm_name"]
        if not name:
            continue
        fs_idx = fstats_name_only.get(name)
        if fs_idx is not None and fs_idx not in used_fstats:
            matched[fp_idx] = fs_idx
            used_fstats.add(fs_idx)

    logger.info(f"Matching strategia 2 (nome esatto): {len(matched)} totali")

    # --- Strategia 3: match con parti nome ordinate (gestisce inversione cognome/nome) ---
    fstats_sorted_parts = {}
    for idx, row in fstats_keys.iterrows():
        if idx in used_fstats:
            continue
        parts_key = tuple(_name_parts(row["_norm_name"]))
        if parts_key and parts_key not in fstats_sorted_parts:
            fstats_sorted_parts[parts_key] = idx

    for fp_idx, fp_row in fpedia_keys.iterrows():
        if fp_idx in matched:
            continue
        parts_key = tuple(_name_parts(fp_row["_norm_name"]))
        if not parts_key:
            continue
        fs_idx = fstats_sorted_parts.get(parts_key)
        if fs_idx is not None and fs_idx not in used_fstats:
            matched[fp_idx] = fs_idx
            used_fstats.add(fs_idx)

    logger.info(f"Matching strategia 3 (parti ordinate): {len(matched)} totali")

    # --- Strategia 4: fuzzy matching (soglia 0.85) ---
    remaining_fpedia = {
        fp_idx: fp_row["_norm_name"]
        for fp_idx, fp_row in fpedia_keys.iterrows()
        if fp_idx not in matched and fp_row["_norm_name"]
    }
    remaining_fstats = {
        fs_idx: fs_row["_norm_name"]
        for fs_idx, fs_row in fstats_keys.iterrows()
        if fs_idx not in used_fstats and fs_row["_norm_name"]
    }

    if remaining_fpedia and remaining_fstats:
        fstats_names_list = list(remaining_fstats.values())
        fstats_idx_list = list(remaining_fstats.keys())

        for fp_idx, fp_name in remaining_fpedia.items():
            best = difflib.get_close_matches(fp_name, fstats_names_list, n=1, cutoff=0.80)
            if best:
                pos = fstats_names_list.index(best[0])
                fs_idx = fstats_idx_list[pos]
                if fs_idx not in used_fstats:
                    matched[fp_idx] = fs_idx
                    used_fstats.add(fs_idx)
                    # Rimuovi dalle liste per efficienza
                    fstats_names_list.pop(pos)
                    fstats_idx_list.pop(pos)

    logger.info(f"Matching strategia 4 (fuzzy 0.80): {len(matched)} totali")

    # --- Strategia 5: subset di parti nome + stessa squadra ---
    # FPEDIA ha spesso "COGNOME NOME" (2 parti), FSTATS può avere nomi composti
    # (es. "Wesley Vinicius Franca Lima"). Se tutte le parti FPEDIA sono contenute
    # in FSTATS e la squadra è la stessa, è un match.
    remaining_fpedia_sub = {
        fp_idx: (set(fpedia_keys.loc[fp_idx, "_norm_name"].split()), fpedia_keys.loc[fp_idx, "_norm_squadra"])
        for fp_idx in fpedia_keys.index
        if fp_idx not in matched and fpedia_keys.loc[fp_idx, "_norm_name"]
    }
    remaining_fstats_sub = {
        fs_idx: (set(fstats_keys.loc[fs_idx, "_norm_name"].split()), fstats_keys.loc[fs_idx, "_norm_squadra"])
        for fs_idx in fstats_keys.index
        if fs_idx not in used_fstats and fstats_keys.loc[fs_idx, "_norm_name"]
    }

    for fp_idx, (fp_parts, fp_team) in remaining_fpedia_sub.items():
        if len(fp_parts) < 2 or not fp_team:
            continue
        for fs_idx, (fs_parts, fs_team) in remaining_fstats_sub.items():
            if fs_idx in used_fstats:
                continue
            if fp_team != fs_team:
                continue
            # FPEDIA parti sono sottoinsieme di FSTATS (o viceversa)
            if fp_parts.issubset(fs_parts) or fs_parts.issubset(fp_parts):
                matched[fp_idx] = fs_idx
                used_fstats.add(fs_idx)
                break

    logger.info(f"Matching strategia 5 (subset parti+squadra): {len(matched)} totali")

    # --- Strategia 6: cognome + squadra ---
    remaining_fpedia_2 = {
        fp_idx: (fpedia_keys.loc[fp_idx, "_norm_name"], fpedia_keys.loc[fp_idx, "_norm_squadra"])
        for fp_idx in fpedia_keys.index
        if fp_idx not in matched
    }
    remaining_fstats_2 = {
        fs_idx: (fstats_keys.loc[fs_idx, "_norm_name"], fstats_keys.loc[fs_idx, "_norm_squadra"])
        for fs_idx in fstats_keys.index
        if fs_idx not in used_fstats
    }

    for fp_idx, (fp_name, fp_team) in remaining_fpedia_2.items():
        fp_surname = _surname(fp_name)
        if not fp_surname or len(fp_surname) < 3:
            continue
        for fs_idx, (fs_name, fs_team) in remaining_fstats_2.items():
            if fs_idx in used_fstats:
                continue
            fs_surname = _surname(fs_name)
            # Cognome deve matchare e squadra uguale
            if fp_surname == fs_surname and fp_team and fp_team == fs_team:
                matched[fp_idx] = fs_idx
                used_fstats.add(fs_idx)
                break

    logger.info(f"Matching strategia 6 (cognome+squadra): {len(matched)} totali")

    return matched


# ---------------------------------------------------------------------------
# Integrazione
# ---------------------------------------------------------------------------

def integrate(
    df_fstats: pd.DataFrame,
    df_fpedia: pd.DataFrame,
) -> pd.DataFrame:
    """
    Integra i dati FSTATS e FPEDIA in un unico DataFrame.

    Args:
        df_fstats: DataFrame FSTATS già processato (da process_fstats)
        df_fpedia: DataFrame FPEDIA già processato (da process_fpedia)

    Returns:
        DataFrame unificato con colonne:
        - Campi comuni unificati (Nome, Ruolo, Squadra)
        - Colonne FSTATS con prefisso fstats_
        - Colonne FPEDIA con prefisso fpedia_
        - Flag _source: "both", "fstats_only", "fpedia_only"
    """
    if df_fstats.empty and df_fpedia.empty:
        logger.error("Entrambi i DataFrame sono vuoti.")
        return pd.DataFrame()

    if df_fstats.empty:
        logger.warning("Solo dati FPEDIA disponibili.")
        result = df_fpedia.copy()
        result["_source"] = "fpedia_only"
        return result

    if df_fpedia.empty:
        logger.warning("Solo dati FSTATS disponibili.")
        result = df_fstats.copy()
        result["_source"] = "fstats_only"
        return result

    # Prepara colonne di matching
    df_fstats = df_fstats.copy()
    df_fpedia = df_fpedia.copy()

    df_fstats["_norm_name"] = df_fstats["Nome"].apply(normalize_name)
    df_fpedia["_norm_name"] = df_fpedia["Nome"].apply(normalize_name)

    df_fstats["_norm_squadra"] = df_fstats.get("Squadra", pd.Series("", index=df_fstats.index)).apply(normalize_name)
    df_fpedia["_norm_squadra"] = df_fpedia.get("Squadra", pd.Series("", index=df_fpedia.index)).apply(normalize_name)

    # Costruisci mappa di match
    match_map = _build_match_map(df_fpedia, df_fstats)

    logger.info(
        f"Match totali: {len(match_map)} / "
        f"FPEDIA: {len(df_fpedia)}, FSTATS: {len(df_fstats)}"
    )

    # Prefissa colonne (escluse quelle di matching)
    exclude_cols = {"Nome", "Ruolo", "Squadra", "_norm_name", "_norm_squadra"}

    fstats_cols_map = {
        c: f"fstats_{c}" for c in df_fstats.columns if c not in exclude_cols
    }
    fpedia_cols_map = {
        c: f"fpedia_{c}" for c in df_fpedia.columns if c not in exclude_cols
    }

    df_fstats_prefixed = df_fstats.rename(columns=fstats_cols_map)
    df_fpedia_prefixed = df_fpedia.rename(columns=fpedia_cols_map)

    # Costruisci righe unificate
    rows = []
    matched_fstats = set()

    for fp_idx, fs_idx in match_map.items():
        matched_fstats.add(fs_idx)
        row = {}
        # Campi unificati: preferenza FPEDIA per nome, FSTATS per squadra
        fp = df_fpedia.loc[fp_idx]
        fs = df_fstats.loc[fs_idx]
        row["Nome"] = fp["Nome"] if pd.notna(fp.get("Nome")) else fs.get("Nome", "")
        row["Ruolo"] = fp.get("Ruolo", "") or fs.get("Ruolo", "")
        row["Squadra"] = fs.get("Squadra", "") or fp.get("Squadra", "")
        row["_source"] = "both"

        # Aggiungi tutte le colonne FSTATS prefissate
        for orig, pref in fstats_cols_map.items():
            row[pref] = df_fstats_prefixed.loc[fs_idx, pref] if pref in df_fstats_prefixed.columns else None

        # Aggiungi tutte le colonne FPEDIA prefissate
        for orig, pref in fpedia_cols_map.items():
            row[pref] = df_fpedia_prefixed.loc[fp_idx, pref] if pref in df_fpedia_prefixed.columns else None

        rows.append(row)

    # FPEDIA-only
    for fp_idx in df_fpedia.index:
        if fp_idx in match_map:
            continue
        fp = df_fpedia.loc[fp_idx]
        row = {
            "Nome": fp.get("Nome", ""),
            "Ruolo": fp.get("Ruolo", ""),
            "Squadra": fp.get("Squadra", ""),
            "_source": "fpedia_only",
        }
        for orig, pref in fpedia_cols_map.items():
            row[pref] = df_fpedia_prefixed.loc[fp_idx, pref] if pref in df_fpedia_prefixed.columns else None
        rows.append(row)

    # FSTATS-only
    for fs_idx in df_fstats.index:
        if fs_idx in matched_fstats:
            continue
        fs = df_fstats.loc[fs_idx]
        row = {
            "Nome": fs.get("Nome", ""),
            "Ruolo": fs.get("Ruolo", ""),
            "Squadra": fs.get("Squadra", ""),
            "_source": "fstats_only",
        }
        for orig, pref in fstats_cols_map.items():
            row[pref] = df_fstats_prefixed.loc[fs_idx, pref] if pref in df_fstats_prefixed.columns else None
        rows.append(row)

    result = pd.DataFrame(rows)

    # Statistiche
    both = (result["_source"] == "both").sum()
    fpedia_only = (result["_source"] == "fpedia_only").sum()
    fstats_only = (result["_source"] == "fstats_only").sum()
    logger.info(
        f"Integrazione completata: {len(result)} giocatori "
        f"(both={both}, fpedia_only={fpedia_only}, fstats_only={fstats_only})"
    )

    return result
