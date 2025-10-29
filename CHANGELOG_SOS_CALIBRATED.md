# SOS Calibrated Pricing - Changelog

## Nuova Funzionalità: Pricing Calibrato su SOS Fanta 2025

### Descrizione
Aggiunto un nuovo modulo di pricing che usa i prezzi di **SOS Fanta 2025** come riferimento base e li calibra utilizzando **tutte le statistiche tecniche** disponibili da FPEDIA e FSTATS.

### File Coinvolti
- **Nuovo**: `src/fantacalcio/analyzers/sos_calibrated_pricing.py`
- **Modificato**: `main_workflow.py`

### Caratteristiche Principali

#### 1. Sistema di Scoring Completo
Il prezzo calibrato si basa su 4 categorie di punteggi:

- **Offensive Score**: Valuta la pericolosità offensiva
  - Gol (peso massimo per attaccanti)
  - Assist
  - xG (Expected Goals)
  - xA (Expected Assists)
  - Pesi diversi per ruolo

- **Defensive Score**: Valuta l'affidabilità difensiva
  - Porte inviolate (clean sheets)
  - Gol subiti (per portieri)
  - Rigori parati

- **Reliability Score**: Valuta l'affidabilità e continuità
  - Presenze (normalizzate su 38 partite)
  - Percentuale di partite da titolare
  - Minuti giocati
  - Penalità per cartellini

- **Technical Score**: Valuta la qualità tecnica tramite indici FSTATS
  - Per attaccanti: Shot_on_target, Offensive_actions, Attacking_area, ecc.
  - Per centrocampisti: Pass_leading_chances, Creativity, Verticalization, ecc.
  - Per difensori: Defense_solidity, Air_challenge, Set_piece_attack, ecc.
  - Per portieri: Defense_solidity, Pass_accuracy

#### 2. Calibrazione Intelligente
- **Con prezzo SOS disponibile**: Applica adjustment factor basato sul punteggio totale
  - Performance eccezionale: +40-80%
  - Performance ottima: +20-40%
  - Performance nella media: -10% a +10%
  - Performance scarsa: -50% a -20%
  
- **Bonus specifici**:
  - Gol ≥15: +30%
  - Gol ≥10: +20%
  - Gol ≥7: +10%
  - Assist ≥10: +15%
  - Assist ≥6: +8%

- **Senza prezzo SOS**: Stima basata solo sui punteggi con moltiplicatori per ruolo

#### 3. Matching Intelligente
- Estrazione automatica del cognome per matching con SOS Fanta
- Normalizzazione dei nomi (rimozione accenti, caratteri speciali)
- Match rate: ~57% (283/499 giocatori)

### Risultati

#### Statistiche Generali
- **Giocatori totali**: 499
- **Match con SOS**: 283 (57%)
- **Prezzo medio calibrato**: 27.6€
- **Correlazione Goals-Prezzo**: 0.625
- **Correlazione Score-Prezzo**: 0.671

#### Calibrazione per Ruolo
| Ruolo | SOS Medio | Calibrato Medio | Differenza Media |
|-------|-----------|-----------------|------------------|
| ATT   | 26.1€     | 34.9€           | +8.8€            |
| CEN   | 6.9€      | 6.2€            | -0.7€            |
| DIF   | 5.5€      | 4.5€            | -1.0€            |
| POR   | 10.0€     | 8.6€            | -1.4€            |

**Nota**: Gli attaccanti vengono valorizzati di più (+33%) per riflettere l'importanza di gol e assist.

#### Top 5 Aumenti di Prezzo
1. DAVID JONATHAN CHRISTIAN (ATT): 115€ → 200€ (+85€) - 16 gol, 4 assist
2. THURAM MARCUS (ATT): 138€ → 200€ (+62€) - 14 gol, 4 assist
3. KEAN MOISE (ATT): 140€ → 200€ (+60€) - 19 gol, 3 assist
4. LOOKMAN ADEMOLA (ATT): 40€ → 93€ (+53€) - 15 gol, 4 assist
5. CASTELLANOS TATY (ATT): 95€ → 135€ (+40€) - 10 gol, 3 assist

### Utilizzo

#### Modalità di Default (SOS Calibrato)
```bash
python main_workflow.py
```

#### Con Aggiornamento Dati
```bash
python main_workflow.py --update-data
```

#### Modalità Legacy (Market Pricing)
```bash
python main_workflow.py --no-sos-calibrated
```

#### Modalità Autonoma (Senza SOS)
```bash
python main_workflow.py --standalone
```

### Output
Il file generato è: `data/output/sos_calibrated_pricing.xlsx`

#### Colonne Principali
- `Prezzo_Calibrato`: Prezzo finale calibrato
- `Prezzo`: Prezzo SOS originale (se disponibile)
- `Differenza_vs_SOS`: Differenza tra calibrato e SOS
- `Total_Score`: Punteggio totale del giocatore
- `Offensive_Score`, `Defensive_Score`, `Reliability_Score`, `Technical_Score`
- `Categoria_Performance`: Fenomeno, Top Player, Eccellente, Buono, Nella Media, Sottotono, Scarso
- Tutte le statistiche originali da FPEDIA e FSTATS

### Vantaggi
1. ✅ **Più realistico**: Combina esperienza di mercato (SOS) con dati oggettivi
2. ✅ **Basato su statistiche**: Considera 19+ indici tecnici FSTATS
3. ✅ **Enfasi su pericolosità**: Giocatori con gol/assist sono valorizzati di più
4. ✅ **Affidabilità considerata**: Presenze e minuti contano
5. ✅ **Trasparente**: Ogni componente dello score è tracciabile

### Limitazioni
- Matching basato su cognome: alcuni giocatori potrebbero non essere matchati
- Giocatori senza prezzo SOS usano solo stima basata su score
- Richiede dati aggiornati da FPEDIA e FSTATS per essere accurato
