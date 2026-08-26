import os

# ---- Required env vars (set these in Render's Environment tab) ----
BOT_TOKEN = os.environ["BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]  # Neon connection string

# ---- Admin(s) ----
# You can add more admin ids separated by commas via ADMIN_IDS env var,
# e.g. ADMIN_IDS=5523761749,111111111
_raw_admins = os.environ.get("ADMIN_IDS", "5523761749")
ADMIN_IDS = [int(x.strip()) for x in _raw_admins.split(",") if x.strip()]

# ---- Bot / webhook ----
BOT_USERNAME = os.environ.get("BOT_USERNAME", "VLL_PREM_BOT")

# Render sets RENDER_EXTERNAL_URL automatically for web services.
# Fallback to a manual WEBHOOK_BASE_URL env var if you set one yourself.
WEBHOOK_BASE_URL = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WEBHOOK_BASE_URL", "")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "vllprem_webhook_secret")

PORT = int(os.environ.get("PORT", 10000))

# ---- Channels the user must join ----
# For public channels: just set "username".
# For private channels (invite-link only): you MUST set "chat_id" (a negative
# number like -1001234567890). Bots cannot resolve invite links on their own —
# see README.md "How to get a private channel's chat_id".
CHANNELS = [
    {
        "title": "VLL Premium",
        "url": "https://t.me/VLLPrem",
        "username": "VLLPrem",   # public -> checked via @username
        "chat_id": None,
    },
    {
        "title": "VLL Premium Chat",
        "url": "https://t.me/+tEUbmGCU-jUxZWYy",
        "username": None,
        "chat_id": None,  # <-- FILL THIS IN, see README (private channel)
    },
]

# ---- Prizes shown to users ----
PRIZES = [
    ("🥇 1-o'rin", "1 yillik Telegram Premium yoki 250 000 so'm"),
    ("🥈 2-o'rin", "170 000 so'm"),
    ("🥉 3-o'rin", "80 000 so'm"),
]
