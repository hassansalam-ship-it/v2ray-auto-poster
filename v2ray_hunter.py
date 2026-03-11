import os, re, ssl, sys, json, time, socket, base64
import logging, threading, argparse, requests
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
log = logging.getLogger("V2Hunter")
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
_ch  = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt); _ch.setLevel(logging.INFO)
log.addHandler(_ch)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
CHAT_ID          = "@V2rayashaq"
ADMIN_USER       = os.environ.get("ADMIN_TG", "@genie_2000")
SUB_FILE         = "sub_link.txt"
SOURCES_FILE     = "learned_sources.json"
STATS_FILE       = "source_stats.json"
MAX_POSTS        = 4
MAX_SUB_CONFIGS  = 200
FETCH_WORKERS    = 60
CHECK_WORKERS    = 100
FETCH_TIMEOUT    = 12
SOCKET_TIMEOUT   = 1.5
SSL_TIMEOUT      = 3.0
MAX_PING_MS      = 600
STOP_AFTER_FOUND = 1000
TARGET_PORT      = 443

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASE SOURCES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASE_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vmess",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Atlas.md",
    "https://t.me/s/v2_team",
    "https://t.me/s/V2ray_Alpha",
    "https://t.me/s/V2Ray_VLESS_VMess",
    "https://t.me/s/Cloudfront_VPN"
]

VPS_KEYWORDS = ["oracle","google","amazon","aws","digitalocean","hetzner","ovh","vps","hosting"]
CF_KEYWORDS = ["cloudfront","cdn","worker","pages.dev","cloudflare","cfip"]

CONFIG_RE  = re.compile(r"(?:vless|vmess)://[^\s#\"'<>][]+")
GITHUB_RAW = re.compile(r"https://raw.githubusercontent.com/[^\s\"'<>][)]+.txt")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def extract_sni(raw: str) -> str:
    if raw.startswith("vmess://"):
        try:
            b64 = raw[len("vmess://"):]
            obj = json.loads(base64.b64decode(b64 + "==" * 3).decode("utf-8", errors="ignore"))
            return str(obj.get("sni", obj.get("host", "")))
        except: return ""
    m = re.search(r"[?&](?:sni|host)=([^&\s#]+)", raw, re.IGNORECASE)
    return m.group(1) if m else ""

def patch_config(raw: str) -> str:
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

class SourceManager:
    def __init__(self):
        self.stats = {}
        self.learned = []
    def record(self, url, count): pass
    def add_discovered(self, urls): pass
    def save(self): pass
    def get_all_sources(self): return list(set(BASE_SOURCES + self.learned))

@dataclass
class V2Config:
    raw: str; raw_patched: str; host: str; port: int; ping_ms: int
    proto: str; ssl_ok: bool = False; ssl_cert_cn: str = ""
    country_code: str = "??"; country: str = "Unknown"; isp: str = ""
    is_vps: bool = False; is_cf: bool = False
    def score(self) -> int:
        s = 600 if self.is_vps else 0
        s += 400 if self.is_cf else 0
        s += 200 if self.ssl_ok else 0
        s += max(0, 600 - self.ping_ms)
        return s

def tcp_ping(host, port):
    try:
        t0 = time.perf_counter()
        with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT):
            return int((time.perf_counter() - t0) * 1000)
    except: return None

def ssl_check(host, port):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with ctx.wrap_socket(socket.create_connection((host, port), timeout=SSL_TIMEOUT), server_hostname=host) as s:
            return True, "Verified"
    except: return False, ""

def check_raw(raw):
    if extract_sni(raw) != "": return None
    m = re.search(r"@([^:/\s#]+):(\d+)", raw)
    if not m: return None
    host, port = m.group(1), int(m.group(2))
    if port != TARGET_PORT: return None
    ping = tcp_ping(host, port)
    if ping is None: return None
    ssl_ok, cn = ssl_check(host, port)
    return V2Config(raw=raw, raw_patched=patch_config(raw), host=host, port=port, ping_ms=ping,
                    proto="VLESS" if "vless" in raw else "VMESS", ssl_ok=ssl_ok, ssl_cert_cn=cn)

def main():
    log.info("🚀 Starting Ashaq Ultimate Hunter v4")
    sm = SourceManager()
    all_raw = []
    for url in sm.get_all_sources():
        try:
            r = requests.get(url, timeout=10)
            all_raw.extend([c for c in CONFIG_RE.findall(r.text) if ":443" in c])
        except: pass
    
    unique = list(set(all_raw))
    live = []
    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as ex:
        futs = [ex.submit(check_raw, r) for r in unique[:500]]
        for f in as_completed(futs):
            res = f.result()
            if res: live.append(res)
    
    live.sort(key=lambda x: x.score(), reverse=True)
    for cfg in live[:MAX_POSTS]:
        msg = f"✨ <b>Ashaq Team</b> ✨\n🌍 <b>Country:</b> {cfg.country_code}\n⚡ <b>Ping:</b> {cfg.ping_ms}ms\n<code>{cfg.raw_patched}</code>"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
    
    with open(SUB_FILE, "w") as f:
        f.write(base64.b64encode("\n".join([c.raw_patched for c in live]).encode()).decode())

if __name__ == "__main__":
    main()
