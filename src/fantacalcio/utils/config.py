# config.py
import os
import base64


def decode(stringa):
    return base64.b64decode(stringa).decode("utf-8")


# --- Percorsi ---
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
INTERIM_DIR = os.path.join(DATA_DIR, "interim")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
GIOCATORI_URLS_FILE = os.path.join(DATA_DIR, "giocatori_urls.txt")
GIOCATORI_CSV = os.path.join(RAW_DIR, "_giocatori.csv")
PLAYERS_CSV = os.path.join(RAW_DIR, "_players.csv")
OUTPUT_EXCEL = os.path.join(OUTPUT_DIR, "final_analysis.xlsx")

# --- Stagione ---
ANNO_CORRENTE = 2025
FSTATS_ANNO = 2024

# --- URL fonti dati ---
BASEURL_FPEDIA = decode("aHR0cHM6Ly93d3cuZmFudGFjYWxjaW9wZWRpYS5jb20=")
BASEURL_FSTATS = decode("aHR0cHM6Ly9hcGkuYXBwLmZhbnRhZ29hdC5pdC9hcGk=")
FPEDIA_URL = f"{BASEURL_FPEDIA}/lista-calciatori-serie-a/"
FSTATS_LOGIN_URL = f"{BASEURL_FSTATS}/account/login/"
FSTATS_PLAYERS_URL = (
    f"{BASEURL_FSTATS}/v1/zona/player/"
    f"?page_size=1000&page=1"
    f"&season={FSTATS_ANNO}%2F{str(FSTATS_ANNO + 1)[-2:]}&ordering="
)

# --- Scraping ---
RUOLI = ["Portieri", "Difensori", "Centrocampisti", "Attaccanti"]
MAX_WORKERS = 5
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Retry e freshness
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # secondi
DATA_MAX_AGE_HOURS = 24  # ore prima di considerare i dati stale

# --- Mappatura ruoli ---
# Normalizzazione dei ruoli dalle diverse fonti a un formato standard
ROLE_MAP = {
    # FPEDIA
    "POR": "P", "DIF": "D", "CEN": "C", "ATT": "A",
    # FSTATS
    "P": "P", "D": "D", "C": "C", "A": "A",
    # Mantra (dalla colonna fantacalcio_position)
    "Por": "P", "Dd": "D", "Ds": "D", "Dc": "D",
    "E": "C", "M": "C", "C": "C", "T": "C",
    "W": "A", "Pc": "A", "A": "A",
}

# --- Indici tecnici FSTATS ---
TECHNICAL_INDICES = [
    "External_breakout_Index",
    "Set_piece_attack_Index",
    "Offensive_verticalization_Index",
    "Attacking_area_Index",
    "Pass_accuracy_Index",
    "Accompany_the_offensive_action_Index",
    "Cross_accuracy_Index",
    "Pass_leading_chances_Index",
    "Shot_on_target_Index",
    "Received_pass_Index",
    "Deep_runs_Index",
    "Air_challenge_offensive_Index",
    "Shot_on_goal_Index",
    "Converge_in_the_center_Index",
    "Pass_forward_accuracy_Index",
    "Defense_solidity_Index",
    "Offensive_actions_Index",
    "Dribbles_successful_Index",
    "Offensive_field_presence_Index",
]

# --- Pricing: pesi per ruolo ---
# Ogni componente di score ha pesi diversi per ruolo
PRICING_WEIGHTS = {
    "P": {"offensive": 0.05, "defensive": 0.45, "reliability": 0.30, "technical": 0.20},
    "D": {"offensive": 0.25, "defensive": 0.25, "reliability": 0.25, "technical": 0.25},
    "C": {"offensive": 0.35, "defensive": 0.10, "reliability": 0.20, "technical": 0.35},
    "A": {"offensive": 0.50, "defensive": 0.05, "reliability": 0.15, "technical": 0.30},
}

# Indici tecnici rilevanti per ruolo con pesi
TECHNICAL_WEIGHTS_BY_ROLE = {
    "P": {
        "Defense_solidity_Index": 5.0,
        "Pass_accuracy_Index": 2.0,
    },
    "D": {
        "Defense_solidity_Index": 4.0,
        "Air_challenge_offensive_Index": 3.0,
        "Set_piece_attack_Index": 2.5,
        "Pass_forward_accuracy_Index": 2.0,
        "Cross_accuracy_Index": 1.5,
        "Offensive_actions_Index": 1.0,
    },
    "C": {
        "Pass_leading_chances_Index": 4.0,
        "Offensive_actions_Index": 3.5,
        "Pass_accuracy_Index": 3.0,
        "Offensive_verticalization_Index": 2.5,
        "Accompany_the_offensive_action_Index": 2.0,
        "Cross_accuracy_Index": 2.0,
        "Dribbles_successful_Index": 1.5,
    },
    "A": {
        "Shot_on_target_Index": 5.0,
        "Shot_on_goal_Index": 4.5,
        "Offensive_actions_Index": 4.0,
        "Attacking_area_Index": 3.5,
        "Deep_runs_Index": 2.5,
        "Dribbles_successful_Index": 2.0,
        "Set_piece_attack_Index": 1.5,
    },
}

# Budget per ruolo (lega classica 500 crediti)
BUDGET = {"P": 30, "D": 75, "C": 110, "A": 285}
