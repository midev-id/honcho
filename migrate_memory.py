"""Migrate Hermes holographic facts + MEMORY.md + USER.md into self-hosted Honcho."""
import os, sys, time

from honcho import Honcho

BASE_URL = os.environ.get("HONCHO_BASE_URL", "http://localhost:8000")
WORKSPACE = "hermes"
USER_PEER = "mahdi"
AI_PEER = "hermes"
SESSION_ID = "migration-from-holographic"

# --- Source data (backup) ---
FACTS = [
    # holographic facts
    "Autopreneur products: AI Seller Academy (9 modul, 597rb-2.2jt), AsistenSeller/AsisAds (Shopee ads optimizer Chrome ext, 3 GMV Max types), AutoCircle (learning community, VPS 84.247.149.243), Healthcare SaaS. Domain autopreneur.id on Cloudflare. Scalev for LP/payment.",
    "Team Autopreneur: Dev (Niko & Ario), Ads (Rahmad), Creative (Rois), Design+AI Studio (Rama), R&D (Ahmad), Onboarding (Yulio/Rosyid), CS (Rosyid), Sales (Afifah), Ops (Mas Wi, Ma'ruf, Falakh).",
    "Prioritas user: 1) TikTok Business MCP - advertiser belum connect (blocker); 2) AI Fashion Photo Studio & AI Product Kit via Google AI Studio; 3) AI ad eval AutoAds Okt 2026. Gaya kerja: iteratif stepwise, checkpoint konfirmasi, audience-first, bahasa sederhana.",
    "Meta Ads via Composio: ad account act_1755454388274867 'MJO - Naufal Muktaz Mahdi HKM - 1' (IDR). Akses jalan setelah user assign ad account asset ke user token (METAADS_LIST_BUSINESSES butuh permission business_management).",
    "Scalev MCP (user midevaloper@gmail.com, Naufal Muktaz Mahdi) punya 2 business: AsistenSeller (business_unique_id 6U9APMV3SPJ6LCXS, username auto-ads) dan Autopreneur (IZPIKYCFL0PNCFAJ). Statistik order per bulan pakai datetime_type=confirmed_time + confirmed_time_since/until + tz Asia/Jakarta; default draft_time malah last-30-days.",
    "Jangan tampilkan log tool internal (tool_search/tool_describe/logo gear dll) ke chat - terlalu rame. Hanya kirim hasil/ringkasan.",
    "Saat menyebut/menagih orang di WhatsApp, langsung mention nama (@) biar kena notifikasi, jangan tulis nama polos.",
    "Akses TikTok (autopreneur.id) & Threads (mahdi.assyarqi) via Composio > Zernio (toolkit zernio_mcp, koneksi sen-retile) - aktif.",
    # MEMORY.md facts not already above
    "User prefers Indonesian language, concise responses (skip pleasantries). Name: Mahdi, call him 'Mas Mahdi'. Working dir: C:\\Users\\MAHDI\\Documents\\Autopreneur. Timezone Asia/Jakarta (UTC+7).",
    "Assistant name: Herman ('Man'). WhatsApp bot number: 6285179959339. User's own WhatsApp number (for DM allowlist): 6281333908590.",
    "WA groups allowed: 'Log & Setting Herman AI' 120363428845665425 (home), 'AsistenSeller Internal' 120363423333123641, 'Marketing & Sales' 120363353470511975. Cek grup/user via skill whatsapp-access (list-groups/list-users); jangan bongkar log manual.",
    "When asked to develop an application, run Claude Code locally (claude code) so Claude does the work directly - don't develop it myself unless explicitly asked.",
    "User developing 'AsistenSeller' app - workspace G:\\My Drive\\# AUTOPRENEUR PLAN\\.",
    "Hermes Dashboard: http://192.168.0.189:9119, user admin, port 9119 open. `hermes dashboard` standalone sering crash; desktop app auto-spawn lebih stabil. Kalau gateway/dashboard bentrok: kill python Hermes, buka desktop app.",
    "Windows: HERMES_HOME=C:\\Users\\MAHDI\\AppData\\Local\\hermes (bukan ~/.hermes). Google-workspace scripts di ...\\skills\\productivity\\google-workspace\\scripts\\setup.py.",
    # USER.md facts not already above
    "User prefers Bahasa Indonesia for communication.",
    "User calls the WhatsApp bot 'Herman' or 'Man' - prefer this name in WhatsApp context.",
    "Autopreneur Hub workspace ada di 'G:\\My Drive\\# AUTOPRENEUR PLAN #\\' - collective-memory.md, project-context.md, decisions-log.md. Semua tim bisa akses sini. Setup gradual: memory dulu, skills menyusul.",
    "Bot WhatsApp bernama 'Herman' terhubung ke grup 'Feedback AsistenSeller' (120363428845665425@g.us). Semua perintah dari semua orang masuk ke konteks yang sama.",
    "WhatsApp bot 'Herman' di grup Feedback AsistenSeller (120363428845665425@g.us) - pakai bridge mode bot, group_policy: open (langsung balas semua pesan grup tanpa @mention), WHATSAPP_ALLOWED_USERS=*.",
    "Users who can @mention: 6281333908590 (Mas Mahdi), 6281542874757 (Mas Rosyid).",
    "Autopreneur apps working directory: C:\\Users\\MAHDI\\Documents\\Autopreneur.",
]

