# convenienza_calculator.py
import pandas as pd
import ast
from loguru import logger
from config import ANNO_CORRENTE

# --- Funzioni per FPEDIA ---

skills_mapping = {
    "Fuoriclasse": 1,
    "Titolare": 3,
    "Buona Media": 2,
    "Goleador": 4,
    "Assistman": 2,
    "Piazzati": 2,
    "Rigorista": 5,
    "Giovane talento": 2,
    "Panchinaro": -4,
    "Falloso": -2,
    "Outsider": 2,
}


def calcola_convenienza_fpedia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola due indici di convenienza per i dati di FPEDIA:
    1. 'Convenienza': basata sulle performance stagionali (presenze, fantamedia).
    2. 'Convenienza Potenziale': basata sul valore intrinseco del giocatore (Punteggio, Skills),
       utile soprattutto a inizio campionato o con poche presenze.
    """
    if df.empty:
        logger.warning("DataFrame FPEDIA è vuoto. Calcolo saltato.")
        return df

    # --- Calcolo Convenienza (basata su presenze) ---
    res_convenienza = []
    df_calc = df.copy()

    numeric_cols = [
        f"Fantamedia anno {ANNO_CORRENTE-2}-{ANNO_CORRENTE-1}",
        "Partite giocate",
        f"Fantamedia anno {ANNO_CORRENTE-1}-{ANNO_CORRENTE}",
        "Presenze campionato corrente",
        "Punteggio",
        "Buon investimento",
        "Resistenza infortuni",
    ]
    for col in numeric_cols:
        df_calc[col] = pd.to_numeric(df_calc[col], errors="coerce").fillna(0)

    giocatemax = df_calc["Presenze campionato corrente"].max()
    if giocatemax == 0:
        giocatemax = 1

    for _, row in df_calc.iterrows():
        appetibilita = 0
        fantamedia_prec = row.get(
            f"Fantamedia anno {ANNO_CORRENTE-2}-{ANNO_CORRENTE-1}", 0
        )
        partite_prec = row.get("Partite giocate", 0)
        fantamedia_corr = row.get(
            f"Fantamedia anno {ANNO_CORRENTE-1}-{ANNO_CORRENTE}", 0
        )
        partite_corr = row.get("Presenze campionato corrente", 0)
        punteggio = row.get("Punteggio", 1)

        if partite_prec > 0:
            appetibilita += fantamedia_prec * (partite_prec / 38) * 0.20
        if partite_corr > 5:
            appetibilita += fantamedia_corr * (partite_corr / giocatemax) * 0.80
        elif partite_prec > 0:
            appetibilita = fantamedia_prec * (partite_prec / 38)

        appetibilita = appetibilita * punteggio * 0.30
        pt = punteggio if punteggio != 0 else 1
        appetibilita = (appetibilita / pt) * 100 / 40

        try:
            skills_list = ast.literal_eval(row.get("Skills", "[]"))
            plus = sum(skills_mapping.get(skill, 0) for skill in skills_list)
            appetibilita += plus
        except (ValueError, SyntaxError):
            pass

        if row.get("Nuovo acquisto", False):
            appetibilita -= 2
        if row.get("Buon investimento", 0) == 60:
            appetibilita += 3
        if row.get("Consigliato prossima giornata", False):
            appetibilita += 1
        if row.get("Trend", "") == "UP":
            appetibilita += 2
        if row.get("Infortunato", False):
            appetibilita -= 1
        if row.get("Resistenza infortuni", 0) > 60:
            appetibilita += 4
        elif row.get("Resistenza infortuni", 0) == 60:
            appetibilita += 2

        res_convenienza.append(appetibilita)

    df["Convenienza"] = res_convenienza
    logger.debug("Indice 'Convenienza' calcolato per FPEDIA.")

    # --- Calcolo Convenienza Potenziale (indipendente da presenze) ---
    res_potenziale = []
    for _, row in df_calc.iterrows():
        potenziale = row.get("Punteggio", 0)
        try:
            skills_list = ast.literal_eval(row.get("Skills", "[]"))
            plus = sum(skills_mapping.get(skill, 0) for skill in skills_list)
            potenziale += plus * 2  # Diamo più peso alle skill nel potenziale
        except (ValueError, SyntaxError):
            pass
        res_potenziale.append(potenziale)

    df["Convenienza Potenziale"] = res_potenziale
    logger.debug("Indice 'Convenienza Potenziale' calcolato per FPEDIA.")

    return df


# --- Funzioni per FSTATS ---


def calcola_convenienza_FSTATS(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola due indici di convenienza per i dati di FSTATS:
    1. 'Convenienza': basata sulle performance stagionali (presenze, fantamedia).
    2. 'Convenienza Potenziale': basata sul valore intrinseco (fantacalcioFantaindex) e potenziale
       statistico (xG, xA), utile soprattutto a inizio campionato.
    """
    if df.empty:
        logger.warning("DataFrame FSTATS è vuoto. Calcolo saltato.")
        return df

    df_calc = df.copy()
    numeric_cols = [
        "goals",
        "assists",
        "yellowCards",
        "redCards",
        "xgFromOpenPlays",
        "xA",
        "presences",
        "fanta_avg",
        "fantacalcioFantaindex",
    ]
    for col in numeric_cols:
        df_calc[col] = pd.to_numeric(df_calc[col], errors="coerce").fillna(0)

    # --- Calcolo Convenienza (basata su presenze) ---
    df_con_presenze = df_calc[df_calc["presences"] > 0].reset_index(drop=True)
    if not df_con_presenze.empty:
        bonus_score = (df_con_presenze["goals"] * 3) + (df_con_presenze["assists"] * 1)
        malus_score = (df_con_presenze["yellowCards"] * 0.5) + (
            df_con_presenze["redCards"] * 1
        )
        bonus_per_presence = bonus_score / df_con_presenze["presences"]
        malus_per_presence = malus_score / df_con_presenze["presences"]
        potential_score = (
            df_con_presenze["xgFromOpenPlays"] + df_con_presenze["xA"]
        ) / df_con_presenze["presences"]

        convenienza = (
            df_con_presenze["fanta_avg"] * 0.6
            + bonus_per_presence * 0.25
            + potential_score * 0.15
            - malus_per_presence * 0.2
        )
        df_con_presenze["Convenienza"] = (
            (convenienza / convenienza.max()) * 100 if not convenienza.empty else 0
        )
        df = df.merge(df_con_presenze[["Nome", "Convenienza"]], on="Nome", how="left")
        logger.debug("Indice 'Convenienza' calcolato per FSTATS.")
    else:
        df["Convenienza"] = 0
        logger.warning(
            "Nessun giocatore con presenze in FSTATS. 'Convenienza' impostata a 0."
        )

    # --- Calcolo Convenienza Potenziale (indipendente da presenze) ---
    potential_stats = (
        df_calc["xgFromOpenPlays"] + df_calc["xA"]
    ) * 2  # Pondera il potenziale xG/xA
    potenziale = df_calc["fantacalcioFantaindex"] + potential_stats

    df_calc["Convenienza Potenziale"] = (
        (potenziale / potenziale.max()) * 100 if not potenziale.empty else 0
    )
    df = df.merge(df_calc[["Nome", "Convenienza Potenziale"]], on="Nome", how="left")
    logger.debug("Indice 'Convenienza Potenziale' calcolato per FSTATS.")

    df.fillna({"Convenienza": 0, "Convenienza Potenziale": 0}, inplace=True)
    return df


