import os
import json
import logging
from flask import Flask, request, jsonify
import requests
import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("lead-bot")

app = Flask(__name__)


@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return resp


@app.route("/", methods=["GET", "OPTIONS"])
def index():
    return "Lead bot is running"

BOT_TOKEN = config.BOT_TOKEN
LEAD_SECRET = config.LEAD_SECRET
SUPABASE_URL = config.SUPABASE_URL
SUPABASE_ANON_KEY = config.SUPABASE_ANON_KEY
OWNER_IDS = list(config.OWNER_IDS)
CHAT_IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_ids.json")

GSHEETS_ENABLED = config.GSHEETS_ENABLED
GSHEETS_SPREADSHEET_ID = config.GSHEETS_SPREADSHEET_ID
GSHEETS_SHEET = config.GSHEETS_SHEET
GSHEETS_CLIENT_ID = config.GSHEETS_CLIENT_ID
GSHEETS_CLIENT_SECRET = config.GSHEETS_CLIENT_SECRET
GSHEETS_REFRESH_TOKEN = config.GSHEETS_REFRESH_TOKEN
_sheets_access_token = {"token": None, "expires": 0}
MAX_BOT_TOKEN = config.MAX_BOT_TOKEN
MAX_WEBHOOK_SECRET = config.MAX_WEBHOOK_SECRET
MAX_OWNER_IDS = list(config.MAX_OWNER_IDS)
MAX_CHAT_IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "max_chat_ids.json")

TG_API = "https://api.telegram.org/bot" + BOT_TOKEN


