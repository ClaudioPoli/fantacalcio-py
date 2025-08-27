# Fantacalcio-PY

Fantacalcio-PY è un tool avanzato che aiuta gli utenti a prepararsi strategicamente per l'asta del fantacalcio, fornendo analisi dettagliate e prezzi massimi consigliati per ogni giocatore basati su statistiche reali e logiche specifiche per ruolo.

## 🎯 Funzionalità Principali

### 1. **Recupero Dati Multi-Source**

* **FPEDIA**: Statistiche qualitative e valutazioni esperte della stagione in corso
* **FSTATS**: Statistiche quantitative dettagliate della stagione precedente (gol, assist, presenze, indici tecnici)

### 2. **Perfect Excel Merger** 🆕

Il sistema include un **Perfect Excel Merger** che garantisce la fusione intelligente dei dati provenienti da FPEDIA e FSTATS con:

- **🎯 Copertura 100%**: Garantisce che tutti i giocatori del file più piccolo vengano matchati
- **🧠 Matching Intelligente**: Algoritmo avanzato che gestisce differenze nei formati dei nomi (COGNOME NOME vs Nome Cognome)
- **📊 Excel Strutturato**: Produce un file Excel con 5 fogli:
  - `FPEDIA_All`: Tutti i giocatori FPEDIA originali
  - `FSTATS_All`: Tutti i giocatori FSTATS originali
  - `Matched`: Giocatori matchati con qualità del match
  - `Unmatched`: Giocatori non matchati per identificare problemi
  - `Statistics`: Statistiche complete del processo

### 2. **Calcolo Prezzo Massimo Consigliato**

Il cuore del sistema è un algoritmo sofisticato che calcola il **"Prezzo Massimo Consigliato"** per ogni giocatore, utilizzando:

#### **🔥 Attaccanti (Budget: ATT_1=180 crediti)**

- **Focus su produttività offensiva**: Gol, assist, Expected Goals (xG)
- **Differenziazione statistica**: Fino a 16 fasce di prezzo diverse
- **Logica**: Premia i finalizzatori (Osimhen, Vlahović) e i assist-man (Lookman, Kvaratskhelia)

#### **⚡ Centrocampisti (Budget: CEN_1=50 crediti)**

- **Focus su contributi totali**: Gol + assist per partita, fantamedia, presenza
- **Differenziazione per qualità**: Premia i centrocampisti più incisivi offensivamente
- **Logica**: Valorizza chi fa la differenza (Barella, Pellegrini, Zielinski)

#### **🛡️ Difensori (Budget: DIF_1=30 crediti)**

- **Focus ULTRA-OFFENSIVO**: Priorità assoluta a gol e assist dei difensori
- **Statistiche chiave**: Contributi offensivi, cross, presenza in area avversaria
- **Logica**: I difensori che segnano/assistono valgono oro (Dimarco, Dumfries, Zortea)

#### **🥅 Portieri (Budget: POR_1=28 crediti)**

- **Focus su affidabilità**: Clean sheets, parate, titolarità
- **Logica**: Stabilità e rendimento costante

### 3. **Sistema di Fasce di Prezzo**

Il sistema rispetta rigorosamente le fasce di budget configurabili:

```python
# Fasce Difensori
DIF_1 = 30  # Elite offensivi (Dimarco, Dumfries)
DIF_2 = 20  # Buoni contributi (Zortea, Bellanova)
DIF_3 = 10  # Discreti
DIF_4 = 5   # Budget players

# Fasce Centrocampisti  
CEN_1 = 50  # Top quality (Barella, top stranieri)
CEN_2 = 30  # Ottimi (Pellegrini, Zielinski)
CEN_3 = 15  # Buoni

# Fasce Attaccanti
ATT_1 = 180 # Fenomeni (Osimhen, Vlahović)
ATT_2 = 70  # Top tier (Lookman, Kvaratskhelia)
ATT_3 = 20  # Discreti
```

### 4. **Indici di Convenienza**

- **Convenienza Standard**: Rapporto qualità/prezzo base
- **Convenienza Potenziale**: Considera il potenziale di crescita
- **Analisi Comparativa**: Identifica occasioni e sopravvalutazioni

## 🚀 Come Funziona l'Algoritmo

### **Metodologia di Calcolo**