# --- Funzione parametrica per calcolare il prezzo massimo consigliato ---

def calcola_prezzo_massimo_consigliato(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sistema parametrico di calcolo del prezzo massimo consigliato.
    Usa le fasce definite in config.py per distribuire automaticamente
    i giocatori nei budget slots basandosi sui punteggi calcolati.
    """
    # Importa i valori delle fasce dal config in modo parametrico
    from config import (POR_1, POR_2, POR_3, 
                       DIF_1, DIF_2, DIF_3, DIF_4, DIF_5, DIF_6, DIF_7, DIF_8,
                       CEN_1, CEN_2, CEN_3, CEN_4, CEN_5, CEN_6, CEN_7, CEN_8,
                       ATT_1, ATT_2, ATT_3, ATT_4, ATT_5, ATT_6)
    
    if df.empty:
        logger.warning("DataFrame è vuoto. Calcolo prezzo massimo saltato.")
        return df

    # Sistema parametrico: crea automaticamente le fasce per ogni ruolo
    fasce_parametriche = {
        'P': [POR_1, POR_2, POR_3],
        'POR': [POR_1, POR_2, POR_3],
        'D': [DIF_1, DIF_2, DIF_3, DIF_4, DIF_5, DIF_6, DIF_7, DIF_8],
        'DIF': [DIF_1, DIF_2, DIF_3, DIF_4, DIF_5, DIF_6, DIF_7, DIF_8],
        'C': [CEN_1, CEN_2, CEN_3, CEN_4, CEN_5, CEN_6, CEN_7, CEN_8],
        'CEN': [CEN_1, CEN_2, CEN_3, CEN_4, CEN_5, CEN_6, CEN_7, CEN_8],
        'A': [ATT_1, ATT_2, ATT_3, ATT_4, ATT_5, ATT_6],
        'ATT': [ATT_1, ATT_2, ATT_3, ATT_4, ATT_5, ATT_6]
    }
    
    # Determina se stiamo usando FPEDIA o FSTATS basandoci sulle colonne
    is_fpedia = 'Punteggio' in df.columns
    is_fstats = 'fantacalcioFantaindex' in df.columns
    
    # Lista per contenere i prezzi calcolati
    risultati_finali = []
    
    # Raggruppa per ruolo e distribuisce nelle fasce parametriche
    for ruolo in df['Ruolo'].unique():
        if pd.isna(ruolo):
            continue
            
        # Filtra giocatori per ruolo
        df_ruolo = df[df['Ruolo'] == ruolo].copy()
        
        if ruolo not in fasce_parametriche:
            logger.warning(f"Ruolo {ruolo} non trovato nella mappatura. Saltato.")
            for idx in df_ruolo.index:
                risultati_finali.append((idx, 1))  # Default minimo
            continue
        
        fasce_ruolo = fasce_parametriche[ruolo]
        if not fasce_ruolo:
            logger.warning(f"Nessun valore fascia per ruolo {ruolo}. Saltato.")
            for idx in df_ruolo.index:
                risultati_finali.append((idx, 1))
            continue
        
        num_fasce = len(fasce_ruolo)
        
        # === CALCOLO SCORE COMPLESSIVO USANDO TUTTE LE STATISTICHE ===
        if is_fpedia:
            score_complessivo = calcola_score_fpedia(df_ruolo, ruolo)
        elif is_fstats:
            score_complessivo = calcola_score_fstats(df_ruolo, ruolo)
        else:
            # Fallback alla convenienza potenziale
            if 'Convenienza Potenziale' in df_ruolo.columns:
                score_complessivo = df_ruolo['Convenienza Potenziale'].fillna(0)
            else:
                score_complessivo = pd.Series([1] * len(df_ruolo), index=df_ruolo.index)
        
        # Ordina per score complessivo
        df_ruolo['Score_Complessivo'] = score_complessivo
        df_ruolo = df_ruolo.sort_values('Score_Complessivo', ascending=False)
        
        if score_complessivo.max() == 0:
            # Se tutti hanno score 0, assegna fascia più bassa
            for idx in df_ruolo.index:
                risultati_finali.append((idx, fasce_ruolo[-1]))  # Ultima fascia (più bassa)
        else:
            # === DISTRIBUZIONE PARAMETRICA NELLE FASCE ===
            num_giocatori = len(df_ruolo)
            
            # Distribuzione più equilibrata basata sul score effettivo
            # Invece di logaritmica rigida, usa percentili degli score
            distribuzione_fasce = []
            
            # Calcola percentili per distribuire meglio i giocatori
            scores_sorted = sorted(score_complessivo, reverse=True)
            
            # Distribuzione meno aggressiva per ogni ruolo
            if ruolo in ['A', 'ATT']:
                # Per attaccanti: distribuzione molto più equilibrata
                percentuali_cumulative = [0.04, 0.10, 0.20, 0.35, 0.65, 1.0]  # 4%, 6%, 10%, 15%, 30%, 35%
            elif ruolo in ['C', 'CEN']:
                # Per centrocampisti: distribuzione MOLTO selettiva (solo elite a 50)
                percentuali_cumulative = [0.03, 0.12, 0.25, 0.40, 0.58, 0.72, 0.83, 1.0]  # 3%, 9%, 13%, 15%, 18%, 14%, 11%, 17%
            elif ruolo in ['D', 'DIF']:
                # Per difensori: distribuzione simile ai centrocampisti
                percentuali_cumulative = [0.06, 0.15, 0.28, 0.43, 0.60, 0.75, 0.88, 1.0]  # 6%, 9%, 13%, 15%, 17%, 15%, 13%, 12%
            else:  # Portieri
                percentuali_cumulative = [0.15, 0.40, 1.0]  # 15%, 25%, 60%
            
            # Calcola numero giocatori per fascia
            prev_percentuale = 0
            for i, percentuale_cumulativa in enumerate(percentuali_cumulative):
                if i == len(percentuali_cumulative) - 1:  # Ultima fascia: tutti i rimanenti
                    distribuzione_fasce.append(num_giocatori - sum(distribuzione_fasce))
                else:
                    n_giocatori_fascia = max(1, int(num_giocatori * (percentuale_cumulativa - prev_percentuale)))
                    distribuzione_fasce.append(n_giocatori_fascia)
                    prev_percentuale = percentuale_cumulativa
            
            # Assegna i prezzi basandosi sulla distribuzione
            indice_giocatore = 0
            for fascia_idx, n_giocatori_fascia in enumerate(distribuzione_fasce):
                prezzo_fascia = fasce_ruolo[fascia_idx]
                
                # Assegna il prezzo della fascia ai giocatori
                for _ in range(n_giocatori_fascia):
                    if indice_giocatore < num_giocatori:
                        idx = df_ruolo.iloc[indice_giocatore].name
                        risultati_finali.append((idx, prezzo_fascia))
                        indice_giocatore += 1
            
            # Verifica che tutti i giocatori abbiano un prezzo
            while indice_giocatore < num_giocatori:
                idx = df_ruolo.iloc[indice_giocatore].name
                risultati_finali.append((idx, fasce_ruolo[-1]))  # Ultima fascia
                indice_giocatore += 1
    
    # Crea un DataFrame con i prezzi calcolati
    prezzi_df = pd.DataFrame(risultati_finali, columns=['index', 'Prezzo Massimo Consigliato'])
    prezzi_df.set_index('index', inplace=True)
    
    # Aggiungi la colonna al DataFrame originale
    df['Prezzo Massimo Consigliato'] = 0
    df.loc[prezzi_df.index, 'Prezzo Massimo Consigliato'] = prezzi_df['Prezzo Massimo Consigliato']
    
    logger.info("Sistema parametrico completato: prezzi distribuiti automaticamente nelle fasce config.py")
    return df


def calcola_score_fpedia(df_ruolo: pd.DataFrame, ruolo: str) -> pd.Series:
    """
    Calcola uno score complessivo per FPEDIA utilizzando tutti i parametri disponibili.
    """
    score = pd.Series(0.0, index=df_ruolo.index)
    
    # PESO RUOLO
    peso_ruolo = {'ATT': 1.2, 'A': 1.2, 'CEN': 1.0, 'C': 1.0, 'DIF': 0.9, 'D': 0.9, 'POR': 0.8, 'P': 0.8}.get(ruolo, 1.0)
    
    # 1. FANTAMEDIA (peso 50%)
    if 'Fantamedia anno 2024-2025' in df_ruolo.columns:
        fm_attuale = df_ruolo['Fantamedia anno 2024-2025'].fillna(0)
        fm_norm = ((fm_attuale - 4.5) / 2.5).clip(0, 1)
        score += fm_norm * 50
    
    # 2. PRESENZE/AFFIDABILITÀ (peso 35%)
    if 'Presenze campionato corrente' in df_ruolo.columns:
        presenze = df_ruolo['Presenze campionato corrente'].fillna(0)
        
        def calcola_affidabilita(presenze):
            if presenze >= 30:
                return 1.0
            elif presenze >= 25:
                return 0.8
            elif presenze >= 20:
                return 0.6
            elif presenze >= 15:
                return 0.4
            elif presenze >= 10:
                return 0.25
            elif presenze >= 5:
                return 0.1
            else:
                return 0.02
        
        affidabilita = presenze.apply(calcola_affidabilita)
        score += affidabilita * 35
    
    # 3. PUNTEGGIO FPEDIA (peso 10%)
    if 'Punteggio' in df_ruolo.columns:
        punteggio_norm = (df_ruolo['Punteggio'].fillna(50) - 30) / 70
        score += punteggio_norm.clip(0, 1) * 10
    
    # 4. SKILLS (peso 3%)
    if 'Skills' in df_ruolo.columns:
        skills_score = pd.Series(0.0, index=df_ruolo.index)
        skills_mapping_realistico = {
            "Rigorista": 8,
            "Goleador": 6,
            "Titolare": 4,
            "Assistman": 3,
            "Piazzati": 2,
            "Panchinaro": -10,
            "Falloso": -5,
            "Fuoriclasse": 2,
            "Buona Media": 1,
        }
        for idx, row in df_ruolo.iterrows():
            try:
                skills_list = ast.literal_eval(row.get("Skills", "[]"))
                skill_bonus = sum(skills_mapping_realistico.get(skill, 0) for skill in skills_list)
                skills_score[idx] = skill_bonus
            except:
                skills_score[idx] = 0
        skills_norm = (skills_score + 10) / 20
        score += skills_norm.clip(0, 1) * 3
    
    # 5. BONUS MINORI (peso 2%)
    bonus_minori = pd.Series(0.0, index=df_ruolo.index)
    if 'Resistenza infortuni' in df_ruolo.columns:
        resistenza = (df_ruolo['Resistenza infortuni'].fillna(50) - 50) / 50
        bonus_minori += resistenza.clip(0, 1) * 1
    if 'Buon investimento' in df_ruolo.columns:
        investimento = (df_ruolo['Buon investimento'].fillna(0) - 50) / 50
        bonus_minori += investimento.clip(0, 1) * 1
    score += bonus_minori
    
    # Applica il moltiplicatore ruolo
    score = score * peso_ruolo
    
    return score.clip(0, 100)


def calcola_score_fstats(df_ruolo: pd.DataFrame, ruolo: str) -> pd.Series:
    """
    Calcola uno score complessivo per FSTATS utilizzando tutti i parametri disponibili.
    """
    score = pd.Series(0.0, index=df_ruolo.index)
    
    # PESO RUOLO
    peso_ruolo = {'ATT': 1.0, 'A': 1.0, 'CEN': 1.0, 'C': 1.0, 'DIF': 0.85, 'D': 0.85, 'POR': 0.8, 'P': 0.8}.get(ruolo, 1.0)
    
    # 1. FANTAMEDIA (peso variabile per ruolo)
    peso_fantamedia = 30 if ruolo in ['ATT', 'A'] else 45
    if 'fanta_avg' in df_ruolo.columns:
        fanta_avg = df_ruolo['fanta_avg'].fillna(0)
        fanta_norm = ((fanta_avg - 4.5) / 3.0).clip(0, 1)
        score += fanta_norm * peso_fantamedia
    
    # 2. AFFIDABILITÀ E UTILIZZO (peso variabile per ruolo)
    peso_utilizzo = 25 if ruolo in ['ATT', 'A'] else 30
    utilizzo_score = pd.Series(0.0, index=df_ruolo.index)
    
    # 2a. Presenze
    peso_presenze = 15 if ruolo in ['ATT', 'A'] else 20
    if 'presences' in df_ruolo.columns:
        presenze = df_ruolo['presences'].fillna(0)
        
        def calcola_affidabilita(presenze):
            if ruolo in ['C', 'CEN']:
                # Per centrocampisti: meno penalizzante sulle presenze
                if presenze >= 30:
                    return 1.0
                elif presenze >= 25:
                    return 0.85
                elif presenze >= 20:
                    return 0.7
                elif presenze >= 15:
                    return 0.55  # Meno penalizzante
                elif presenze >= 10:
                    return 0.4   # Meno penalizzante
                elif presenze >= 5:
                    return 0.25  # Meno penalizzante
                else:
                    return 0.1
            else:
                # Per altri ruoli: sistema originale
                if presenze >= 30:
                    return 1.0
                elif presenze >= 25:
                    return 0.75
                elif presenze >= 20:
                    return 0.5
                elif presenze >= 15:
                    return 0.3
                elif presenze >= 10:
                    return 0.15
                elif presenze >= 5:
                    return 0.05
                else:
                    return 0.01
        
        affidabilita = presenze.apply(calcola_affidabilita)
        utilizzo_score += affidabilita * peso_presenze
    
    # 2b. Titolarità
    peso_titolarita = 10
    if 'perc_matchesStarted' in df_ruolo.columns:
        perc_started = df_ruolo['perc_matchesStarted'].fillna(0) / 100
        titolarita_bonus = pd.Series(0.0, index=df_ruolo.index)
        for idx, perc in perc_started.items():
            if perc >= 0.85:
                titolarita_bonus[idx] = 1.0
            elif perc >= 0.7:
                titolarita_bonus[idx] = 0.7
            elif perc >= 0.5:
                titolarita_bonus[idx] = 0.4
            elif perc >= 0.3:
                titolarita_bonus[idx] = 0.2
            else:
                titolarita_bonus[idx] = 0.05
        
        utilizzo_score += titolarita_bonus * peso_titolarita
    
    score += utilizzo_score
    
    # 3. STATISTICHE OFFENSIVE (peso variabile per ruolo)
    peso_offensivo = {'A': 35, 'ATT': 35, 'C': 20, 'CEN': 20, 'D': 3, 'DIF': 3, 'P': 0, 'POR': 0}.get(ruolo, 5)
    
    if peso_offensivo > 0:
        stat_offensive = pd.Series(0.0, index=df_ruolo.index)
        
        # Goals per partita
        if 'goals' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            goals = df_ruolo['goals'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            goals_per_partita = goals / presenze.clip(lower=1)
            if ruolo in ['ATT', 'A']:
                goals_score = (goals_per_partita / 0.5).clip(0, 2.0)
            else:
                goals_score = (goals_per_partita / 0.8).clip(0, 1.0)
            stat_offensive += goals_score * 0.35
        
        # xG per partita
        if 'xgFromOpenPlays' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            xg = df_ruolo['xgFromOpenPlays'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            xg_per_partita = xg / presenze.clip(lower=1)
            if ruolo in ['ATT', 'A']:
                xg_score = (xg_per_partita / 0.4).clip(0, 1.8)
            else:
                xg_score = (xg_per_partita / 0.6).clip(0, 1.0)
            stat_offensive += xg_score * 0.25
        
        # Assists per partita
        if 'assists' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            assists = df_ruolo['assists'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            assists_per_partita = assists / presenze.clip(lower=1)
            if ruolo in ['ATT', 'A']:
                assists_score = (assists_per_partita / 0.25).clip(0, 1.6)
            else:
                assists_score = (assists_per_partita / 0.5).clip(0, 1.0)
            stat_offensive += assists_score * 0.2
        
        # xA per partita
        if 'xA' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            xa = df_ruolo['xA'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            xa_per_partita = xa / presenze.clip(lower=1)
            if ruolo in ['ATT', 'A']:
                xa_score = (xa_per_partita / 0.2).clip(0, 1.5)
            else:
                xa_score = (xa_per_partita / 0.4).clip(0, 1.0)
            stat_offensive += xa_score * 0.15
        
        score += stat_offensive * peso_offensivo
    
    # 4. FANTACALCIO INDEX (peso ridotto per ATT)
    peso_index = 5 if ruolo in ['ATT', 'A'] else 8
    if 'fantacalcioFantaindex' in df_ruolo.columns:
        index_norm = (df_ruolo['fantacalcioFantaindex'].fillna(0) - 60) / 40
        score += index_norm.clip(0, 1) * peso_index
    
    # 5. INDICI TECNICI
    peso_tecnici = 8 if ruolo in ['ATT', 'A'] else 5
    indici_tecnici = [
        'Shot_on_goal_Index', 'Offensive_actions_Index', 'Pass_forward_accuracy_Index',
        'Attacking_area_Index', 'Pass_leading_chances_Index', 'Dribbles_successful_Index'
    ]
    
    indici_disponibili = [col for col in indici_tecnici if col in df_ruolo.columns]
    if indici_disponibili:
        indici_score = df_ruolo[indici_disponibili].fillna(0).mean(axis=1) / 100
        score += indici_score * peso_tecnici
    
    # 6. PENALITÀ
    penalita = pd.Series(0.0, index=df_ruolo.index)
    
    if 'yellowCards' in df_ruolo.columns and 'presences' in df_ruolo.columns:
        yellow = df_ruolo['yellowCards'].fillna(0)
        presenze = df_ruolo['presences'].fillna(1)
        yellow_per_partita = yellow / presenze.clip(lower=1)
        penalita += (yellow_per_partita / 0.4) * 2
    
    if 'redCards' in df_ruolo.columns:
        red = df_ruolo['redCards'].fillna(0)
        penalita += red * 5
    
    if 'injured' in df_ruolo.columns:
        injured = df_ruolo['injured'].fillna(False).astype(int) * 5
        penalita += injured
    
    if 'banned' in df_ruolo.columns:
        banned = df_ruolo['banned'].fillna(False).astype(int) * 3
        penalita += banned
    
    score -= penalita.clip(0, 10) * 0.2
    
    # Applica il moltiplicatore ruolo
    score = score * peso_ruolo
    
    # Limiti per ruolo
    if ruolo in ['ATT', 'A']:
        return score.clip(0, 200)
    elif ruolo in ['CEN', 'C']:
        return score.clip(0, 150)
    elif ruolo in ['DIF', 'D']:
        return score.clip(0, 120)
    else:
        return score.clip(0, 100)