# Hard conclusions to seed explicitly (key identity + prefs) so they're queryable immediately
HARD_CONCLUSIONS = [
    "User is Mahdi, called 'Mas Mahdi', Jakarta timezone (UTC+7). Prefers Indonesian, concise responses without pleasantries.",
    "User runs Autopreneur with products: AI Seller Academy, AsistenSeller/AsisAds (Shopee ads optimizer), AutoCircle, Healthcare SaaS. Domain autopreneur.id. Uses Scalev for landing pages/payments.",
    "User's assistant is named Herman ('Man'), connected to WhatsApp bot 6285179959339. Groups: Feedback AsistenSeller and others.",
    "When asked to build an app, user wants Claude Code to do the work locally (claude code), not the assistant developing directly.",
    "User's working style: iterative stepwise, checkpoint confirmation, audience-first, simple language.",
]

def main():
    print(f"Connecting to self-hosted Honcho: {BASE_URL}")
    hc = Honcho(base_url=BASE_URL, environment="local", workspace_id=WORKSPACE)

    # Get/create peers
    print(f"Resolving peers: user={USER_PEER}, ai={AI_PEER}")
    user = hc.peer(USER_PEER)
    ai = hc.peer(AI_PEER)
    print("Peers OK")

    # Create a session with both peers
    sess = hc.session(
        SESSION_ID,
        peers=[user, ai],
    )
    print(f"Session ready: {sess}")

    # Option A: inject facts as user messages so deriver builds representations
    msgs = []
    for f in FACTS:
        msgs.append(
            f"Migrated memory fact about me (from previous Hermes memory): {f}"
        )
    resp = sess.add_messages([user.message(content=f"({m})") for m in msgs])
    print(f"Injected {len(resp)} user messages for deriver processing")

    # Option B: seed hard conclusions so facts are instantly queryable
    scope = user.conclusions_of(user)
    created = scope.create([{"content": c} for c in HARD_CONCLUSIONS])
    print(f"Seeded {len(created)} hard conclusions")

    print("\n--- Verify: query conclusions ---")
    try:
        q = scope.query("Who is the user and what products does Autopreneur make?", top_k=3)
        for c in q:
            print(f"  * {c.content[:90]}")
    except Exception as e:
        print("Query failed (may still be embedding):", e)

    print("\nDONE migration. Deriver will keep processing in background.")

if __name__ == "__main__":
    main()