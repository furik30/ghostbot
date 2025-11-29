import os
import yaml
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# --- ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SESSION_NAME = os.getenv("SESSION_NAME", "ghost_session")

# --- ПУТИ К ФАЙЛАМ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = "database"
SESSIONS_DIR = "sessions"

DATA_DIR_PATH = os.path.join(BASE_DIR, DATA_DIR)
SESSIONS_DIR_PATH = os.path.join(BASE_DIR, SESSIONS_DIR)

MIMICRY_DB = os.path.join(DATA_DIR_PATH, "mimicry.db")
CONTEXT_FILE = os.path.join(DATA_DIR_PATH, "chat_contexts.json")
PROMPTS_FILE = os.path.join(BASE_DIR, "prompts.yaml")

# --- ЗАГРУЗКА PROMPTS ---
def load_prompts():
    if not os.path.exists(PROMPTS_FILE):
        return {}
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(f"Error loading YAML: {exc}")
            return {}

PROMPTS = load_prompts()

# --- ИНИЦИАЛИЗАЦИЯ ---
os.makedirs(DATA_DIR_PATH, exist_ok=True)
os.makedirs(SESSIONS_DIR_PATH, exist_ok=True)

if not API_ID or not API_HASH:
    print("❌ ОШИБКА: API_ID или API_HASH не найдены в .env")