1. **Raccolta Multi-Parametrica**: Ogni giocatore viene valutato su 20+ parametri statistici
2. **Peso Specifico per Ruolo**: Ogni ruolo ha logiche di valutazione ottimizzate
3. **Normalizzazione e Score**: I dati vengono normalizzati e combinati in uno score complessivo
4. **Interpolazione Intelligente**: Lo score viene mappato sulle fasce di prezzo tramite interpolazione quasi-lineare
5. **Bonus Statistici**: Bonus/malus basati su eccellenze o carenze specifiche

### **Esempio Pratico - Difensori**

```
Dimarco: 4 gol + 7 assist = 0.333 contributi/partita → 30 crediti (DIF_1)
Dumfries: 7 gol + 2 assist = 0.310 contributi/partita → 30 crediti (DIF_1)  
Zortea: 6 gol + 2 assist = 0.229 contributi/partita → 28 crediti (DIF_2)
Bastoni: 1 gol + 3 assist = 0.121 contributi/partita → 20 crediti (DIF_3)
```

### **Vantaggi del Sistema**

- ✅ **Oggettività**: Basato su dati reali, non opinioni
- ✅ **Specificità**: Logiche ottimizzate per ogni ruolo
- ✅ **Differenziazione**: Identifica le sfumature tra giocatori simili
- ✅ **Budget-Aware**: Rispetta i vincoli economici reali
- ✅ **Statistiche Avanzate**: Usa Expected Goals, indici tecnici, contributi per partita

## 🧮 Calcoli Dettagliati per Fonte

### **📊 FPEDIA - Analisi Qualitativa**

#### **Calcolo Convenienza FPEDIA**

```python
# Formula base
Convenienza = (Fantamedia_Corrente * Peso_Partite + Appetibilità) / Quotazione_Mantra

Dove:
- Fantamedia_Corrente: Media voto stagione attuale
- Peso_Partite: Fattore di correzione basato su partite giocate
- Appetibilità: Indice qualitativo di desiderabilità
- Quotazione_Mantra: Prezzo base del giocatore
```

**Esempio Pratico:**

```
Lautaro Martinez:
- Fantamedia: 7.2
- Partite giocate: 32/38 (84% → peso 0.95)
- Appetibilità: 8.5
- Quotazione: 42
→ Convenienza = (7.2 * 0.95 + 8.5) / 42 = 0.364
```

#### **Calcolo Convenienza Potenziale FPEDIA**

```python
# Considera il potenziale di crescita
Convenienza_Potenziale = Convenienza_Base * (1 + Fattore_Crescita)

Fattore_Crescita basato su:
- Età del giocatore (giovani = bonus)
- Trend della fantamedia
- Cambio squadra/ruolo
- Infortuni passati (recovery potential)
```

#### **Prezzo Massimo Consigliato FPEDIA**

```python
# Sistema a score combinato
Score_FPEDIA = (
    Fantamedia_Normalizzata * 0.4 +
    Appetibilità_Normalizzata * 0.3 +
    Partite_Giocate_Normalizzate * 0.2 +
    Bonus_Ruolo * 0.1
)

# Mappatura su fasce di prezzo
if Ruolo == "ATT":
    Prezzo = interpolazione(Score, range=[1, ATT_1=180])
elif Ruolo == "CEN":
    Prezzo = interpolazione(Score, range=[1, CEN_1=50])
# etc...
```

### **⚡ FSTATS - Analisi Quantitativa**

#### **Calcolo Convenienza FSTATS**

```python
# Formula performance-driven
Convenienza = Performance_Score / Quotazione_Base

Performance_Score = (
    Gol_per_Partita * 3.0 +
    Assist_per_Partita * 2.0 +
    Expected_Goals_per_Partita * 1.5 +
    Indice_Tecnico_Medio * 0.1 +
    Bonus_Titolarità
)
```

**Esempio Pratico - Difensore:**

```
Dimarco:
- Gol/partita: 0.12 (4 gol in 33 partite)
- Assist/partita: 0.21 (7 assist in 33 partite)
- Titolarità: 70min/partita (bonus 1.2)
- Cross accuracy: 78.4 (bonus 0.8)
→ Performance_Score = (0.12*3 + 0.21*2 + 1.2 + 0.8) = 2.78
→ Convenienza = 2.78 / Quotazione_Base
```

#### **Calcolo Convenienza Potenziale FSTATS**

```python
# Basata su trend statistici
Trend_Gol = (Gol_Ultima_10_Partite - Gol_Prime_10_Partite) / 10
Trend_Assist = (Assist_Ultimi - Assist_Primi) / 10
Trend_Minuti = Evoluzione_Titolarità

Convenienza_Potenziale = Convenienza_Base * (1 + Trend_Combinato)
```

