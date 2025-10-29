# Fantacalcio Analysis - Guida Rapida

## 🚀 Come Usare il Sistema

### Esecuzione Semplice

```bash
python main.py
```

Questo comando esegue automaticamente:
1. ✅ Verifica se i dati sono aggiornati (meno di 1 giorno)
2. ✅ Scarica dati da FPEDIA e FSTATS (solo se necessario)
3. ✅ Crea file di analisi `fpedia_analysis.xlsx` e `FSTATS_analysis.xlsx`
4. ✅ Calcola prezzi calibrati su SOS Fanta
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
- `data/SOS Fanta 2025_26.xlsx` - Prezzi di riferimento SOS Fanta
- `data/fpedia_analysis.xlsx` - Analisi FPEDIA (generato automaticamente)
- `data/FSTATS_analysis.xlsx` - Analisi FSTATS (generato automaticamente)

### Output
- `data/output/final_analysis.xlsx` - **FILE FINALE** con tutte le metriche e prezzi consigliati

### Dati Scaricati (automatici)
- `data/raw/_giocatori.csv` - Dati grezzi FPEDIA
- `data/raw/_players.csv` - Dati grezzi FSTATS

## 📊 Contenuto del File Finale

Il file `final_analysis.xlsx` contiene:

### Informazioni Base
- `Nome` - Nome del giocatore
- `Ruolo` - Ruolo (POR, DIF, CEN, ATT)
- `Squadra` - Squadra di appartenenza

### Prezzi
- `Prezzo_Calibrato` - **Prezzo consigliato calcolato**
- `Prezzo` - Prezzo SOS Fanta (riferimento)
- `Differenza_vs_SOS` - Differenza tra calibrato e SOS

### Scores Componenti
- `Total_Score` - Punteggio totale (0-100)
- `Offensive_Score` - Pericolosità offensiva (gol, assist, xG)
- `Defensive_Score` - Solidità difensiva (clean sheets, gol subiti)
- `Reliability_Score` - Affidabilità (presenze, minuti)
- `Technical_Score` - Qualità tecnica (indici FSTATS)

### Categoria
- `Categoria_Performance` - Fenomeno, Top Player, Eccellente, Buono, Nella Media, Sottotono, Scarso

### Statistiche Complete
- Tutte le statistiche FPEDIA (fantamedia, presenze, gol previsti, ecc.)
- Tutti i 19+ indici tecnici FSTATS
- Goals, assists, xG, xA, presenze, minuti, cartellini, ecc.

## 🎯 Sistema di Pricing

Il prezzo calibrato viene calcolato considerando:

1. **Baseline SOS Fanta** - Usa i prezzi SOS come riferimento
2. **Performance Offensiva** - Gol, assist, xG, xA (peso massimo per attaccanti)
3. **Solidità Difensiva** - Clean sheets, gol subiti (per portieri e difensori)
4. **Affidabilità** - Presenze, minuti giocati, continuità
5. **Qualità Tecnica** - 19+ indici FSTATS specializzati per ruolo

### Bonus Speciali
- Gol ≥15: +30%
- Gol ≥10: +20%
- Gol ≥7: +10%
- Assist ≥10: +15%
- Assist ≥6: +8%

## 📈 Esempi di Output

### Top Players con Maggiori Aumenti
```
DAVID J.C. (ATT)    SOS: 115€ → Calibrato: 200€ (+85€) | 16 gol, 4 assist
LOOKMAN (ATT)       SOS: 40€  → Calibrato: 93€  (+53€) | 15 gol, 4 assist
KRSTOVIC (ATT)      SOS: 55€  → Calibrato: 95€  (+40€) | 11 gol, 5 assist
```

### Best Value Players
Giocatori con alto score e prezzo contenuto - ideali per completare la rosa.

## 🔄 Aggiornamento Dati

Il sistema controlla automaticamente l'età dei dati:
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
Assicurati che `data/SOS Fanta 2025_26.xlsx` esista nella directory data.

### "ModuleNotFoundError"
Installa le dipendenze: `pip install -r requirements.txt`

### Dati non aggiornati
Usa `python main.py --force-update` per forzare il download.

## 📝 Note

- Il matching con SOS si basa sul cognome (es: "MARTIN AARON" → "MARTIN")
- Match rate tipico: ~40-60% dei giocatori
- Giocatori non matchati con SOS usano stima basata solo su statistiche
- Il file finale include TUTTI i giocatori (matchati e non)

## 🎉 Workflow Completo in Un Comando

```bash
python main.py
```

That's it! Il sistema fa tutto automaticamente.
