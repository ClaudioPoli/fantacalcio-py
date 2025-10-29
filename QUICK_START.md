# Fantacalcio Analysis - Guida Rapida

## 🚀 Come Usare il Sistema (Solo FSTATS)

### Esecuzione Semplice

```bash
python main.py
```

Questo comando esegue automaticamente:
1. ✅ Verifica se i dati FSTATS sono aggiornati (meno di 1 giorno)
2. ✅ Scarica dati da FSTATS (solo se necessario)
3. ✅ Crea file di analisi `FSTATS_analysis.xlsx`
4. ✅ Calcola prezzi basati su statistiche FSTATS
5. ✅ Genera output finale con tutte le metriche

### Opzioni Disponibili

```bash
# Forza l'aggiornamento dei dati (anche se freschi)
python main.py --force-update

# Usa una directory dati personalizzata
python main.py --data-dir /percorso/ai/dati
```

## 📁 Struttura File

### Input
- `data/SOS Fanta 2025_26.xlsx` - Prezzi di riferimento SOS Fanta (opzionale)
- `data/FSTATS_analysis.xlsx` - Analisi FSTATS (generato automaticamente)

### Output
- `data/output/final_analysis.xlsx` - **FILE FINALE** con tutte le metriche FSTATS e prezzi consigliati

### Dati Scaricati (automatici)
- `data/raw/_players.csv` - Dati grezzi FSTATS

## 📊 Contenuto del File Finale

Il file `final_analysis.xlsx` contiene **89 colonne** basate esclusivamente su dati FSTATS:

### Informazioni Base
- `Nome` - Nome del giocatore
- `Ruolo` - Ruolo (P, D, C, A)
- `Squadra` - Squadra di appartenenza

### Prezzi
- `Prezzo_Calibrato` - **Prezzo consigliato calcolato**
- `Prezzo` - Prezzo SOS Fanta (riferimento, se disponibile)
- `Differenza_vs_SOS` - Differenza tra calibrato e SOS

### Scores Componenti (basati su FSTATS)
- `Total_Score` - Punteggio totale (0-100)
- `Offensive_Score` - Pericolosità offensiva (gol, assist, xG)
- `Defensive_Score` - Solidità difensiva (clean sheets, gol subiti)
- `Reliability_Score` - Affidabilità (presenze, minuti)
- `Technical_Score` - Qualità tecnica (19 indici FSTATS)

### Categoria
- `Categoria_Performance` - Fenomeno, Top Player, Eccellente, Buono, Nella Media, Sottotono, Scarso

### Statistiche FSTATS Complete
- **Statistiche di base**: goals, assists, presences, avg, fanta_avg, minuti
- **xG e xA**: xgFromOpenPlays, xA, xG/90min
- **Portieri**: gkCleanSheets, gkConcededGoals, gkPenaltiesSaved
- **Cartellini**: yellowCards, redCards
- **19 Indici Tecnici Specializzati**:
  - Offensive: Shot_on_target_Index, Shot_on_goal_Index, Offensive_actions_Index, Attacking_area_Index
  - Creativity: Pass_leading_chances_Index, Pass_accuracy_Index, Cross_accuracy_Index
  - Defensive: Defense_solidity_Index, Air_challenge_offensive_Index
  - E molti altri specifici per ruolo

## 🎯 Sistema di Pricing (Basato su FSTATS)

Il prezzo viene calcolato considerando:

1. **Baseline SOS Fanta** - Usa i prezzi SOS come riferimento (se disponibile)
2. **Performance Offensiva** - Gol, assist, xG, xA (peso massimo per attaccanti)
3. **Solidità Difensiva** - Clean sheets, gol subiti (per portieri e difensori)
4. **Affidabilità** - Presenze, minuti giocati, continuità
5. **Qualità Tecnica** - 19 indici FSTATS specializzati per ruolo

### Statistiche Considerate per Ruolo

#### Portieri (P)
- Clean sheets, gol subiti, rigori parati
- Defense_solidity_Index, Pass_accuracy_Index
- Presenze, minuti giocati

#### Difensori (D)
- Clean sheets, gol, assist
- Defense_solidity_Index, Air_challenge_offensive_Index, Set_piece_attack_Index
- Presenze, minuti giocati

#### Centrocampisti (C)
- Gol, assist, xG, xA
- Pass_leading_chances_Index, Offensive_actions_Index, Pass_accuracy_Index
- Creatività, verticalizzazione, presenza offensiva

#### Attaccanti (A)
- Gol, assist, xG, xA (peso massimo)
- Shot_on_target_Index, Shot_on_goal_Index, Offensive_actions_Index
- Efficienza sotto porta, pericolosità in area

### Bonus Speciali
- Gol ≥15: +30%
- Gol ≥10: +20%
- Gol ≥7: +10%
- Assist ≥10: +15%
- Assist ≥6: +8%

## 📈 Esempi di Output

### Top Players con Maggiori Aumenti
```
OKEREKE (A)     SOS: 115€ → Calibrato: 138€ (+23€) | 11 gol, 5 assist
BATURINA (C)    SOS: 16€  → Calibrato: 19€  (+3€)  | 4 gol, 5 assist
```

### Best Value Players
Giocatori con alto score e prezzo contenuto - ideali per completare la rosa.

## 🔄 Aggiornamento Dati

Il sistema controlla automaticamente l'età dei dati FSTATS:
- **< 1 giorno**: Usa dati esistenti (veloce)
- **≥ 1 giorno**: Scarica dati aggiornati automaticamente

Per forzare il download:
```bash
python main.py --force-update
```

## ⚙️ Requisiti

```bash
pip install pandas openpyxl beautifulsoup4 requests loguru tqdm python-dotenv
```

O con Poetry:
```bash
poetry install
```

## 🆘 Problemi Comuni

### "File SOS non trovato"
Il sistema funziona anche senza SOS Fanta. I prezzi saranno calcolati solo su statistiche FSTATS.

### "ModuleNotFoundError"
Installa le dipendenze: `pip install -r requirements.txt`

### Dati non aggiornati
Usa `python main.py --force-update` per forzare il download.

## 📝 Note

- **Solo FSTATS**: Il sistema usa esclusivamente dati FSTATS per massima precisione
- **19 indici tecnici**: Ogni giocatore è valutato con indici specifici per il suo ruolo
- **Bonus per performance**: Gol e assist aumentano significativamente il prezzo
- **SOS opzionale**: Se disponibile, viene usato come baseline, altrimenti si basa solo su statistiche
- Il file finale include TUTTI i giocatori (499 totali)

## 🎉 Workflow Completo in Un Comando

```bash
python main.py
```

That's it! Il sistema scarica FSTATS, analizza ogni giocatore e calcola prezzi basati su statistiche reali.