#### **Prezzo Massimo Consigliato FSTATS - Dettaglio per Ruolo**

##### **🛡️ Difensori (Focus Ultra-Offensivo)**

```python
Score_Base = Statistiche_Difensive * 0.2 + Passaggi * 0.1

# BONUS MASSIVI per contributi offensivi
if Gol_Assist_per_Partita >= 0.30:  # Elite (Dimarco, Dumfries)
    Bonus += 25
elif Gol_Assist_per_Partita >= 0.25:  # Excellent
    Bonus += 20
elif Gol_Assist_per_Partita >= 0.20:  # Very Good (Zortea)
    Bonus += 17

# Bonus aggiuntivi
Bonus_Gol = min(Gol * 2, 8)  # Max 8 bonus per gol
Bonus_Assist = min(Assist * 1.5, 6)  # Max 6 bonus per assist
Bonus_Cross = Cross_Accuracy > 85 ? 5 : 0
Bonus_AttackArea = Attack_Area_Index > 70 ? 4 : 0

Score_Finale = Score_Base + Bonus_Totali
Prezzo = interpolazione_quasi_lineare(Score_Finale, [1, DIF_1=30])
```

##### **⚡ Centrocampisti (Focus Contributi Totali)**

```python
Score_Base = (
    Fantamedia_Predicted * 0.3 +
    Presenze_Normalizzate * 0.2 +
    Indici_Tecnici * 0.2
)

# Bonus per contributi offensivi
Contributi_Totali = (Gol + Assist) / Presenze
if Contributi_Totali >= 0.55:  # Top (Orsolini level)
    Bonus += 4
elif Contributi_Totali >= 0.45:  # Excellent
    Bonus += 3

# Bonus qualità
if Fantamedia >= 8.0:  # Elite (Tramoni level)
    Bonus += 3
elif Fantamedia >= 7.5:  # Excellent
    Bonus += 2

Score_Finale = Score_Base + Bonus_Moderati
Prezzo = interpolazione_quasi_lineare(Score_Finale, [1, CEN_1=50])
```

##### **🔥 Attaccanti (Focus Produttività)**

```python
Score_Base = (
    Expected_Goals_per_Partita * 0.4 +
    Gol_per_Partita * 0.3 +
    Assist_per_Partita * 0.2 +
    Titolarità * 0.1
)

# Sistema di amplificazione per differenziazione
if Gol_per_Partita >= 0.8:  # Fenomeni (Osimhen level)
    Moltiplicatore = 1.5
elif Gol_per_Partita >= 0.6:  # Top tier
    Moltiplicatore = 1.3
elif Gol_per_Partita >= 0.4:  # Buoni
    Moltiplicatore = 1.1

# Bonus finisher vs assist-man
Bonus_Finisher = Gol > Assist ? Gol * 2 : 0
Bonus_AssistMan = Assist > Gol ? Assist * 1.5 : 0

Score_Finale = (Score_Base * Moltiplicatore) + Bonus_Specializzazione
Prezzo = interpolazione_convessa(Score_Finale, [1, ATT_1=180])
```

### **🔄 Differenze Chiave tra FPEDIA e FSTATS**

| Aspetto                      | FPEDIA                          | FSTATS                             |
| ---------------------------- | ------------------------------- | ---------------------------------- |
| **Fonte Dati**         | Valutazioni esperte qualitative | Statistiche quantitative pure      |
| **Convenienza Base**   | Fantamedia + Appetibilità      | Performance score da statistiche   |
| **Prezzo Consigliato** | Score qualitativo               | Score statistico con bonus ruolo   |
| **Punti di Forza**     | Cattura potenziale e contesto   | Oggettività e precisione numerica |
| **Ideale Per**         | Scoprire talenti emergenti      | Validare performance consolidate   |

## 📊 Output Generati

Al termine dell'esecuzione, vengono creati due file Excel dettagliati:

### **📈 fpedia_analysis.xlsx**

- Analisi basata su valutazioni qualitative FPEDIA
- Colonna **"Prezzo Massimo Consigliato"** per ogni giocatore
- Indici di convenienza standard e potenziale
- Ordinamento per convenienza

### **📈 FSTATS_analysis.xlsx**

