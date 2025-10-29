# 🏆 Fantacalcio Analysis System - Autonomous Edition

Un sistema **completamente autonomo** per l'analisi dei giocatori di fantacalcio che calcola prezzi consigliati basandosi esclusivamente su **19 indici tecnici specializzati FSTATS**, senza dipendere da dati di mercato esterni.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Standalone](https://img.shields.io/badge/standalone-100%25-brightgreen.svg)](https://github.com/ClaudioPoli/fantacalcio-py)

## ✨ Caratteristiche Principali

### 🧮 **Sistema Completamente Autonomo**
- **Nessuna dipendenza** da SOS Fanta o altri dati di mercato esterni
- **FPEDIA**: Statistiche offensive e difensive dettagliate
- **FSTATS**: 19 indici tecnici specializzati per ruolo
- **Algoritmo proprietario** calibrato su performance reali

### 💰 **Pricing Intelligente Autonomo**
- Calcolo prezzi basato **esclusivamente** su 19 indici tecnici FSTATS
- Pesatura specifica per ruolo (POR, DIF, CEN, ATT)
- Normalizzazione avanzata di scale diverse (0-100 indici, 0-38 presenze, etc.)
- Gestione intelligente di dati mancanti (-1 values, NaN)
- Moltiplicatori calibrati per ogni ruolo

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
│   │   ├── standalone_pricing.py # 🧮 Calcolo prezzi autonomo
│   │   ├── market_pricing.py     # [Legacy] Pricing con SOS
│   │   └── advanced_analyzer.py  # Analisi avanzata
│   ├── 📂 data/                  # Gestione dati
│   │   ├── processor.py          # Elaborazione e merge
│   │   └── retriever.py          # Download dati web
│   └── 📂 utils/                 # Utilities
│       ├── config.py             # Configurazioni
│       └── reporting.py          # Report e statistiche
├── 📂 data/                      # Dati input/output
│   └── output/                   # Risultati analisi
│       ├── perfect_merged_analysis.xlsx  # Input: dati FPEDIA+FSTATS
│       └── standalone_pricing_analysis.xlsx  # 🎯 Output finale
├── 📂 scripts/                   # Script legacy e utility
├── main.py                       # 🚀 Entry point principale
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

### 🔄 **Modalità Interattiva** (Raccomandato)
```bash
python main.py --interactive
```
Menu interattivo con:
1. 🧮 Calcolo prezzi autonomo
2. 🏆 Top player per ruolo
3. 💰 Migliori occasioni per fascia di prezzo

### ⚡ **Modalità Batch**
```bash
# Analisi completa autonoma
python main.py --mode analysis

# Directory dati personalizzata
python main.py --mode analysis --data-dir /path/to/data

# Help completo
python main.py --help
```

## 📊 Output e Risultati

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
