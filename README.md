# 🏆 Fantacalcio Analysis System

Sistema completo per l'analisi dei giocatori di fantacalcio basato esclusivamente su **statistiche FSTATS** con calcolo prezzi calibrati su **SOS Fanta 2025**.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Caratteristiche Principali

### 🚀 **Un Solo Comando - Tutto Automatico (Solo FSTATS)**
```bash
python main.py
```
- Verifica automatica aggiornamento dati FSTATS
- Scarica dati FSTATS (solo se necessario)
- Crea file di analisi completo
- Calcola prezzi basati su **19 indici tecnici FSTATS**
- Genera output finale con tutte le metriche

### 💰 **Pricing Basato su Statistiche Reali**
- Usa **statistiche FSTATS complete** per ogni giocatore
- Calibra su **SOS Fanta 2025** come baseline (opzionale)
- Enfatizza **pericolosità offensiva** (gol, assist, xG)
- Considera **affidabilità** (presenze, minuti)
- Bonus per performance eccezionali

### 📊 **Analisi Multi-dimensionale (19+ Indici FSTATS)**
- **Offensive Score**: Gol, assist, xG, xA, tiri in porta
- **Defensive Score**: Clean sheets, gol subiti (portieri/difensori)
- **Reliability Score**: Presenze, minuti, continuità
- **Technical Score**: 19 indici FSTATS specializzati per ruolo

### 🔍 **Categorizzazione Assoluta**
- **Top Player**: Performance eccezionali (>15.0 punti) - 3.3% dei giocatori
- **Eccellente**: Performance molto buone (12.0-15.0) - 8.2%
- **Buono**: Performance solide (8.0-12.0) - 24.2%  
- **Nella Media**: Performance standard (5.0-8.0) - 22.6%
- **Sottotono**: Performance insufficienti (2.0-5.0) - 20.3%
- **Scarso**: Performance molto basse (<2.0) - 21.4%

## 📁 Struttura del Progetto

```
fantacalcio-py/
├── 📂 src/fantacalcio/           # Core package
│   ├── 📂 analyzers/             # Moduli di analisi
│   │   ├── sos_calibrated_pricing.py # 🎯 Pricing calibrato SOS
│   │   ├── standalone_pricing.py     # Pricing autonomo
│   │   └── market_pricing.py         # [Legacy] Market pricing
│   ├── 📂 data/                  # Gestione dati
│   │   ├── processor.py          # Elaborazione FSTATS
│   │   └── retriever.py          # Download dati FSTATS
│   └── 📂 utils/                 # Utilities
├── 📂 data/                      # Dati e analisi
│   ├── FSTATS_analysis.xlsx      # 📊 Analisi FSTATS (auto-generato)
│   ├── SOS Fanta 2025_26.xlsx    # 💰 Prezzi riferimento SOS (opzionale)
│   ├── 📂 output/                # Output finale
│   │   └── final_analysis.xlsx   # 🎯 FILE FINALE (89 colonne FSTATS)
│   └── 📂 raw/                   # Dati grezzi FSTATS scaricati
├── main.py                       # 🚀 Script principale (solo FSTATS)
├── QUICK_START.md                # 📖 Guida rapida
└── README.md                     # Documentazione
```

## 🚀 Installazione e Setup

### Prerequisiti
- **Python 3.8+**
- **Poetry** (raccomandato) o pip

### Setup Rapido
```bash
# Clona il repository
git clone https://github.com/ClaudioPoli/fantacalcio-py.git
cd fantacalcio-py

# Installa con Poetry (raccomandato)
poetry install
poetry shell

# OPPURE con pip
pip install -r requirements.txt
```

## 💻 Utilizzo

### 🚀 **Quick Start - Un Solo Comando (Solo FSTATS)**
```bash
python main.py
```

Questo comando esegue **automaticamente**:
1. ✅ Verifica se i dati FSTATS sono aggiornati (< 1 giorno)
2. ✅ Scarica dati FSTATS (solo se necessario)
3. ✅ Crea `FSTATS_analysis.xlsx` con 499 giocatori
4. ✅ Calcola prezzi basati su 19 indici tecnici FSTATS
5. ✅ Genera `data/output/final_analysis.xlsx` con **89 colonne di metriche**

### ⚙️ **Opzioni Avanzate**
```bash
# Forza download anche se dati freschi
python main.py --force-update

# Directory dati personalizzata
python main.py --data-dir /percorso/custom

# Help completo
python main.py --help
```

### 📖 **Guida Completa**
Vedi [QUICK_START.md](QUICK_START.md) per la guida dettagliata.

## 📊 Output e Risultati

### File Generati
1. **`data/FSTATS_analysis.xlsx`**: Analisi completa FSTATS con 499 giocatori
2. **`data/output/final_analysis.xlsx`**: 🎯 **FILE FINALE** con 89 colonne

### Colonne nel File Finale (Solo FSTATS)
Il file `final_analysis.xlsx` contiene **89 colonne** con dati FSTATS:

#### Informazioni Base
- `Nome`, `Ruolo`, `Squadra`

#### Prezzi e Valutazione
- `Prezzo_Calibrato` - **Prezzo consigliato finale**
- `Prezzo` - Prezzo SOS Fanta (riferimento, se disponibile)
- `Differenza_vs_SOS` - Scostamento dal SOS
- `Categoria_Performance` - Fenomeno, Top Player, Eccellente, Buono, Nella Media, Sottotono, Scarso