def load_chat_ids():
    if os.path.exists(CHAT_IDS_FILE):
        try:
            with open(CHAT_IDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_chat_ids(ids):
    try:
        with open(CHAT_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(ids, f)
    except Exception as e:
        log.error("save chat_ids failed: %s", e)


def tg_send(chat_id, text):
    if not BOT_TOKEN:
        log.warning("BOT_TOKEN not set, skip send")
        return
    try:
        requests.post(
            TG_API + "/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=15,
        )
    except Exception as e:
        log.error("tg send failed: %s", e)


def save_lead(lead):
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        log.warning("Supabase env not set, skip save")
        return
    try:
        r = requests.post(
            SUPABASE_URL + "/rest/v1/leads",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": "Bearer " + SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=lead,
            timeout=15,
        )
        log.info("supabase save status: %s", r.status_code)
    except Exception as e:
        log.error("supabase save failed: %s", e)


def sheets_access_token():
    import time
    if _sheets_access_token["token"] and _sheets_access_token["expires"] > time.time() + 60:
        return _sheets_access_token["token"]
    try:
        r = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GSHEETS_CLIENT_ID,
                "client_secret": GSHEETS_CLIENT_SECRET,
                "refresh_token": GSHEETS_REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
        data = r.json()
        token = data.get("access_token")
        if token:
            _sheets_access_token["token"] = token
            _sheets_access_token["expires"] = time.time() + int(data.get("expires_in", 3599))
        return token
    except Exception as e:
        log.error("sheets token failed: %s", e)
        return None


def save_to_sheets(lead):
    if not GSHEETS_ENABLED or not GSHEETS_SPREADSHEET_ID:
        log.info("GSHEETS not enabled, skip sheets")
        return
    token = sheets_access_token()
    if not token:
        log.error("no sheets access token")
        return
    try:
        url = (
            "https://sheets.googleapis.com/v4/spreadsheets/"
            + GSHEETS_SPREADSHEET_ID
            + "/values/"
            + requests.utils.quote(GSHEETS_SHEET)
            + "!A1:G1:append?valueInputOption=RAW"
        )
        r = requests.post(
            url,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            json={"values": [[lead.get("created_at", ""), lead.get("name", ""), lead.get("contact", ""), lead.get("title", ""), lead.get("message", ""), lead.get("note", ""), lead.get("source", "")]]},
            timeout=20,
        )
        log.info("sheets append status: %s", r.status_code)
    except Exception as e:
        log.error("sheets append failed: %s", e)


MAX_API = "https://platform-api.max.ru"

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


def max_headers():
    return {"Authorization": MAX_BOT_TOKEN, "Content-Type": "application/json"}


def load_max_chat_ids():
    if os.path.exists(MAX_CHAT_IDS_FILE):
        try:
            with open(MAX_CHAT_IDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_max_chat_ids(ids):
    try:
        with open(MAX_CHAT_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(ids, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error("save max_chat_ids failed: %s", e)


def max_send(target_id, text):
    if not MAX_BOT_TOKEN:
        log.warning("MAX_BOT_TOKEN not set, skip max send")
        return
    try:
        r = requests.post(
            MAX_API + "/messages",
            params={"user_id": target_id},
            headers=max_headers(),
            json={"text": text},
            timeout=15,
            verify=False,
        )
        if r.status_code != 200:
            log.warning("max send status %s: %s", r.status_code, r.text[:300])
    except Exception as e:
        log.error("max send failed: %s", e)


@app.route("/debug", methods=["GET"])
def debug():
    return jsonify({
        "lead_secret": LEAD_SECRET,
        "bot_token_len": len(BOT_TOKEN),
        "supabase_url": SUPABASE_URL,
        "owner_ids": OWNER_IDS,
        "chat_ids": load_chat_ids(),
        "sheets_enabled": GSHEETS_ENABLED,
        "sheets_spreadsheet_id": GSHEETS_SPREADSHEET_ID,
        "max_owner_ids": MAX_OWNER_IDS,
        "max_chat_ids": load_max_chat_ids(),
    })


@app.route("/api/lead", methods=["POST", "OPTIONS"])
def lead():
    if request.method == "OPTIONS":
        return "", 200
    data = request.get_json(silent=True) or {}
    log.info("lead request: %s", json.dumps(data, ensure_ascii=False)[:200])
    if data.get("secret") != LEAD_SECRET:
        return jsonify({"ok": False, "error": "bad secret"}), 403

    name = (data.get("name") or "").strip()
    contact = (data.get("contact") or "").strip()
    title = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    note = (data.get("note") or "").strip()
    source = (data.get("source") or "site").strip()

    if not name or not contact:
        return jsonify({"ok": False, "error": "name and contact are required"}), 422

    lead = {"name": name, "contact": contact, "title": title, "message": message, "note": note, "source": source}
    from datetime import datetime, timedelta, timezone
    msk = timezone(timedelta(hours=3))
    lead["created_at"] = datetime.now(msk).strftime("%Y-%m-%d %H:%M:%S")
    save_lead(lead)
    save_to_sheets(lead)

    text = "— Заявка с сайта —\n"
    if title:
        text += "Название: " + title + "\n"
    text += "Имя: " + (name or "—") + "\n"
    text += "Контакт: " + (contact or "—") + "\n"
    text += "Описание:\n" + (message or "—")
    if note:
        text += "\nСообщение для нас:\n" + note
    recipients = set(OWNER_IDS + load_chat_ids())
    for cid in recipients:
        tg_send(cid, text)

    max_recipients = set(str(x) for x in (MAX_OWNER_IDS + load_max_chat_ids()))
    for uid in max_recipients:
        max_send(uid, text)

    return jsonify({"ok": True})


@app.route("/tg", methods=["POST", "OPTIONS"])
def tg_webhook():
    if request.method == "OPTIONS":
        return "", 200
    update = request.get_json(silent=True) or {}
    handle_update(update)
    return jsonify({"ok": True})


@app.route("/tg/set-webhook")
def set_webhook():
    url = request.host_url.rstrip("/") + "/tg"
    r = requests.post(TG_API + "/setWebhook", json={"url": url}, timeout=15)
    return jsonify(r.json())


@app.route("/max", methods=["POST", "OPTIONS"])
def max_webhook():
    if request.method == "OPTIONS":
        return "", 200
    if request.headers.get("X-Max-Bot-Api-Secret") != MAX_WEBHOOK_SECRET:
        return jsonify({"ok": False, "error": "bad webhook secret"}), 403
    update = request.get_json(silent=True) or {}
    log.info("max update: %s", json.dumps(update, ensure_ascii=False)[:300])
    handle_max_update(update)
    return jsonify({"ok": True})


@app.route("/max/set-webhook")
def max_set_webhook():
    url = request.host_url.rstrip("/") + "/max"
    r = requests.post(
        MAX_API + "/subscriptions",
        headers=max_headers(),
        json={
            "url": url,
            "update_types": ["message_created", "bot_started"],
            "secret": MAX_WEBHOOK_SECRET,
        },
        timeout=15,
        verify=False,
    )
    try:
        return jsonify(r.json())
    except Exception:
        return jsonify({"status": r.status_code, "body": r.text[:500]})


@app.route("/max/test", methods=["GET"])
def max_test():
    results = {}
    for domain in ("platform-api.max.ru", "platform-api2.max.ru"):
        try:
            r = requests.get(
                "https://" + domain + "/me",
                headers=max_headers(),
                timeout=10,
                verify=False,
            )
            results[domain] = {"status": r.status_code, "body": r.text[:200]}
        except Exception as e:
            results[domain] = {"error": str(e)[:200]}
    return jsonify(results)


@app.route("/max/subscriptions", methods=["GET"])
def max_subscriptions():
    r = requests.get(MAX_API + "/subscriptions", headers=max_headers(), timeout=15, verify=False)
    try:
        return jsonify(r.json())
    except Exception:
        return jsonify({"status": r.status_code, "body": r.text[:500]})


@app.route("/max/clear-webhook", methods=["GET", "POST", "DELETE"])
def max_clear_webhook():
    r = requests.delete(MAX_API + "/subscriptions", headers=max_headers(), timeout=15, verify=False)
    try:
        return jsonify(r.json())
    except Exception:
        return jsonify({"status": r.status_code, "body": r.text[:500]})


def handle_max_update(update):
    update_type = update.get("update_type", "")
    user = update.get("user") or {}
    user_id = str(user.get("user_id", ""))
    if not user_id:
        return
    ids = load_max_chat_ids()
    if user_id not in ids:
        ids.append(user_id)
        save_max_chat_ids(ids)
        if update_type == "bot_started":
            max_send(user_id, "Бот для заявок работает. Заявки будут приходить сюда.")


def handle_update(update):
    msg = update.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    text = (msg.get("text") or "").strip()
    if chat_id and text == "/start":
        ids = load_chat_ids()
        if chat_id not in ids:
            ids.append(chat_id)
            save_chat_ids(ids)
        tg_send(chat_id, "Бот для заявок работает. Заявки будут приходить сюда.")


def run_polling():
    import time
    log.info("starting polling")
    offset = 0
    while True:
        try:
            r = requests.get(
                TG_API + "/getUpdates",
                params={"timeout": 30, "offset": offset, "allowed_updates": ["message"]},
                timeout=60,
            )
            data = r.json()
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                handle_update(upd)
        except Exception as e:
            log.error("polling error: %s", e)
            time.sleep(5)


if __name__ == "__main__":
    if os.environ.get("POLLING") == "1":
        run_polling()
    else:
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)