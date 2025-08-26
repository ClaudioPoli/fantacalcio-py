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


# --- Funzione per calcolare il prezzo massimo consigliato ---

def calcola_prezzo_massimo_consigliato(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola il prezzo massimo consigliato per ogni giocatore utilizzando TUTTI i parametri
    disponibili nel dataset, non solo la convenienza potenziale.
    
    FPEDIA: Utilizza punteggio, skills, fantamedia, presenze, trend, resistenza infortuni, etc.
    FSTATS: Utilizza tutti gli indici statistici, xG/xA, percentuali, indici tecnici, etc.
    
    Il calcolo è specifico per ogni dataset e ruolo.
    """
    from config import (POR_1, POR_2, POR_3, 
                       DIF_1, DIF_2, DIF_3, DIF_4, DIF_5, DIF_6, DIF_7, DIF_8,
                       CEN_1, CEN_2, CEN_3, CEN_4, CEN_5, CEN_6, CEN_7, CEN_8,
                       ATT_1, ATT_2, ATT_3, ATT_4, ATT_5, ATT_6)
    
    if df.empty:
        logger.warning("DataFrame è vuoto. Calcolo prezzo massimo saltato.")
        return df

    # Mapping dei ruoli ai valori degli slot
    slot_values = {
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
    prezzi_massimi = []
    
    # Raggruppa per ruolo
    for ruolo in df['Ruolo'].unique():
        if pd.isna(ruolo):
            continue
            
        # Filtra giocatori per ruolo
        df_ruolo = df[df['Ruolo'] == ruolo].copy()
        
        # Ottieni i valori degli slot per questo ruolo
        valori_slot = slot_values.get(ruolo, [10, 5, 1])
        
        # === CALCOLO SCORE COMPLESSIVO USANDO TUTTE LE COLONNE ===
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
            # Se tutti hanno score 0, assegna prezzi minimi
            for idx in df_ruolo.index:
                prezzi_massimi.append((idx, 1))
        else:
            # Calcola il prezzo per ogni giocatore basato sulla sua posizione nella classifica
            for i, (idx, row) in enumerate(df_ruolo.iterrows()):
                score = row['Score_Complessivo']
                
                # Calcola la posizione percentuale del giocatore (0-1)
                if score_complessivo.max() > score_complessivo.min():
                    posizione_norm = (score - score_complessivo.min()) / (score_complessivo.max() - score_complessivo.min())
                else:
                    posizione_norm = 1.0
                
                # Interpola tra il valore massimo e minimo degli slot
                valore_max = valori_slot[0]
                valore_min = valori_slot[-1]
                
                # Calcola il prezzo usando interpolazione esponenziale
                esponente = 2.0
                prezzo_interpolato = valore_min + (valore_max - valore_min) * (posizione_norm ** esponente)
                
                # Margine di sicurezza
                margine_sicurezza = 0.85
                prezzo_max = int(round(prezzo_interpolato * margine_sicurezza))
                prezzo_max = max(1, prezzo_max)
                
                prezzi_massimi.append((idx, prezzo_max))
    
    # Crea un DataFrame con i prezzi calcolati
    prezzi_df = pd.DataFrame(prezzi_massimi, columns=['index', 'Prezzo Massimo Consigliato'])
    prezzi_df.set_index('index', inplace=True)
    
    # Aggiungi la colonna al DataFrame originale
    df['Prezzo Massimo Consigliato'] = 0
    df.loc[prezzi_df.index, 'Prezzo Massimo Consigliato'] = prezzi_df['Prezzo Massimo Consigliato']
    
    logger.info("Prezzo massimo consigliato calcolato utilizzando TUTTI i parametri disponibili.")
    return df


def calcola_score_fpedia(df_ruolo: pd.DataFrame, ruolo: str) -> pd.Series:
    """
    Calcola uno score complessivo per FPEDIA utilizzando tutti i parametri disponibili.
    MIGLIORATO: Maggior peso alle presenze e fattore di affidabilità.
    """
    score = pd.Series(0.0, index=df_ruolo.index)
    
    # 1. PUNTEGGIO BASE (peso 25% - ridotto)
    if 'Punteggio' in df_ruolo.columns:
        punteggio_norm = df_ruolo['Punteggio'].fillna(0) / 100
        score += punteggio_norm * 25
    
    # 2. FANTAMEDIA CON FATTORE DI AFFIDABILITÀ (peso 30% - aumentato)
    if 'Fantamedia anno 2024-2025' in df_ruolo.columns and 'Presenze campionato corrente' in df_ruolo.columns:
        fm_attuale = df_ruolo['Fantamedia anno 2024-2025'].fillna(0)
        presenze = df_ruolo['Presenze campionato corrente'].fillna(0)
        
        # FATTORE DI AFFIDABILITÀ basato sulle presenze
        # Titolari fissi (>25 presenze): 100% affidabilità
        # Titolari parziali (15-25): 70-100% affidabilità  
        # Riserve utilizzate (5-15): 30-70% affidabilità
        # Riserve poco utilizzate (<5): 10-30% affidabilità
        def calcola_affidabilita(presenze):
            if presenze >= 25:
                return 1.0  # Titolare fisso
            elif presenze >= 15:
                return 0.7 + 0.3 * (presenze - 15) / 10  # 70%-100%
            elif presenze >= 5:
                return 0.3 + 0.4 * (presenze - 5) / 10   # 30%-70%
            elif presenze > 0:
                return 0.1 + 0.2 * presenze / 5          # 10%-30%
            else:
                return 0.05  # Praticamente mai giocato
        
        affidabilita = presenze.apply(calcola_affidabilita)
        fm_affidabile = (fm_attuale / 10) * affidabilita
        score += fm_affidabile.clip(0, 1) * 30
    
    # 3. PRESENZE COME INDICATORE DI TITOLARITÀ (peso 20% - aumentato)
    if 'Presenze campionato corrente' in df_ruolo.columns:
        presenze = df_ruolo['Presenze campionato corrente'].fillna(0)
        
        # Bonus progressivo per le presenze
        def calcola_bonus_presenze(presenze):
            if presenze >= 30:
                return 1.0  # Titolarissimo
            elif presenze >= 25:
                return 0.9  # Titolare fisso
            elif presenze >= 20:
                return 0.7  # Titolare
            elif presenze >= 15:
                return 0.5  # Semi-titolare
            elif presenze >= 10:
                return 0.3  # Riserva utilizzata
            elif presenze >= 5:
                return 0.15 # Riserva
            else:
                return 0.05 # Panchinaro
        
        bonus_presenze = presenze.apply(calcola_bonus_presenze)
        score += bonus_presenze * 20
    
    # 4. RESISTENZA INFORTUNI (peso 8% - ridotto)
    if 'Resistenza infortuni' in df_ruolo.columns:
        resistenza = df_ruolo['Resistenza infortuni'].fillna(50) / 100
        score += resistenza * 8
    
    # 5. BUON INVESTIMENTO (peso 7% - ridotto)
    if 'Buon investimento' in df_ruolo.columns:
        investimento = df_ruolo['Buon investimento'].fillna(0) / 100
        score += investimento * 7
    
    # 6. SKILLS QUALITATIVE (peso 5% - ridotto)
    if 'Skills' in df_ruolo.columns:
        skills_score = pd.Series(0.0, index=df_ruolo.index)
        skills_mapping = {
            "Fuoriclasse": 2, "Titolare": 4, "Goleador": 5, "Rigorista": 6,
            "Buona Media": 3, "Assistman": 3, "Piazzati": 3, "Giovane talento": 2,
            "Outsider": 2, "Panchinaro": -5, "Falloso": -3
        }
        for idx, row in df_ruolo.iterrows():
            try:
                skills_list = ast.literal_eval(row.get("Skills", "[]"))
                skill_bonus = sum(skills_mapping.get(skill, 0) for skill in skills_list)
                skills_score[idx] = skill_bonus
            except:
                skills_score[idx] = 0
        skills_norm = (skills_score + 10) / 20  # Normalizza -10/+10 -> 0-1
        score += skills_norm.clip(0, 1) * 5
    
    # 7. BONUS/MALUS SPECIFICI (peso 5%)
    bonus_malus = pd.Series(0.0, index=df_ruolo.index)
    
    # Trend
    if 'Trend' in df_ruolo.columns:
        trend_bonus = df_ruolo['Trend'].map({'UP': 2, 'STABLE': 0, 'DOWN': -2}).fillna(0)
        bonus_malus += trend_bonus
    
    # Consigliato prossima giornata
    if 'Consigliato prossima giornata' in df_ruolo.columns:
        consigliato = df_ruolo['Consigliato prossima giornata'].fillna(False).astype(int) * 2
        bonus_malus += consigliato
    
    # Infortunato (malus SEVERO)
    if 'Infortunato' in df_ruolo.columns:
        infortunato = df_ruolo['Infortunato'].fillna(False).astype(int) * -5  # Aumentato
        bonus_malus += infortunato
    
    # Nuovo acquisto (malus per incertezza)
    if 'Nuovo acquisto' in df_ruolo.columns:
        nuovo = df_ruolo['Nuovo acquisto'].fillna(False).astype(int) * -2  # Aumentato
        bonus_malus += nuovo
    
    bonus_norm = (bonus_malus + 7) / 14  # Normalizza -7/+7 -> 0-1
    score += bonus_norm.clip(0, 1) * 5
    
    return score


def calcola_score_fstats(df_ruolo: pd.DataFrame, ruolo: str) -> pd.Series:
    """
    Calcola uno score complessivo per FSTATS utilizzando tutti i parametri statistici disponibili.
    MIGLIORATO: Maggior peso alle presenze e fattore di affidabilità per fantamedia.
    """
    score = pd.Series(0.0, index=df_ruolo.index)
    
    # 1. FANTACALCIO FANTA INDEX (peso 18% - ridotto)
    if 'fantacalcioFantaindex' in df_ruolo.columns:
        fanta_index = df_ruolo['fantacalcioFantaindex'].fillna(0) / 100
        score += fanta_index * 18
    
    # 2. FANTAMEDIA CON FATTORE DI AFFIDABILITÀ (peso 25% - aumentato)
    if 'fanta_avg' in df_ruolo.columns and 'presences' in df_ruolo.columns:
        fanta_avg = df_ruolo['fanta_avg'].fillna(0)
        presenze = df_ruolo['presences'].fillna(0)
        
        # FATTORE DI AFFIDABILITÀ identico a FPEDIA
        def calcola_affidabilita(presenze):
            if presenze >= 25:
                return 1.0  # Titolare fisso
            elif presenze >= 15:
                return 0.7 + 0.3 * (presenze - 15) / 10
            elif presenze >= 5:
                return 0.3 + 0.4 * (presenze - 5) / 10
            elif presenze > 0:
                return 0.1 + 0.2 * presenze / 5
            else:
                return 0.05
        
        affidabilita = presenze.apply(calcola_affidabilita)
        fanta_avg_affidabile = (fanta_avg / 10) * affidabilita
        score += fanta_avg_affidabile.clip(0, 1) * 25
    
    # 3. PRESENZE E UTILIZZO (peso 22% - aumentato)
    utilizzo_score = pd.Series(0.0, index=df_ruolo.index)
    
    # 3a. Presenze assolute (12%)
    if 'presences' in df_ruolo.columns:
        presenze = df_ruolo['presences'].fillna(0)
        
        def calcola_bonus_presenze(presenze):
            if presenze >= 30:
                return 1.0
            elif presenze >= 25:
                return 0.9
            elif presenze >= 20:
                return 0.7
            elif presenze >= 15:
                return 0.5
            elif presenze >= 10:
                return 0.3
            elif presenze >= 5:
                return 0.15
            else:
                return 0.05
        
        bonus_presenze = presenze.apply(calcola_bonus_presenze)
        utilizzo_score += bonus_presenze * 12
    
    # 3b. Percentuale titolarità (10%)
    if 'perc_matchesStarted' in df_ruolo.columns:
        perc_started = df_ruolo['perc_matchesStarted'].fillna(0) / 100
        # Bonus per chi è titolare fisso
        titolarita_bonus = pd.Series(0.0, index=df_ruolo.index)
        for idx, perc in perc_started.items():
            if perc >= 0.8:  # >80% titolare
                titolarita_bonus[idx] = 1.0
            elif perc >= 0.6:  # 60-80% titolare
                titolarita_bonus[idx] = 0.8
            elif perc >= 0.4:  # 40-60% semi-titolare
                titolarita_bonus[idx] = 0.5
            elif perc >= 0.2:  # 20-40% riserva utilizzata
                titolarita_bonus[idx] = 0.3
            else:  # <20% panchinaro
                titolarita_bonus[idx] = 0.1
        
        utilizzo_score += titolarita_bonus * 10
    
    score += utilizzo_score
    
    # 4. STATISTICHE OFFENSIVE (peso variabile per ruolo)
    peso_offensivo = {'A': 20, 'ATT': 20, 'C': 12, 'CEN': 12, 'D': 5, 'DIF': 5, 'P': 0, 'POR': 0}.get(ruolo, 8)
    
    if peso_offensivo > 0:
        stat_offensive = pd.Series(0.0, index=df_ruolo.index)
        
        # Expected Goals e Goals (pesati per presenze!)
        if 'xgFromOpenPlays' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            xg = df_ruolo['xgFromOpenPlays'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)  # Evita divisione per 0
            xg_per_partita = xg / presenze.clip(lower=1)  # xG per partita
            stat_offensive += (xg_per_partita / 0.5).clip(0, 1) * 0.4  # 0.5 xG/partita = ottimo
        
        if 'goals' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            goals = df_ruolo['goals'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            goals_per_partita = goals / presenze.clip(lower=1)
            stat_offensive += (goals_per_partita / 0.7).clip(0, 1) * 0.3  # 0.7 gol/partita = eccellente
        
        # Expected Assists e Assists (pesati per presenze!)
        if 'xA' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            xa = df_ruolo['xA'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            xa_per_partita = xa / presenze.clip(lower=1)
            stat_offensive += (xa_per_partita / 0.3).clip(0, 1) * 0.2  # 0.3 xA/partita = ottimo
        
        if 'assists' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            assists = df_ruolo['assists'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            assists_per_partita = assists / presenze.clip(lower=1)
            stat_offensive += (assists_per_partita / 0.4).clip(0, 1) * 0.1  # 0.4 assist/partita = eccellente
        
        score += stat_offensive * peso_offensivo
    
    # 5. INDICI TECNICI SPECIALIZZATI (peso 12% - ridotto)
    indici_tecnici = [
        'Shot_on_goal_Index', 'Offensive_actions_Index', 'Pass_forward_accuracy_Index',
        'Attacking_area_Index', 'Pass_leading_chances_Index', 'Dribbles_successful_Index'
    ]
    
    indici_disponibili = [col for col in indici_tecnici if col in df_ruolo.columns]
    if indici_disponibili:
        indici_score = df_ruolo[indici_disponibili].fillna(0).mean(axis=1) / 100
        score += indici_score * 12
    
    # 6. STATISTICHE DIFENSIVE (per difensori e portieri)
    peso_difensivo = {'P': 18, 'POR': 18, 'D': 12, 'DIF': 12, 'C': 3, 'CEN': 3, 'A': 0, 'ATT': 0}.get(ruolo, 0)
    
    if peso_difensivo > 0:
        stat_difensive = pd.Series(0.0, index=df_ruolo.index)
        
        if 'Defense_solidity_Index' in df_ruolo.columns:
            defense = df_ruolo['Defense_solidity_Index'].fillna(0) / 100
            stat_difensive += defense * 0.4
        
        if 'gkCleanSheets' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            clean_sheets = df_ruolo['gkCleanSheets'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            cs_per_partita = clean_sheets / presenze.clip(lower=1)
            stat_difensive += (cs_per_partita / 0.4).clip(0, 1) * 0.3  # 0.4 CS/partita = ottimo
        
        if 'gkPenaltiesSaved' in df_ruolo.columns:
            pen_saved = df_ruolo['gkPenaltiesSaved'].fillna(0)
            stat_difensive += (pen_saved / 3).clip(0, 1) * 0.3  # 3 rigori parati = eccellente
        
        score += stat_difensive * peso_difensivo
    
    # 7. PENALITÀ SEVERE (peso 5%)
    penalita = pd.Series(0.0, index=df_ruolo.index)
    
    if 'yellowCards' in df_ruolo.columns and 'presences' in df_ruolo.columns:
        yellow = df_ruolo['yellowCards'].fillna(0)
        presenze = df_ruolo['presences'].fillna(1)
        yellow_per_partita = yellow / presenze.clip(lower=1)
        penalita += (yellow_per_partita / 0.3) * 3  # >0.3 ammonizioni/partita = problematico
    
    if 'redCards' in df_ruolo.columns:
        red = df_ruolo['redCards'].fillna(0)
        penalita += red * 8  # Penalità severa per espulsioni
    
    if 'injured' in df_ruolo.columns:
        injured = df_ruolo['injured'].fillna(False).astype(int) * 8  # Penalità severa per infortunio
        penalita += injured
    
    if 'banned' in df_ruolo.columns:
        banned = df_ruolo['banned'].fillna(False).astype(int) * 5  # Penalità per squalifica
        penalita += banned
    
    score -= penalita.clip(0, 15) * 0.33  # Sottrae penalità (max 5 punti)
    
    return score.clip(0, 100)