- Analisi basata su statistiche quantitative FSTATS
- Colonna **"Prezzo Massimo Consigliato"** ottimizzata per ruolo
- Dati dettagliati: gol, assist, presenze, indici tecnici
- Focus su rendimento statistico reale

### **Colonne Chiave negli Output**

- **Nome**: Nome del giocatore
- **Ruolo**: Posizione (ATT, CEN, DIF, POR)
- **Squadra**: Club di appartenenza
- **Prezzo Massimo Consigliato**: 🎯 **Il valore calcolato dal sistema**
- **Convenienza**: Rapporto qualità/prezzo
- **Convenienza Potenziale**: Include fattori di crescita
- **Statistiche**: Gol, assist, presenze, fantamedia, indici tecnici

### **📋 Come Interpretare i Risultati**

#### **📊 Valori di Convenienza**

```
Convenienza > 1.0  : 🟢 OTTIMO AFFARE (compra subito!)
Convenienza 0.7-1.0: 🟡 BUON ACQUISTO (valuta)
Convenienza 0.5-0.7: 🟠 PREZZO GIUSTO (se serve)
Convenienza < 0.5  : 🔴 SOPRAVVALUTATO (evita)
```

#### **💰 Interpretazione Prezzo Massimo Consigliato**

- **Valore Assoluto**: Non superare mai questo limite in asta
- **Confronto Listini**: Se il prezzo di listino è molto più basso → value pick
- **Strategia**: Usa come base per rilanci e contrattazioni

#### **🎯 Esempi Pratici di Lettura**

```
Giocatore X:
- Prezzo Listino: 25 crediti
- Prezzo Massimo Consigliato: 30 crediti
- Convenienza: 1.2
→ INTERPRETAZIONE: Ottimo affare, puoi arrivare fino a 30 crediti

Giocatore Y:
- Prezzo Listino: 40 crediti  
- Prezzo Massimo Consigliato: 28 crediti
- Convenienza: 0.4
→ INTERPRETAZIONE: Sopravvalutato, evita l'acquisto
```

## Prerequisiti

Per utilizzare questo progetto, è necessario avere installato **Python 3.10** o superiore e **Poetry** per la gestione delle dipendenze.

## Installazione

1. **Clonare la repository (se non già fatto)**:

   ```bash
   git clone <url_della_repository>
   cd fantacalcio-py-main
   ```
2. **Installare le dipendenze**:
   Questo progetto utilizza `poetry` per gestire le dipendenze. Per installarle, eseguire il seguente comando dalla root del progetto:

   ```bash
   poetry install
   ```

   Questo comando creerà un ambiente virtuale e installerà tutte le librerie necessarie specificate nel file `pyproject.toml`.

## Configurazione

Il progetto richiede delle credenziali per accedere a `FSTATS`. Queste credenziali vanno inserite in un file `.env` nella root del progetto.

Il file `config.py` contiene altre configurazioni, come gli URL per lo scraping e i percorsi dei file di output. Non dovrebbe essere necessario modificarlo per il funzionamento base.

## Avvio del Progetto

Per avviare l'analisi completa, eseguire lo script `main.py` utilizzando `poetry`.

```bash
poetry run python main.py
```

Lo script eseguirà tutti i passaggi (recupero, elaborazione, calcolo e salvataggio).

## 🎮 Strategia per l'Asta

### **Come Usare i Risultati**

1. **Preparazione Pre-Asta**:

   - Apri i file Excel generati
   - Filtra per ruolo di interesse
   - Identifica i "value picks" (alta convenienza)
2. **Durante l'Asta**:

   - Usa il "Prezzo Massimo Consigliato" come limite di spesa
   - Punta sui difensori offensivi (massimo ROI)
   - Non superare mai il prezzo suggerito
3. **Filosofia di Acquisto**:

   - **Difensori**: Priorità assoluta a chi fa gol/assist
   - **Centrocampisti**: Cerca i contributi offensivi
   - **Attaccanti**: Bilancia titolarità e produttività
   - **Portieri**: Punta su affidabilità e clean sheets

### **📋 Esempi di Liste Consigliate**

#### **🔥 Lista Difensori Offensivi** (Budget: 75 crediti)

```
Dimarco (30) + Zortea (28) + Bellanova (22) = 80 crediti
Dumfries (30) + Cambiaso (17) + Gosens (23) = 70 crediti  
```

#### **⚡ Lista Centrocampisti Bilanciata** (Budget: 110 crediti)

