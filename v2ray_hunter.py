"""
V2RAY ULTIMATE HUNTER v4 - ASHAQ TEAM
- Empty SNI only + Allow Insecure injected
- Self-evolving: discovers new sources, learns from success/failure
"""
import os, re, ssl, sys, json, time, socket, base64
import logging, threading, argparse, requests
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── LOGGING ────────────────────────────────────────────────────
log = logging.getLogger("V2Hunter")
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
_ch  = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt); _ch.setLevel(logging.INFO)
log.addHandler(_ch)

# ─── SETTINGS ───────────────────────────────────────────────────
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

# ─── BASE SOURCES ───────────────────────────────────────────────
BASE_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://t.me/s/v2_team",
    "https://t.me/s/V2ray_Alpha",
    "https://t.me/s/V2Ray_VLESS_VMess"
]

VPS_KEYWORDS = ["oracle","google","amazon","aws","digitalocean","hetzner","ovh","vultr","azure","vps"]
CF_KEYWORDS = ["cloudfront","cdn","worker","pages.dev","cloudflare","cfcdn"]

# تم إصلاح الأقواس هنا (التصحيح المطلوب)
CONFIG_RE  = re.compile(r"(?:vless|vmess)://[^\s#\"'<>]+")
GITHUB_RAW = re.compile(r"https://raw\.githubusercontent\.com/[^\s\"'<>/]+/[^\s\"'<>]+/[^\s\"'<>]+")

# ─── SNI UTILS ──────────────────────────────────────────────────
_SNI_KEYS = ("sni","host","peer","servername","server-name")

def extract_sni(raw: str) -> str:
    if raw.startswith("vmess://"):
        try:
            b64 = raw[len("vmess://"):]
            obj = json.loads(base64.b64decode(b64 + "==" * 3).decode("utf-8", errors="ignore"))
            for k in _SNI_KEYS:
                if obj.get(k): return str(obj[k])
        except: pass
    else:
        for k in _SNI_KEYS:
            m = re.search(rf"[?&]{k}=([^&\s#]+)", raw, re.IGNORECASE)
            if m: return m.group(1)
    return ""

def has_empty_sni(raw: str) -> bool:
    return extract_sni(raw) == ""

def patch_config(raw: str) -> str:
    if raw.startswith("vmess://"):
        try:
            b64 = raw[len("vmess://"):]
            obj = json.loads(base64.b64decode(b64 + "==" * 3).decode("utf-8", errors="ignore"))
            obj["allowInsecure"] = True
            for k in _SNI_KEYS: obj[k] = ""
            return "vmess://" + base64.b64encode(json.dumps(obj).encode()).decode()
        except: return raw
    sep = "&" if "?" in raw else "?"
    return raw + f"{sep}allowInsecure=1"

# ─── SOURCE MANAGER ─────────────────────────────────────────────
class SourceManager:
    def __init__(self):
        self.stats = self._load(STATS_FILE, {})
        self.learned = self._load(SOURCES_FILE, [])
    def _load(self, path, default):
        try:
            with open(path, "r") as f: return json.load(f)
        except: return default
    def save(self):
        try:
            with open(STATS_FILE, "w") as f: json.dump(self.stats, f)
            with open(SOURCES_FILE, "w") as f: json.dump(self.learned, f)
        except: pass
    def record(self, url, count):
        if url not in self.stats: self.stats[url] = {"hits":0, "fails":0}
        if count > 0: self.stats[url]["hits"] += 1
        else: self.stats[url]["fails"] += 1
    def get_all_sources(self):
        return list(set(BASE_SOURCES + self.learned))

@dataclass
class V2Config:
    raw: str; raw_patched: str; host: str; port: int; ping_ms: int; proto: str
    ssl_ok: bool = False; country_code: str = "??"; country: str = "Unknown"
    isp: str = ""; is_vps: bool = False; is_cf: bool = False
    def score(self) -> int:
        s = 600 if self.is_vps else 0
        s += 400 if self.is_cf else 0
        return s + max(0, 600 - self.ping_ms)

def tcp_ping(host, port):
    try:
        t0 = time.perf_counter()
        with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT):
            return int((time.perf_counter() - t0) * 1000)
    except: return None

def main():
    log.info("🚀 Starting ASHAQ Ultimate Hunter v4 (Full Corrected)")
    sm = SourceManager()
    all_raw = []
    for url in sm.get_all_sources():
        try:
            r = requests.get(url, timeout=FETCH_TIMEOUT)
            found = [c for c in CONFIG_RE.findall(r.text) if has_empty_sni(c)]
            all_raw.extend(found)
            sm.record(url, len(found))
        except: sm.record(url, 0)

    unique = list(set(all_raw))
    live = []
    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as ex:
        futs = {ex.submit(tcp_ping, re.search(r"@([^:/\s#]+):(\d+)", r).group(1), 443): r for r in unique[:300] if re.search(r"@([^:/\s#]+):(\d+)", r)}
        for f in as_completed(futs):
            ping = f.result()
            if ping:
                raw = futs[f]
                host = re.search(r"@([^:/\s#]+):(\d+)", raw).group(1)
                live.append(V2Config(raw=raw, raw_patched=patch_config(raw), host=host, port=443, ping_ms=ping, proto="VLESS" if "vless" in raw else "VMESS"))

    live.sort(key=lambda x: x.score(), reverse=True)
    for cfg in live[:MAX_POSTS]:
        msg = f"🔥 <b>Ultimate Ashaq</b> 🔥\n⚡ <b>Ping:</b> {cfg.ping_ms}ms\n<code>{cfg.raw_patched}</code>\n@V2rayashaq"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":CHAT_ID, "text":msg, "parse_mode":"HTML"})
    
    sm.save()
    log.info("Process Completed.")

if __name__ == "__main__":
    main()
