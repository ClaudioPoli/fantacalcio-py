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
                
                # SISTEMA RICALIBRATO per creare sfumature realistiche
                if ruolo in ['ATT', 'A']:
                    # Per attaccanti: interpolazione PIÙ LINEARE per preservare differenze
                    esponente = 1.2  # Molto meno aggressivo - quasi lineare
                    margine_sicurezza = 0.95
                    
                    # NESSUNA amplificazione aggiuntiva - usa solo gli score naturali
                    # Il range 69-99 deve tradursi in prezzi diversi
                    
                elif ruolo in ['CEN', 'C']:
                    # Per centrocampisti: interpolazione MOLTO PIÙ LINEARE per differenziazione
                    esponente = 1.1  # Quasi completamente lineare
                    margine_sicurezza = 0.90  # Margine per non superare CEN_1=50
                
                elif ruolo in ['DIF', 'D']:
                    # Per difensori: rispetta le fasce config (DIF_1=30, DIF_2=20, etc.)
                    esponente = 1.2  # Leggermente convesso per premiare i top
                    margine_sicurezza = 1.0  # Usa tutto il budget DIF_1=30
                        
                else:
                    esponente = 3.0
                    margine_sicurezza = 0.7
                    
                prezzo_interpolato = valore_min + (valore_max - valore_min) * (posizione_norm ** esponente)
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
    RICALIBRATO: Prezzi più realistici, maggior peso alle statistiche concrete.
    """
    score = pd.Series(0.0, index=df_ruolo.index)
    
    # PESO RUOLO: Attaccanti hanno moltiplicatore bonus per i maggiori bonus fantacalcio
    peso_ruolo = {'ATT': 1.2, 'A': 1.2, 'CEN': 1.0, 'C': 1.0, 'DIF': 0.9, 'D': 0.9, 'POR': 0.8, 'P': 0.8}.get(ruolo, 1.0)
    
    # 1. FANTAMEDIA GREZZA (peso 50% - base principale)
    if 'Fantamedia anno 2024-2025' in df_ruolo.columns:
        fm_attuale = df_ruolo['Fantamedia anno 2024-2025'].fillna(0)
        # Normalizza: 6.0 = ottimo, 5.5 = buono, 5.0 = sufficiente
        fm_norm = ((fm_attuale - 4.5) / 2.5).clip(0, 1)  # 4.5-7.0 -> 0-1
        score += fm_norm * 50
    
    # 2. FATTORE DI AFFIDABILITÀ/PRESENZE (peso 35% - critico)
    if 'Presenze campionato corrente' in df_ruolo.columns:
        presenze = df_ruolo['Presenze campionato corrente'].fillna(0)
        
        # Affidabilità più severa per abbassare i prezzi
        def calcola_affidabilita_severa(presenze):
            if presenze >= 30:
                return 1.0  # Solo i titolarissimi hanno 100%
            elif presenze >= 25:
                return 0.8  # Titolari fissi ridotti
            elif presenze >= 20:
                return 0.6  # Titolari
            elif presenze >= 15:
                return 0.4  # Semi-titolari
            elif presenze >= 10:
                return 0.25 # Riserve utilizzate
            elif presenze >= 5:
                return 0.1  # Riserve rare
            else:
                return 0.02 # Praticamente mai
        
        affidabilita = presenze.apply(calcola_affidabilita_severa)
        score += affidabilita * 35
    
    # 3. PUNTEGGIO FPEDIA (peso 10% - molto ridotto)
    if 'Punteggio' in df_ruolo.columns:
        punteggio_norm = (df_ruolo['Punteggio'].fillna(50) - 30) / 70  # 30-100 -> 0-1
        score += punteggio_norm.clip(0, 1) * 10
    
    # 4. SKILLS CONCRETE (peso 3% - solo quelle importanti)
    if 'Skills' in df_ruolo.columns:
        skills_score = pd.Series(0.0, index=df_ruolo.index)
        skills_mapping_realistico = {
            "Rigorista": 8,    # Molto importante per bonus
            "Goleador": 6,     # Importante per attaccanti
            "Titolare": 4,     # Conferma titolarità
            "Assistman": 3,    # Bonus assist
            "Piazzati": 2,     # Piccolo bonus
            "Panchinaro": -10, # Penalità severa
            "Falloso": -5,     # Penalità media
            "Fuoriclasse": 2,  # Poco valore concreto
            "Buona Media": 1,  # Poco valore concreto
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
    
    # 5. RESISTENZA E INVESTIMENTO (peso 2% - molto ridotto)
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
    RICALIBRATO: Prezzi più realistici, focus su statistiche concrete.
    """
    score = pd.Series(0.0, index=df_ruolo.index)
    
    # PESO RUOLO: Attaccanti hanno moltiplicatore molto più alto
    peso_ruolo = {'ATT': 1.0, 'A': 1.0, 'CEN': 1.0, 'C': 1.0, 'DIF': 0.85, 'D': 0.85, 'POR': 0.8, 'P': 0.8}.get(ruolo, 1.0)
    
    # 1. FANTAMEDIA GREZZA (peso 30% per ATT, 45% per altri - ancora ridotto per ATT)
    peso_fantamedia = 30 if ruolo in ['ATT', 'A'] else 45
    if 'fanta_avg' in df_ruolo.columns:
        fanta_avg = df_ruolo['fanta_avg'].fillna(0)
        # Scaling più severo: 6.5 = eccellente, 6.0 = ottimo, 5.5 = buono
        fanta_norm = ((fanta_avg - 4.5) / 3.0).clip(0, 1)  # 4.5-7.5 -> 0-1
        score += fanta_norm * peso_fantamedia
    
    # 2. AFFIDABILITÀ E UTILIZZO (peso 25% per ATT, 30% per altri - ridotto per ATT)
    peso_utilizzo = 25 if ruolo in ['ATT', 'A'] else 30
    utilizzo_score = pd.Series(0.0, index=df_ruolo.index)
    
    # 2a. Presenze (15% per ATT, 20% per altri)
    peso_presenze = 15 if ruolo in ['ATT', 'A'] else 20
    if 'presences' in df_ruolo.columns:
        presenze = df_ruolo['presences'].fillna(0)
        
        def calcola_affidabilita_severa(presenze):
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
        
        affidabilita = presenze.apply(calcola_affidabilita_severa)
        utilizzo_score += affidabilita * peso_presenze
    
    # 2b. Titolarità (10% per ATT, 10% per altri)
    peso_titolarita = 10
    if 'perc_matchesStarted' in df_ruolo.columns:
        perc_started = df_ruolo['perc_matchesStarted'].fillna(0) / 100
        # Bonus più severo per titolarità
        titolarita_bonus = pd.Series(0.0, index=df_ruolo.index)
        for idx, perc in perc_started.items():
            if perc >= 0.85:    # >85% titolare
                titolarita_bonus[idx] = 1.0
            elif perc >= 0.7:   # 70-85% 
                titolarita_bonus[idx] = 0.7
            elif perc >= 0.5:   # 50-70%
                titolarita_bonus[idx] = 0.4
            elif perc >= 0.3:   # 30-50%
                titolarita_bonus[idx] = 0.2
            else:              # <30%
                titolarita_bonus[idx] = 0.05
        
        utilizzo_score += titolarita_bonus * peso_titolarita
    
    score += utilizzo_score
    
    # 3. STATISTICHE OFFENSIVE (peso MASSIMO per attaccanti)
    peso_offensivo = {'A': 35, 'ATT': 35, 'C': 8, 'CEN': 8, 'D': 3, 'DIF': 3, 'P': 0, 'POR': 0}.get(ruolo, 5)
    
    if peso_offensivo > 0:
        stat_offensive = pd.Series(0.0, index=df_ruolo.index)
        
        # Goals per partita - scaling ottimizzato per creare differenze
        if 'goals' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            goals = df_ruolo['goals'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            goals_per_partita = goals / presenze.clip(lower=1)
            # Sistema più graduato: 0.3 = buono, 0.5 = ottimo, 0.7+ = fenomenale
            if ruolo in ['ATT', 'A']:
                goals_score = (goals_per_partita / 0.5).clip(0, 2.0)  # Max 200% per fenomeni
            else:
                goals_score = (goals_per_partita / 0.8).clip(0, 1.0)
            stat_offensive += goals_score * 0.35
        
        # xG per partita - più selettivo
        if 'xgFromOpenPlays' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            xg = df_ruolo['xgFromOpenPlays'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            xg_per_partita = xg / presenze.clip(lower=1)
            # Sistema graduato: 0.25 = buono, 0.4 = ottimo, 0.6+ = fenomenale
            if ruolo in ['ATT', 'A']:
                xg_score = (xg_per_partita / 0.4).clip(0, 1.8)  # Max 180% per fenomeni
            else:
                xg_score = (xg_per_partita / 0.6).clip(0, 1.0)
            stat_offensive += xg_score * 0.25
        
        # Assists per partita - importante per attaccanti moderni
        if 'assists' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            assists = df_ruolo['assists'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            assists_per_partita = assists / presenze.clip(lower=1)
            # Sistema graduato per assist
            if ruolo in ['ATT', 'A']:
                assists_score = (assists_per_partita / 0.25).clip(0, 1.6)  # 0.25 = ottimo
            else:
                assists_score = (assists_per_partita / 0.5).clip(0, 1.0)
            stat_offensive += assists_score * 0.2
        
        # xA per partita - capacità di creare occasioni
        if 'xA' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            xa = df_ruolo['xA'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            xa_per_partita = xa / presenze.clip(lower=1)
            # Sistema graduato per expected assists
            if ruolo in ['ATT', 'A']:
                xa_score = (xa_per_partita / 0.2).clip(0, 1.5)  # 0.2 = ottimo
            else:
                xa_score = (xa_per_partita / 0.4).clip(0, 1.0)
            stat_offensive += xa_score * 0.15
        
        # EFFICIENZA AVANZATA: Differenziazione per veri fenomeni
        if ruolo in ['ATT', 'A']:
            # TEMPORANEAMENTE DISABILITATO PER DEBUG
            pass  # Non fare nessuna modifica per ora
            
        # RAFFINAMENTO PER CENTROCAMPISTI  
        elif ruolo in ['CEN', 'C']:
            # Sistema di differenziazione LEGGERO per centrocampisti
            for idx, row in df_ruolo.iterrows():
                goals = row.get('goals', 0)
                assists = row.get('assists', 0)
                presenze = row.get('presences', 1)
                fantamedia = row.get('fanta_avg', 0)
                
                # BONUS MOLTO PICCOLI per evitare compressione
                bonus_qualita = 0
                
                # Fantamedia excellence - bonus ridottissimi
                if fantamedia >= 8.0:          # Elite (Tramoni level)
                    bonus_qualita += 3
                elif fantamedia >= 7.5:        # Excellent (Orsolini, McTominay)
                    bonus_qualita += 2
                elif fantamedia >= 7.0:        # Very good 
                    bonus_qualita += 1
                elif fantamedia < 6.0:         # Below average
                    bonus_qualita -= 1
                
                # Contributi totali - bonus piccoli
                goals_per_game = goals / max(presenze, 1)
                assists_per_game = assists / max(presenze, 1)
                total_contributions = goals_per_game + assists_per_game
                
                if total_contributions >= 0.55:    # Top (Orsolini level)
                    bonus_qualita += 4
                elif total_contributions >= 0.45:  # Excellent
                    bonus_qualita += 3
                elif total_contributions >= 0.35:  # Good  
                    bonus_qualita += 2
                elif total_contributions >= 0.25:  # Decent
                    bonus_qualita += 1
                elif total_contributions < 0.1:    # Low
                    bonus_qualita -= 1
                
                # APPLICA MODIFICHE MINIME
                current_score = stat_offensive.loc[idx] 
                modified_score = current_score + bonus_qualita
                stat_offensive.loc[idx] = modified_score
                
        # RAFFINAMENTO PER DIFENSORI  
        elif ruolo in ['DIF', 'D']:
            # Sistema ULTRA-OFFENSIVO per difensori - gol e assist valgono ORO!
            for idx, row in df_ruolo.iterrows():
                goals = row.get('goals', 0)
                assists = row.get('assists', 0)
                presenze = row.get('appearances', 1)
                mins_played = row.get('mins_played', 0)
                fantamedia = row.get('expectedFantamediaMean', 0)
                
                # BONUS ENORMI per difensori offensivi - sono i più preziosi!
                bonus_qualita = 0
                
                # 1. CONTRIBUTI OFFENSIVI - BONUS MASSIMI ASSOLUTI
                goals_per_game = goals / max(presenze, 1)
                assists_per_game = assists / max(presenze, 1)
                total_contributions = goals_per_game + assists_per_game
                
                # Ogni gol/assist di un difensore vale ORO nel fantacalcio!
                if total_contributions >= 0.30:    # Elite (Dimarco 0.333, Dumfries 0.310)
                    bonus_qualita += 25  # BONUS GIGANTESCO
                elif total_contributions >= 0.25:  # Excellent (Gosens 0.242, Martin 0.250)
                    bonus_qualita += 20  
                elif total_contributions >= 0.20:  # Very good (Zortea 0.229, Bellanova 0.229)
                    bonus_qualita += 17
                elif total_contributions >= 0.15:  # Good (Kamara 0.167, Valeri 0.171)
                    bonus_qualita += 14
                elif total_contributions >= 0.10:  # Decent (Di Lorenzo 0.135, Cambiaso 0.121)
                    bonus_qualita += 10
                elif total_contributions >= 0.05:  # Some contribution
                    bonus_qualita += 6
                elif total_contributions > 0:      # Almeno qualcosa
                    bonus_qualita += 3
                else:                               # Zero contributi = penalità
                    bonus_qualita -= 5
                
                # 2. BONUS AGGIUNTIVI PER GOL (più rari e preziosi degli assist)
                if goals >= 6:  # Zortea, Dumfries level
                    bonus_qualita += 8
                elif goals >= 4:  # Dimarco, Zappacosta level
                    bonus_qualita += 6
                elif goals >= 2:  # Cambiaso, Valeri level
                    bonus_qualita += 4
                elif goals >= 1:  # Almeno un gol
                    bonus_qualita += 2
                
                # 3. BONUS AGGIUNTIVI PER ASSIST (specialisti cross/passaggi)
                if assists >= 8:  # Bellanova level
                    bonus_qualita += 6
                elif assists >= 6:  # Dimarco, Tavares level
                    bonus_qualita += 5
                elif assists >= 4:  # Kamara, Valeri level
                    bonus_qualita += 3
                elif assists >= 2:  # Dumfries, Zortea level
                    bonus_qualita += 2
                
                # 4. TITOLARITÀ - importante ma secondaria rispetto all'attacco
                mins_per_game = mins_played / max(presenze, 1)
                if mins_per_game >= 90:        # Titolare fisso (Di Lorenzo 98min)
                    bonus_qualita += 6
                elif mins_per_game >= 80:      # Spesso titolare  
                    bonus_qualita += 4
                elif mins_per_game >= 70:      # Buona titolarità
                    bonus_qualita += 2
                elif mins_per_game >= 60:      # Discreto utilizzo
                    bonus_qualita += 1
                else:                           # Poco utilizzato
                    bonus_qualita -= 3
                
                # 5. STATISTICHE OFFENSIVE AVANZATE - peso maggiore
                offensive_actions = row.get('Offensive_actions_Index', 0)
                attacking_area = row.get('Attacking_area_Index', 0)
                cross_accuracy = row.get('Cross_accuracy_Index', 0)
                
                # Azioni offensive (Bastoni 93.8, Cambiaso 89.5)
                if offensive_actions >= 90:
                    bonus_qualita += 6
                elif offensive_actions >= 80:
                    bonus_qualita += 4
                elif offensive_actions >= 70:
                    bonus_qualita += 2
                
                # Presenza in area avversaria (Dumfries 75.5, Dimarco 73.7)
                if attacking_area >= 75:
                    bonus_qualita += 5
                elif attacking_area >= 65:
                    bonus_qualita += 3
                elif attacking_area >= 55:
                    bonus_qualita += 1
                
                # Precisione cross (Tavares 92.9, Bellanova 89.3, Zortea 88.8)
                if cross_accuracy >= 85:
                    bonus_qualita += 5
                elif cross_accuracy >= 75:
                    bonus_qualita += 3
                elif cross_accuracy >= 65:
                    bonus_qualita += 1
                
                # 6. FANTAMEDIA - peso ridotto, le statistiche offensive contano di più
                if fantamedia > 0:  # Solo se dato disponibile
                    if fantamedia >= 6.5:          # Ottima
                        bonus_qualita += 3
                    elif fantamedia >= 6.0:        # Buona
                        bonus_qualita += 2
                    elif fantamedia >= 5.5:        # Discreta
                        bonus_qualita += 1
                    elif fantamedia < 5.0:         # Scarsa
                        bonus_qualita -= 2
                
                # APPLICA MODIFICHE SOSTANZIALI PER CREARE SEPARAZIONE
                current_score = stat_offensive.loc[idx] 
                modified_score = current_score + bonus_qualita
                stat_offensive.loc[idx] = modified_score
                
        
        score += stat_offensive * peso_offensivo
    
    # 4. FANTACALCIO INDEX (peso ridotto per ATT, normale per altri)
    peso_index = 5 if ruolo in ['ATT', 'A'] else 8
    if 'fantacalcioFantaindex' in df_ruolo.columns:
        index_norm = (df_ruolo['fantacalcioFantaindex'].fillna(0) - 60) / 40  # 60-100 -> 0-1
        score += index_norm.clip(0, 1) * peso_index
    
    # 5. INDICI TECNICI E SPECIALIZZAZIONI (peso variabile per ruolo)
    peso_tecnici = 8 if ruolo in ['ATT', 'A'] else 5  # Più importante per attaccanti
    indici_tecnici = [
        'Shot_on_goal_Index', 'Offensive_actions_Index', 'Pass_forward_accuracy_Index',
        'Attacking_area_Index', 'Pass_leading_chances_Index', 'Dribbles_successful_Index'
    ]
    
    indici_disponibili = [col for col in indici_tecnici if col in df_ruolo.columns]
    if indici_disponibili:
        indici_score = df_ruolo[indici_disponibili].fillna(0).mean(axis=1) / 100
        score += indici_score * peso_tecnici
    
    # 6. ANALISI AVANZATE SPECIFICHE PER ATTACCANTI
    if ruolo in ['ATT', 'A']:
        bonus_attaccanti = pd.Series(0.0, index=df_ruolo.index)
        
        # Consistenza nelle prestazioni (meno variabilità = meglio)
        if 'fanta_avg' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            fm = df_ruolo['fanta_avg'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            # Bonus per alta fantamedia + molte presenze (consistenza)
            consistenza = (fm / 10) * (presenze / 38).clip(0, 1)
            bonus_attaccanti += consistenza * 3
        
        # Rendimento in zona gol (Shot on goal index)
        if 'Shot_on_goal_Index' in df_ruolo.columns:
            shot_index = df_ruolo['Shot_on_goal_Index'].fillna(0) / 100
            bonus_attaccanti += shot_index * 2
        
        # Capacità di concludere in area (Attacking area index)
        if 'Attacking_area_Index' in df_ruolo.columns:
            area_index = df_ruolo['Attacking_area_Index'].fillna(0) / 100
            bonus_attaccanti += area_index * 2
        
        # Dribbling (importante per attaccanti moderni)
        if 'Dribbles_successful_Index' in df_ruolo.columns:
            dribble_index = df_ruolo['Dribbles_successful_Index'].fillna(0) / 100
            bonus_attaccanti += dribble_index * 1.5
        
        # PENALIZZAZIONE per rendimento inconsistente
        if 'yellowCards' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            yellow = df_ruolo['yellowCards'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            indisciplina = yellow / presenze.clip(lower=1)
            # Penalizza chi prende più di 0.3 ammonizioni/partita
            penalita_disciplina = (indisciplina / 0.3).clip(0, 2) * 1.5
            bonus_attaccanti -= penalita_disciplina
        
        score += bonus_attaccanti
    
    # 6. STATISTICHE DIFENSIVE (peso ridotto)
    peso_difensivo = {'P': 10, 'POR': 10, 'D': 7, 'DIF': 7, 'C': 2, 'CEN': 2, 'A': 0, 'ATT': 0}.get(ruolo, 0)
    
    if peso_difensivo > 0:
        stat_difensive = pd.Series(0.0, index=df_ruolo.index)
        
        if 'Defense_solidity_Index' in df_ruolo.columns:
            defense = df_ruolo['Defense_solidity_Index'].fillna(0) / 100
            stat_difensive += defense * 0.5
        
        if 'gkCleanSheets' in df_ruolo.columns and 'presences' in df_ruolo.columns:
            clean_sheets = df_ruolo['gkCleanSheets'].fillna(0)
            presenze = df_ruolo['presences'].fillna(1)
            cs_per_partita = clean_sheets / presenze.clip(lower=1)
            stat_difensive += (cs_per_partita / 0.5).clip(0, 1) * 0.3  # 0.5 CS/partita = ottimo
        
        if 'gkPenaltiesSaved' in df_ruolo.columns:
            pen_saved = df_ruolo['gkPenaltiesSaved'].fillna(0)
            stat_difensive += (pen_saved / 2).clip(0, 1) * 0.2  # 2 rigori = ottimo
        
        score += stat_difensive * peso_difensivo
    
    # 7. PENALITÀ (peso 2% - ridotto)
    penalita = pd.Series(0.0, index=df_ruolo.index)
    
    if 'yellowCards' in df_ruolo.columns and 'presences' in df_ruolo.columns:
        yellow = df_ruolo['yellowCards'].fillna(0)
        presenze = df_ruolo['presences'].fillna(1)
        yellow_per_partita = yellow / presenze.clip(lower=1)
        penalita += (yellow_per_partita / 0.4) * 2  # >0.4 ammonizioni/partita
    
    if 'redCards' in df_ruolo.columns:
        red = df_ruolo['redCards'].fillna(0)
        penalita += red * 5  # Penalità ridotta
    
    if 'injured' in df_ruolo.columns:
        injured = df_ruolo['injured'].fillna(False).astype(int) * 5
        penalita += injured
    
    if 'banned' in df_ruolo.columns:
        banned = df_ruolo['banned'].fillna(False).astype(int) * 3
        penalita += banned
    
    score -= penalita.clip(0, 10) * 0.2
    
    # Applica il moltiplicatore ruolo
    score = score * peso_ruolo
    
    # Per attaccanti: limiti più alti per permettere differenziazione
    if ruolo in ['ATT', 'A']:
        return score.clip(0, 200)  # Limite più contenuto per debug
    elif ruolo in ['CEN', 'C']:
        return score.clip(0, 150)  # Limite più alto per centrocampisti top
    elif ruolo in ['DIF', 'D']:
        return score.clip(0, 120)  # Limite più alto per difensori top
    else:
        return score.clip(0, 100)
    
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