#### Scores Componenti (Basati su FSTATS)
- `Total_Score` - Punteggio totale (0-100)
- `Offensive_Score` - Pericolosità offensiva
- `Defensive_Score` - Solidità difensiva  
- `Reliability_Score` - Affidabilità e continuità
- `Technical_Score` - Qualità tecnica (19 indici FSTATS)

#### Statistiche FSTATS Complete (89 colonne totali)
- **Base**: goals, assists, presences, avg, fanta_avg, minutes
- **xG/xA**: xgFromOpenPlays, xA, xG/90min, xA/90min
- **Portieri**: gkCleanSheets, gkConcededGoals, gkPenaltiesSaved
- **Cartellini**: yellowCards, redCards, penalties
- **19 Indici Tecnici**: Shot_on_target_Index, Defense_solidity_Index, Pass_leading_chances_Index, ecc.

### File Generati
1. **`standalone_pricing_analysis.xlsx`**: 🎯 **Risultati finali autonomi**
2. **`perfect_merged_analysis.xlsx`**: Input con dati FPEDIA+FSTATS unificati

### Colonne Chiave nel File Finale
| Colonna | Descrizione |
|---------|-------------|
| `Performance_Score` | Punteggio performance autonomo (0-20) |
| `Prezzo_Consigliato` | **Prezzo calcolato autonomamente** |
| `Categoria` | **Categorizzazione assoluta** |
| `19 Indici FSTATS` | FSTATS_Shot_on_target_Index, FSTATS_goals, etc. |

## 🧠 Come Funziona l'Algoritmo Autonomo

### 1. **Calcolo Performance Score**
```python
# Combina 19 indici FSTATS con pesi specifici per ruolo
for indice in indici_tecnici[ruolo]:
    valore_normalizzato = normalizza_scala(valore_grezzo)
    score += valore_normalizzato × peso_ruolo[indice]
```

### 2. **Pricing Completamente Autonomo**
- **Portieri**: `performance × 2.5` + bonus/malus
- **Difensori**: `performance × 3.0` + aggiustamenti ruolo
- **Centrocampisti**: `performance × 3.5` + creatività
- **Attaccanti**: `performance × 4.0` + bonus gol/assist

### 3. **Normalizzazione Intelligente**
- **Indici FSTATS (0-100)**: `/10` → scala 0-10
- **Goals/Assists**: Diretti con cap a 20
- **Presenze**: `/38 × 10` (normalizzato su Serie A)
- **FantaIndex**: `/10` per uniformità

## 🏆 Esempi di Risultati Autonomi

### Top Player per Ruolo
```
🥇 ATTACCANTI:
   • KEAN MOISE - Performance: 20.0, Prezzo: 112€
   • ESPOSITO F. PIO - Performance: 19.1, Prezzo: 107€
   • LOOKMAN ADEMOLA - Performance: 19.1, Prezzo: 107€

🥈 CENTROCAMPISTI:
   • DE BRUYNE KEVIN - Performance: 15.0, Prezzo: 58€
   • MODRIC LUKA - Performance: 14.7, Prezzo: 57€
   • CALHANOGLU HAKAN - Performance: 14.5, Prezzo: 56€
```

### Migliori Occasioni per Fascia
```
💰 FASCIA ALTA (15-30€):
   • BISSECK Y. (DIF) - Perf: 10.0, Prezzo: 30€
   • ROMAGNOLI A. (DIF) - Perf: 9.6, Prezzo: 29€
   
🎯 FASCIA MEDIA (5-15€):
   Perfetti per completare la rosa con giocatori affidabili
```

## 🔧 Configurazione Avanzata

Il file `src/fantacalcio/analyzers/standalone_pricing.py` permette di personalizzare:

```python
# Pesi tecnici per ruolo
technical_weights = {
    'ATT': {
        'FSTATS_Shot_on_target_Index': 4.0,
        'FSTATS_goals': 4.5,
        # ...
    }
}

# Moltiplicatori di prezzo base
price_multipliers = {
    'POR': 2.5,  # Portieri più contenuti
    'DIF': 3.0,  # Difensori medi
    'CEN': 3.5,  # Centrocampisti vari
    'ATT': 4.0   # Attaccanti premium
}
```

## 📈 Statistiche Attuali v3.0

- **513 giocatori** analizzati autonomamente
- **Performance media**: 6.31/20
- **Prezzo medio**: 21.9€
- **17 Top Player** (3.3%) con performance >15
- **42 Eccellenti** (8.2%) con performance 12-15
- **Zero dipendenze** da dati esterni

## 🤝 Contributi

1. Fork del progetto
2. Crea il tuo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add: Amazing feature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📜 Licenza

Distribuito sotto **Licenza MIT**. Vedi [LICENSE](LICENSE) per dettagli.

## 📬 Contatti

**Claudio Poli** - [@ClaudioPoli](https://github.com/ClaudioPoli)

**Link Progetto**: [https://github.com/ClaudioPoli/fantacalcio-py](https://github.com/ClaudioPoli/fantacalcio-py)

---

<div align="center">
  <strong>🧮 Sistema 100% Autonomo - Zero Dipendenze Esterne! 🧮</strong><br>
  <em>⚽ Buona fortuna con il tuo fantacalcio autonomo! ⚽</em>
</div>
