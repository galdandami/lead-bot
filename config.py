import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(path):
        return {}
    values = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip()
    return values


_DOTENV = _load_dotenv()


def _env(key, default=""):
    return os.environ.get(key) or _DOTENV.get(key) or default


BOT_TOKEN = _env("BOT_TOKEN")
LEAD_SECRET = _env("LEAD_SECRET")
SUPABASE_URL = _env("SUPABASE_URL")
SUPABASE_ANON_KEY = _env("SUPABASE_ANON_KEY")
OWNER_IDS = [x.strip() for x in _env("OWNER_IDS", "").split(",") if x.strip()]

GSHEETS_ENABLED = _env("GSHEETS_ENABLED", "true").lower() in ("1", "true", "yes")
GSHEETS_SPREADSHEET_ID = _env("GSHEETS_SPREADSHEET_ID")
GSHEETS_SHEET = _env("GSHEETS_SHEET", "Заявки")
GSHEETS_CLIENT_ID = _env("GSHEETS_CLIENT_ID")
GSHEETS_CLIENT_SECRET = _env("GSHEETS_CLIENT_SECRET")
GSHEETS_REFRESH_TOKEN = _env("GSHEETS_REFRESH_TOKEN")

MAX_BOT_TOKEN = _env("MAX_BOT_TOKEN")
MAX_WEBHOOK_SECRET = _env("MAX_WEBHOOK_SECRET")
MAX_OWNER_IDS = [x.strip() for x in _env("MAX_OWNER_IDS", "").split(",") if x.strip()]