import os, re, ssl, sys, json, time, socket, base64
import logging, threading, argparse, requests
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger("V2Hunter")
log.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S")
_ch  = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt)
log.addHandler(_ch)

BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
CHAT_ID          = "@V2rayashaq"
ADMIN_USER       = os.environ.get("ADMIN_TG", "@genie_2000")
MAX_POSTS        = 4
TARGET_PORT      = 443
SOCKET_TIMEOUT   = 1.5

BASE_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://t.me/s/v2_team",
    "https://t.me/s/V2ray_Alpha",
    "https://t.me/s/V2Ray_VLESS_VMess"
]

CONFIG_RE = re.compile(r"(?:vless|vmess)://[^\s#\"'<>]+")

@dataclass
class V2Config:
    raw: str; patched: str; host: str; port: int; ping: int; proto: str
    country: str = "Unknown"; cc: str = "??"; isp: str = "Unknown"

# --- التنسيق الأصلي للرسالة كما طلبت ---
def build_message(cfg: V2Config) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = "🔥 <b>Ultimate Ashaq</b> 🔥"
    
    return (
        f"{header}\n"
        f"========================\n"
        f"🌍 <b>Country:</b> {cfg.cc} {cfg.country}\n"
        f"🔷 <b>Protocol:</b> {cfg.proto}\n"
        f"🔒 <b>SSL/TLS:</b> ✅ Active (Insecure)\n"
        f"⚙️ <b>SNI:</b> Empty ✔️\n"
        f"🔓 <b>Allow Insecure:</b> ON ✔️\n"
        f"⚡ <b>Ping:</b> {cfg.ping}ms\n"
        f"🌐 <b>ISP:</b> {cfg.isp}\n"
        f"📅 <b>Verified:</b> {now}\n"
        f"========================\n"
        f"<code>{cfg.patched}</code>\n"
        f"========================\n"
        f"#Ashaq #V2Ray #Free443 #{cfg.proto} #EmptySNI\n"
        f"@V2rayashaq"
    )

def patch_config(raw):
    if raw.startswith("vmess://"):
        try:
            b64 = raw[len("vmess://"):]
            obj = json.loads(base64.b64decode(b64 + "==" * 3).decode("utf-8", errors="ignore"))
            obj["allowInsecure"] = True
            obj["sni"] = ""; obj["host"] = ""
            return "vmess://" + base64.b64encode(json.dumps(obj).encode()).decode()
        except: return raw
    sep = "&" if "?" in raw else "?"
    return raw + f"{sep}allowInsecure=1"

def get_geo(host):
    try:
        ip = socket.gethostbyname(host)
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp", timeout=5).json()
        if r.get("status") == "success":
            return r.get("country", "Unknown"), r.get("countryCode", "??"), r.get("isp", "Unknown")
    except: pass
    return "Unknown", "??", "Unknown"

def check_raw(raw):
    m = re.search(r"@([^:/\s#]+):(\d+)", raw)
    if not m: return None
    host, port = m.group(1), int(m.group(2))
    if port != TARGET_PORT: return None
    ping = int((time.perf_counter() - time.perf_counter()) * 1000) # Dummy start
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT):
            ping = int((time.perf_counter() - t0) * 1000)
            country, cc, isp = get_geo(host)
            return V2Config(raw=raw, patched=patch_config(raw), host=host, port=port, ping=ping, 
                            proto="VLESS" if "vless" in raw else "VMESS", country=country, cc=cc, isp=isp)
    except: return None

def main():
    log.info("🚀 Starting Ultimate Ashaq v4.1...")
    all_raw = []
    for url in BASE_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            all_raw.extend(CONFIG_RE.findall(r.text))
        except: pass
    
    unique = list(set(all_raw))
    live = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        futs = [ex.submit(check_raw, r) for r in unique[:300]]
        for f in as_completed(futs):
            res = f.result()
            if res: live.append(res)
    
    live.sort(key=lambda x: x.ping)
    for cfg in live[:MAX_POSTS]:
        payload = {
            "chat_id": CHAT_ID,
            "text": build_message(cfg),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": {"inline_keyboard": [[
                {"text": "Channel", "url": "https://t.me/V2rayashaq"},
                {"text": "Admin", "url": f"https://t.me/{ADMIN_USER.lstrip('@')}"}
            ]]}
        }
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
    log.info("Done! Posted exactly as original.")

if __name__ == "__main__":
    main()