```
Barella (45) + Pellegrini (35) + Zielinski (30) = 110 crediti
```

## 💡 Pro Tips

- **🎯 Focus sui Ruoli Giusti**: I difensori offensivi fanno la differenza più degli attaccanti costosi
- **📊 Usa le Statistiche**: Un difensore con 0.3 gol+assist/partita vale oro
- **💰 Rispetta il Budget**: Il sistema è calibrato sulle fasce reali di spesa
- **🔍 Cerca i Value Picks**: Giocatori con alta convenienza ma prezzo contenuto
- **📈 Monitora le Presenze**: Titolarità = consistenza di rendimento

## ⚠️ Disclaimer

- Se perdete il fanta non è colpa mia, io ci so arrivato secondo co sta roba. E l'anno dopo primo.
- Il tool utilizza i csv prodotti da fpedia, tutti i dati processati sono loro, dato che fantagazzetta ha deciso di tagliare i dataset open.
- I prezzi sono suggerimenti basati su analisi statistiche, non certezze assolute.

*Refactor del codice di cttynul con algoritmi avanzati di pricing*

## � Perfect Excel Merger

Per utilizzare il **Perfect Excel Merger** che garantisce copertura 100% del file più piccolo:

```bash
poetry run python perfect_excel_merger.py
```

### **Output del Perfect Merger**

Il comando genera `perfect_merged_analysis.xlsx` con 5 fogli:

1. **Unified_Analysis** � - **Analisi ottimizzata** con:
   - Tutti i giocatori matchati (499 righe con copertura 100% FSTATS)
   - **Colonne FPEDIA essenziali**: Convenienza, Prezzo Massimo Consigliato, Skills, Trend, Gol/Assist previsti, ecc.
   - **Solo 3 colonne FSTATS**: Convenienza, Convenienza Potenziale, Prezzo Massimo Consigliato
   - **21 colonne totali** (ottimizzato per analisi)

2. **Complete_Merge** 🆕 - **Merge completo** con:
   - **TUTTI i giocatori** di entrambe le fonti (513 righe totali)
   - **TUTTE le colonne** FPEDIA (28 colonne) + **TUTTE le colonne** FSTATS (68 colonne)
   - **102 colonne totali** con dati completi
   - Status di matching: `MATCHED`, `FPEDIA_ONLY`, `FSTATS_ONLY`
   - Score e qualità del matching

3. **Matched** - 499 giocatori matchati con score di qualità
4. **Unmatched** - Solo giocatori non matchati con fonte di provenienza
5. **Statistics** - Statistiche complete del processo di matching

### **Caratteristiche del Perfect Merger**

- ✅ **Copertura 100% garantita** del file più piccolo (FSTATS)
- 🧠 **Matching intelligente** con gestione di varianti nomi
- 📊 **Qualità verificata** - Score medio 0.991/1.0
- 🔍 **Identificazione problemi** - Mostra esattamente cosa non matcha
- 🎯 **Analisi unificata** - Foglio ottimizzato per uso quotidiano (21 colonne)
- 🔗 **Merge completo** - Foglio con TUTTI i dati per analisi approfondite (102 colonne)
- 📋 **Generazione automatica** - Integrato nel `main.py`

## �🚧 WIP (Work in Progress)

- [ ] **Calcolo Prezzo Massimo Consigliato (Upgrade)**
- [X] **Differenziazione per Ruolo**
- [X] **Algoritmi Statistici Avanzati**
- [X] **Sistema di Fasce Budget**
- [X] **Perfect Excel Merger con copertura 100%**
- [ ] **Formazione Consigliata Automatica**
- [ ] **Simulatore di Asta**
- [ ] **Frontend Web Interattivo**
- [ ] **API REST per integrazione**
- [ ] **Machine Learning per previsioni**

## 🏆 Success Stories

> *"Secondo posto nel 2023, primo nel 2024. I dati non mentono!"* - Sviluppatore

### **📈 Risultati Verificati**

- **Difensori Target Identificati**: Dimarco, Dumfries, Zortea (tutti con contributi 0.2+ gol+assist/partita)
- **Value Picks Scoperti**: Difensori a 15-20 crediti con statistiche offensive sorprendenti
- **Budget Ottimizzato**: Sistema di fasce che massimizza il ROI per ruolo

## Stars

[![Star History Chart](https://api.star-history.com/svg?repos=piopy/fantacalcio-py&type=Date)](https://www.star-history.com/#piopy/fantacalcio-py&Date)
