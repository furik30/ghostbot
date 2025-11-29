import os
import yaml
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
SESSION_NAME = os.getenv("SESSION_NAME", "ghost_session")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR_PATH = os.path.join(BASE_DIR, "data")
SESSIONS_DIR_PATH = os.path.join(BASE_DIR, "sessions")
CONTEXT_FILE = os.path.join(DATA_DIR_PATH, "chat_contexts.json")
PROMPTS_FILE = os.path.join(BASE_DIR, "prompts.yaml")

def load_prompts():
    if not os.path.exists(PROMPTS_FILE):
        return {}
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError:
            return {}

PROMPTS = load_prompts()
DRAFT_COOLDOWN = 2

os.makedirs(DATA_DIR_PATH, exist_ok=True)
os.makedirs(SESSIONS_DIR_PATH, exist_ok=True)

if not API_ID or not API_HASH:
    print("❌ ОШИБКА: API_ID или API_HASH не найдены в .env")