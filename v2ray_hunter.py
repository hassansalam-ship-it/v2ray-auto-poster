#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  🤖 V2RAY ULTIMATE HUNTER v8 — AI EDITION — ASHAQ TEAM                ║
# ║  هيكلية: VMESS/VLESS | WS | TLS | Port 443 | path=/ws*               ║
# ║  ذاكرة دائمة + كاش مؤقت + ترميم ذاتي + hard deadline                ║
# ╚══════════════════════════════════════════════════════════════════════════╝
from __future__ import annotations
import os, sys, re, json, time, ssl, socket, base64, random, hashlib
import threading, argparse, ipaddress, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("v2ray_hunt.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("V8")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG — كل الثوابت هنا
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
CHAT_ID     = "@V2rayashaq"
ADMIN_USER  = "@genie_2000"
CUSTOM_SNI  = os.environ.get("CUSTOM_SNI", "")
SUB_FILE    = "sub_link.txt"
TARGET_PORT = 443

MAX_POSTS        = 5
MAX_SUB_CONFIGS  = 200
STOP_AFTER_FOUND = 50      # يكفي 50 شغال ثم يتوقف
MAX_CHECK_RAWS   = 5000    # أقصى كونفيجات تُفحص في جولة

# ── Timeouts (كل قيمة مدروسة) ────────────────────────────────────────────
TCP_TIMEOUT   = 1.2   # TCP connect
SSL_TIMEOUT   = 2.0   # SSL handshake
PROBE_TIMEOUT = 2.0   # HTTP WS probe لكل bug host
FETCH_TIMEOUT = 6     # جلب مصدر واحد
MAX_PING_MS   = 500   # رفض فوق 500ms

# ── Workers ───────────────────────────────────────────────────────────────
FETCH_WORKERS = 80    # جلب مصادر
CHECK_WORKERS = 100   # فحص كونفيجات
GEO_WORKERS   = 30

# ── Hard Deadline — يُضبط في main() ──────────────────────────────────────
# 20 دقيقة = آمن بأي timeout (حتى لو YAML = 60m أو 6h)
HARD_DEADLINE_MINS = 20
_deadline: float   = 0.0    # يُحدَّد في main()

def deadline_ok() -> bool:
    """هل لا يزال لدينا وقت؟"""
    return _deadline == 0.0 or time.time() < _deadline

def deadline_left() -> int:
    """كم ثانية تبقت؟"""
    if _deadline == 0.0: return 9999
    return max(0, int(_deadline - time.time()))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUG HOSTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALL_BUG_HOSTS: list[str] = [
    "m.tiktok.com",
    "www.snapchat.com",
    "m.instagram.com",
    "m.facebook.com",
    "www.wechat.com",
    "m.youtube.com",
    "www.pubgmobile.com",
    "web.telegram.org",
    "open.spotify.com",
    "web.whatsapp.com",
    "invite.viber.com",
    "en.help.roblox.com",
]
TARGET_HOSTS: dict[str, list] = {
    "oodi": ALL_BUG_HOSTS[:],
    "zain": ["m.tiktok.com"],
    "voxi": [],
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI PERSISTENT MEMORY — يتعلم ويتحسن بين الجولات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_AI_FILE   = "ai_memory.json"
_ai_lock   = threading.Lock()
_AI_SCHEMA = {
    "v": 8, "runs": 0, "posted": 0, "last": "",
    "bug_wins": {}, "bug_fails": {},
    "src_hits": {}, "src_fails": {},
    "good_ips": [], "seen_md5": [],
}

def _ai_load() -> dict:
    try:
        d = json.loads(open(_AI_FILE, encoding="utf-8").read())
        for k, v in _AI_SCHEMA.items():
            d.setdefault(k, v)
        return d
    except Exception:
        return dict(_AI_SCHEMA)

def _ai_save(m: dict) -> None:
    try:
        m["seen_md5"] = m.get("seen_md5", [])[-5000:]
        m["good_ips"] = list(set(m.get("good_ips", [])))[-500:]
        open(_AI_FILE, "w", encoding="utf-8").write(
            json.dumps(m, ensure_ascii=False, separators=(",", ":")))
    except Exception as e:
        log.warning(f"AI save failed: {e}")

_AI: dict = _ai_load()

def ai_seen(raw: str) -> bool:
    h = hashlib.md5(raw.encode()).hexdigest()
    with _ai_lock:
        seen = _AI.setdefault("seen_md5", [])
        if h in seen: return True
        seen.append(h); return False

def ai_good_ip(ip: str) -> None:
    with _ai_lock:
        g = _AI.setdefault("good_ips", [])
        if ip not in g: g.append(ip)

def ai_bad_ip(ip: str) -> None:
    """يحفظ الـ IPs الفاشلة لتجنبها."""
    with _ai_lock:
        bad = _AI.setdefault("bad_ips", [])
        if ip not in bad: bad.append(ip)

def ai_is_bad_ip(ip: str) -> bool:
    with _ai_lock:
        return ip in _AI.get("bad_ips", [])

def ai_score_config(ping: int, probe_ms: int, nc: int) -> float:
    """يحسب نقاط الكونفيج — يُستخدم للترتيب الذكي قبل النشر."""
    score = 0.0
    # Ping score (أهم)
    if   ping < 80:  score += 40
    elif ping < 150: score += 30
    elif ping < 300: score += 20
    elif ping < 500: score += 10
    # Probe speed
    if   probe_ms < 200: score += 30
    elif probe_ms < 500: score += 20
    elif probe_ms < 900: score += 10
    # Compatible hosts count
    score += min(nc * 3, 30)
    return score

def ai_bug_update(bh: str, ok: bool) -> None:
    with _ai_lock:
        key = "bug_wins" if ok else "bug_fails"
        _AI[key][bh] = _AI[key].get(bh, 0) + 1

def ai_src_update(url: str, hits: int) -> None:
    with _ai_lock:
        if hits > 0:
            _AI["src_hits"][url] = _AI["src_hits"].get(url, 0) + hits
        else:
            _AI["src_fails"][url] = _AI["src_fails"].get(url, 0) + 1

def ai_order() -> list[str]:
    """يرتب Bug Hosts من الأفضل للأسوأ بناءً على التاريخ."""
    with _ai_lock:
        w = _AI["bug_wins"]; f = _AI["bug_fails"]
    def sc(h):
        ww = w.get(h, 0); ff = f.get(h, 0); t = ww + ff
        return ww / t if t else 0.5
    return sorted(ALL_BUG_HOSTS, key=sc, reverse=True)

def ai_dead() -> set:
    """مصادر فاشلة دائماً — تُحذف."""
    with _ai_lock:
        hits = _AI["src_hits"]; fails = _AI["src_fails"]
    dead = set()
    for url, ff in fails.items():
        hh = hits.get(url, 0); total = hh + ff
        if total >= 8 and hh == 0:
            dead.add(url)
    return dead

def ai_rank_sources(srcs: list) -> list:
    dead = ai_dead()
    live = [u for u in srcs if u not in dead]
    with _ai_lock:
        h = _AI["src_hits"]
    return sorted(live, key=lambda u: h.get(u, -1), reverse=True)

def ai_report() -> str:
    with _ai_lock:
        w = sum(_AI["bug_wins"].values())
        t = w + sum(_AI["bug_fails"].values())
        runs = _AI["runs"]
        top = sorted(_AI["bug_wins"].items(), key=lambda x: -x[1])[:2]
    rate = w / t * 100 if t else 0
    tops = ",".join(h.split(".")[1] + f"({n})" for h, n in top) or "—"
    return f"AI#{runs} {w}/{t}({rate:.0f}%) top:{tops} dead:{len(ai_dead())}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WORKING CACHE — كاش مؤقت للكونفيجات الشغالة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_CACHE_FILE  = "working_cache.json"
_CACHE_TTL   = 2 * 3600   # 2 ساعات (أقصر = جودة أحدث)

def cache_load() -> list[dict]:
    try:
        data  = json.loads(open(_CACHE_FILE, encoding="utf-8").read())
        fresh = [c for c in data if time.time() - c.get("ts", 0) < _CACHE_TTL]
        log.info(f"♻️  Cache: {len(fresh)}/{len(data)} configs (< {_CACHE_TTL//3600}h)")
        return fresh
    except Exception:
        return []

def cache_save(cfgs: list) -> None:
    try:
        data = []
        for c in cfgs[:200]:
            data.append({
                "raw": c.raw, "raw_p": c.raw_patched,
                "host": c.host, "port": c.port,
                "proto": c.proto, "ping": c.ping_ms, "probe": c.probe_ms,
                "compat": c.compatible_hosts, "best": c.best_bug_host,
                "cc": c.country_code, "country": c.country,
                "isp": c.isp, "is_cf": c.is_cf, "is_vps": c.is_vps,
                "diag": c.ai_diagnosis, "ssl": c.ssl_ok,
                "ts": time.time(),
            })
        open(_CACHE_FILE, "w", encoding="utf-8").write(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        log.info(f"💾 Cache saved: {len(data)} configs")
    except Exception as e:
        log.warning(f"Cache save failed: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CF IP DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_CF_CIDRS = [
    "103.21.244.0/22","103.22.200.0/22","103.31.4.0/22",
    "104.16.0.0/13","104.24.0.0/14","108.162.192.0/18",
    "131.0.72.0/22","141.101.64.0/18","162.158.0.0/15",
    "172.64.0.0/13","173.245.48.0/20","188.114.96.0/20",
    "190.93.240.0/20","197.234.240.0/22","198.41.128.0/17",
]
_CF_NETS = [ipaddress.ip_network(c) for c in _CF_CIDRS]

def is_cf_ip(ip: str) -> bool:
    try:
        a = ipaddress.ip_address(ip)
        return any(a in n for n in _CF_NETS)
    except Exception:
        return False

CF_KEYWORDS  = ("cloudflare","cf-","cfssl","cdn","1.1.1.","104.16.","104.17.","104.18.")
VPS_KEYWORDS = ("vps","server","host","vir","linode","digital","vultr","aws","azure","hetz")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HTTP SESSION — anti-bot headers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]
_SESS_LOCAL = threading.local()

def _headers() -> dict:
    return {
        "User-Agent":      random.choice(_UAS),
        "Accept":          "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "Cache-Control":   "no-cache",
    }

def _sess() -> requests.Session:
    s = getattr(_SESS_LOCAL, "s", None)
    if s is None:
        s = requests.Session()
        s.verify = False
        _SESS_LOCAL.s = s
    return s

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dataclass
class V2Config:
    raw:              str
    raw_patched:      str
    host:             str
    port:             int
    ping_ms:          int
    proto:            str
    original_sni:     str
    injected_sni:     str
    ssl_ok:           bool  = False
    ssl_cert_cn:      str   = ""
    country_code:     str   = "??"
    country:          str   = "Unknown"
    isp:              str   = ""
    is_vps:           bool  = False
    is_cf:            bool  = False
    compatible_hosts: list  = field(default_factory=list)
    best_bug_host:    str   = ""
    probe_ms:         int   = 0
    ai_diagnosis:     str   = ""
    server_type:      str   = ""

    def score(self) -> int:
        s  = 600 if self.is_cf  else 0
        s += 400 if self.is_vps else 0
        s += 300 if self.ssl_ok else 0
        oodi = set(TARGET_HOSTS["oodi"]); zain = set(TARGET_HOSTS["zain"])
        compat = set(self.compatible_hosts)
        s += len(compat & oodi) * 800
        s += len(compat & zain) * 700
        if len(compat) >= len(ALL_BUG_HOSTS): s += 2000
        if   self.probe_ms < 100: s += 1000
        elif self.probe_ms < 200: s += 700
        elif self.probe_ms < 400: s += 400
        if   self.ping_ms  < 80:  s += 800
        elif self.ping_ms  < 150: s += 500
        elif self.ping_ms  < 300: s += 300
        return s

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SNI EXTRACTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_SNI_KEYS = ("sni","host","peer","servername","server-name")
_CONFIG_RE = re.compile(r"(?:vless|vmess)://[^\s#\"'<>\]\[]+")

def extract_sni(raw: str) -> str:
    if raw.startswith("vmess://"):
        try:
            b64 = raw[8:]
            for pad in ("","=","==","==="):
                try:
                    obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                    for k in _SNI_KEYS:
                        if obj.get(k): return str(obj[k])
                    return ""
                except Exception: continue
        except Exception: pass
        return ""
    for k in _SNI_KEYS:
        m = re.search(rf"[?&]{k}=([^&\s#]+)", raw, re.IGNORECASE)
        if m and m.group(1): return m.group(1)
    return ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STRUCTURE VALIDATION — هيكلية السيرفر الشغال
#  VMESS WS TLS 443 AID=0 path=/ws*
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_PATH_RE = re.compile(
    r"^/(?:ws|vws|linkvws|link|v2ray|proxy|grpc|wss?|ray|xray|"
    r"vmess|vless|relay|[a-z0-9]{3,20})(?:/.*)?$",
    re.IGNORECASE
)

def is_valid_struct(raw: str) -> bool:
    if raw.startswith("vmess://"):
        try:
            b64 = raw[8:]
            for pad in ("","=","==","==="):
                try:
                    obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                    break
                except Exception: continue
            else: return False
            if str(obj.get("port","")) != "443":                 return False
            if obj.get("net","") not in ("ws","websocket"):      return False
            if obj.get("tls","") not in ("tls","xtls"):          return False
            if str(obj.get("aid","0")) not in ("0",""):           return False
            path = obj.get("path","")
            if path and not _PATH_RE.match(path):                return False
            return True
        except Exception: return False
    else:
        rl = raw.lower()
        if "type=ws" not in rl and "net=ws" not in rl:   return False
        if ":443" not in raw:                              return False
        if "security=tls" not in rl and "tls" not in rl: return False
        m = re.search(r"[?&]path=([^&\s#]+)", raw, re.IGNORECASE)
        if m:
            path = m.group(1).replace("%2F","/").replace("%2f","/")
            if not _PATH_RE.match(path): return False
        return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EMBEDDED HOST DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ── الحل الجذري: Whitelist بدل Blacklist ─────────────────────────────────
# نقبل فقط:  (1) SNI فارغ  (2) أحد Bug Hosts بالضبط  (3) IP مباشر
# نرفض كل شيء آخر بدون استثناء — nodejs.org, example.com, etc.
_IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
_BUG_HOSTS_SET = {bh.lower() for bh in ALL_BUG_HOSTS}

def is_embedded(raw: str) -> bool:
    """
    Whitelist filter — الحل الجذري لـ Downlink=0B.

    ✅ مقبول: SNI فارغ (المستخدم يحط هوسته)
    ✅ مقبول: SNI = أحد Bug Hosts المعتمدة بالضبط
    ✅ مقبول: SNI = IP مباشر (قد يكون CF server)
    ❌ مرفوض: أي domain آخر (nodejs.org, example.com, speedtest.net...)

    السبب: أي SNI غير معتمد = Downlink=0B مضمون في NPV Tunnel.
    """
    sni = extract_sni(raw).lower().strip()
    # فارغ = نظيف (المستخدم يحط هوسته)
    if not sni: return False
    # Bug Host معتمد = نظيف
    if sni in _BUG_HOSTS_SET: return False
    # IP مباشر = نظيف (CF IP)
    if _IP_RE.match(sni): return False
    # كل شيء آخر = embedded = مرفوض
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PATCH ENGINE — host/sni فارغ في الكونفيج النهائي
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _sp(url: str, key: str, val: str) -> str:
    pat = re.compile(rf"([?&]{re.escape(key)}=)[^&\s#]*", re.IGNORECASE)
    if pat.search(url):
        return pat.sub(lambda m: m.group(1) + val, url)
    sep = "&" if "?" in url else "?"
    return url + f"{sep}{key}={val}"

def _dp(url: str, key: str) -> str:
    url = re.sub(rf"[?&]{re.escape(key)}=[^&\s#]*", "", url, flags=re.IGNORECASE)
    url = re.sub(r"\?&", "?", url)
    return re.sub(r"[?&]$", "", url)

def patch_final(raw: str) -> str:
    """الكونفيج النهائي: host='' sni='' فارغ — المستخدم يحط هوسته."""
    if raw.startswith("vmess://"):
        try:
            b64 = raw[8:]
            for pad in ("","=","==","==="):
                try:
                    obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                    break
                except Exception: continue
            else: return raw
            obj["sni"] = ""; obj["host"] = ""
            for k in ("peer","servername","server-name"):
                obj.pop(k, None)
            obj["net"] = "ws"; obj["path"] = "/ws"
            obj["tls"] = "tls"; obj["allowInsecure"] = True
            obj["skip-cert-verify"] = True
            return "vmess://" + base64.b64encode(
                json.dumps(obj, ensure_ascii=False, separators=(",",":")).encode()
            ).decode()
        except Exception: return raw
    else:
        r = raw
        for k in ("sni","host"):       r = _sp(r, k, "")
        for k in ("peer","servername","server-name"): r = _dp(r, k)
        r = _sp(r, "path",         "%2Fws")
        r = _sp(r, "type",         "ws")
        r = _sp(r, "security",     "tls")
        r = _sp(r, "allowInsecure","1")
        return r

def patch_for_probe(raw: str, bh: str) -> str:
    """نسخة مؤقتة للفحص فقط — تحقن bug host."""
    if raw.startswith("vmess://"):
        try:
            b64 = raw[8:]
            for pad in ("","=","==","==="):
                try:
                    obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                    break
                except Exception: continue
            else: return raw
            obj["sni"] = bh; obj["host"] = bh
            obj["net"] = "ws"; obj["path"] = "/ws"
            obj["tls"] = "tls"; obj["allowInsecure"] = True
            return "vmess://" + base64.b64encode(
                json.dumps(obj, ensure_ascii=False, separators=(",",":")).encode()
            ).decode()
        except Exception: return raw
    r = raw
    for k in ("sni","host","peer","servername"): r = _sp(r, k, bh)
    r = _sp(r, "type",         "ws")
    r = _sp(r, "security",     "tls")
    r = _sp(r, "allowInsecure","1")
    return r

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROBE ENGINE — الفحص الحقيقي
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def tcp_ping(host: str, port: int) -> Optional[int]:
    try:
        t0 = time.perf_counter()
        with socket.create_connection((host, port), timeout=TCP_TIMEOUT):
            return int((time.perf_counter() - t0) * 1000)
    except Exception:
        return None

def _ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    return ctx

def ssl_check(host: str, port: int) -> tuple[bool, str]:
    try:
        ctx  = _ssl_ctx()
        conn = socket.create_connection((host, port), timeout=SSL_TIMEOUT)
        conn.settimeout(SSL_TIMEOUT)
        sock = ctx.wrap_socket(conn, server_hostname=host)
        cert = sock.getpeercert()
        sock.close()
        cn = ""
        if cert:
            for field in cert.get("subject",()):
                for k, v in field:
                    if k == "commonName": cn = v; break
        return True, cn
    except ssl.SSLError:
        return False, ""
    except Exception:
        return False, ""

def ws_probe(host: str, port: int, bug_host: str, path: str = "/ws") -> Optional[int]:
    """
    STRICT 101-ONLY PROBE — الضمان الوحيد أن Downlink ≠ 0B

    لماذا 101 فقط؟
    ─────────────────────────────────────────────────────────
    CF يرد 400+CF-Ray لأي طلب على CF IPs — حتى لو الـ UUID غير موجود
    هذا يعني: probe يقبل → ينشر → Uplink=KB + Downlink=0B

    101 Switching Protocols لا يحدث إلا إذا:
    ① CF استقبل الـ WebSocket
    ② وجّهه للـ Worker الصحيح (UUID المسجل)
    ③ الـ Worker رد بـ 101

    = الـ proxy chain نشط من أوله لآخره = Downlink ✅
    """
    if not deadline_ok(): return None
    ctx = _ssl_ctx()
    probe_paths = [path] if path != "/ws" else [path, "/linkvws", "/vws"]
    for try_path in probe_paths:
        try:
            t0   = time.perf_counter()
            conn = socket.create_connection((host, port), timeout=PROBE_TIMEOUT)
            conn.settimeout(PROBE_TIMEOUT)
            sock = ctx.wrap_socket(conn, server_hostname=bug_host)
            key  = base64.b64encode(os.urandom(16)).decode()
            req  = (
                f"GET {try_path} HTTP/1.1\r\nHost: {bug_host}\r\n"
                f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
                f"Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits\r\n"
                f"Origin: https://{bug_host}\r\n"
                f"User-Agent: Go-http-client/1.1\r\n\r\n"
            )
            sock.sendall(req.encode())
            resp = b""
            dl   = time.perf_counter() + PROBE_TIMEOUT
            while time.perf_counter() < dl:
                try:
                    chunk = sock.recv(4096)
                    if not chunk: break
                    resp += chunk
                    if b"\r\n\r\n" in resp: break
                except Exception: break
            elapsed = int((time.perf_counter() - t0) * 1000)
            try: sock.close()
            except Exception: pass
            if not resp: continue
            first  = resp.split(b"\r\n")[0].decode(errors="ignore").strip()
            if not first.startswith("HTTP"): continue
            parts  = first.split()
            status = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
            rl     = resp.lower()
            # ── القبول الوحيد: 101 = proxy chain نشط ─────────────────
            if status == 101:
                log.debug(f"  ✅101 {host}←{bug_host}{try_path} {elapsed}ms")
                ai_bug_update(bug_host, True)
                return elapsed
            # VPS فقط: 200 + Upgrade header = WebSocket server حقيقي
            if status == 200:
                is_cf = b"cf-ray:" in rl or b"server: cloudflare" in rl
                has_ws_headers = (b"upgrade:" in rl or b"sec-websocket-accept" in rl)
                if has_ws_headers and not is_cf:
                    log.debug(f"  ✅200+WS(VPS) {host}←{bug_host} {elapsed}ms")
                    ai_bug_update(bug_host, True)
                    return elapsed
            # ── رفض كل شيء آخر ──────────────────────────────────────
            # 400+CF-Ray = CF يعمل لكن proxy UUID ميت = Downlink=0B
            # 530 = SNI خاطئ, 5xx = ميت, فارغ = timeout
            log.debug(f"  ❌{status} {host}←{bug_host}")
        except Exception as e:
            log.debug(f"  ❌{type(e).__name__} {host}←{bug_host}")
    ai_bug_update(bug_host, False)
    return None


def extract_path(raw: str) -> str:
    """يستخرج WS path من الكونفيج."""
    if raw.startswith("vmess://"):
        try:
            b64 = raw[8:]
            for pad in ("","=","==","==="):
                try:
                    obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                    p = obj.get("path","")
                    return p if p else "/ws"
                except Exception: continue
        except Exception: pass
        return "/ws"
    m = re.search(r"[?&]path=([^&\s#]+)", raw, re.IGNORECASE)
    if m:
        p = m.group(1).replace("%2F","/").replace("%2f","/")
        return p if p.startswith("/") else "/" + p
    return "/ws"

def multi_probe(host: str, port: int, raw: str = "") -> tuple[list[str], str, int]:
    """يفحص كل Bug Host بالتوازي مع path الكونفيج الحقيقي."""
    if not deadline_ok(): return [], "", 0
    ordered  = ai_order()
    cfg_path = extract_path(raw) if raw else "/ws"
    timings: dict[str, int] = {}

    def _probe_bh(bh: str) -> Optional[int]:
        ms = ws_probe(host, port, bh, path=cfg_path)
        if ms is not None: return ms
        if cfg_path not in ("/ws", "/"):
            return ws_probe(host, port, bh, path="/ws")
        return None

    with ThreadPoolExecutor(max_workers=min(len(ordered), 12)) as ex:
        futs = {ex.submit(_probe_bh, bh): bh for bh in ordered}
        for fut in as_completed(futs):
            bh = futs[fut]
            try:
                ms = fut.result()
                if ms is not None: timings[bh] = ms
            except Exception: pass
    if not timings: return [], "", 0
    compat = list(timings)
    best   = min(timings, key=timings.get)
    return compat, best, timings[best]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHECK_RAW — الفحص الكامل لكونفيج واحد
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_raw(raw: str) -> Optional[V2Config]:
    # ── Guards ──────────────────────────────────────────────────────────────
    if not deadline_ok():      return None
    if ai_seen(raw):            return None

    m = re.search(r"@([^:/\s\]#]+):(\d+)", raw)
    if not m: return None
    host = m.group(1)
    try:    port = int(m.group(2))
    except ValueError: return None
    if port != TARGET_PORT:     return None
    if not is_valid_struct(raw): return None
    if is_embedded(raw):         return None

    proto    = "VLESS" if raw.startswith("vless://") else "VMESS"
    orig_sni = extract_sni(raw)

    # ── 1. TCP ───────────────────────────────────────────────────────────────
    ping = tcp_ping(host, port)
    if ping is None or ping > MAX_PING_MS: return None

    # ── 2. SSL ───────────────────────────────────────────────────────────────
    ssl_ok, ssl_cn = ssl_check(host, port)

    # ── 3. CF/VPS ────────────────────────────────────────────────────────────
    try:    ip = socket.gethostbyname(host)
    except Exception: ip = ""
    # رفض الـ IPs الفاشلة المعروفة
    if ip and ai_is_bad_ip(ip): return None
    is_cf  = (is_cf_ip(ip) if ip else False) or \
             any(k in (host+raw).lower() for k in CF_KEYWORDS)
    is_vps = any(k in (host+raw).lower() for k in VPS_KEYWORDS)

    # ── 4. Bug-Host Probe — الفلتر الحقيقي ─────────────────────────────────
    if CUSTOM_SNI:
        ms = ws_probe(host, port, CUSTOM_SNI)
        if ms is None: return None
        compat, best, probe_ms = [CUSTOM_SNI], CUSTOM_SNI, ms
    else:
        compat, best, probe_ms = multi_probe(host, port, raw)
        # يجب أن ينجح على الأقل هوستين = إحصائياً موثوق (ليس false positive)
        if len(compat) < 2: return None
        # probe بطيء = اتصال ضعيف = تجربة سيئة
        if probe_ms > 1200: return None

    # ── 5. Final Patch (host فارغ) ───────────────────────────────────────────
    raw_p = patch_final(raw)
    if ip: ai_good_ip(ip)

    # ── Diagnosis ────────────────────────────────────────────────────────────
    nc   = len(compat); nt = len(ALL_BUG_HOSTS)
    ops  = []
    if set(compat) & set(TARGET_HOSTS["oodi"]): ops.append("Oodi")
    if set(compat) & set(TARGET_HOSTS["zain"]): ops.append("Zain")
    q    = "🏆Elite" if nc>=8 else "⭐⭐⭐" if nc>=4 else "⭐⭐" if nc>=2 else "⭐"
    tp   = ("CF⚡" if is_cf else "") + (" VPS🚀" if is_vps else "")
    diag = f"✅{q}|{tp}|{nc}/{nt}hosts|{ping}ms|{'+'.join(ops) or '?'}"

    log.info(f"✅ {host}|{proto}|{nc}/{nt}|{ping}ms→{best}")
    return V2Config(
        raw=raw, raw_patched=raw_p,
        host=host, port=port, ping_ms=ping, proto=proto,
        original_sni=orig_sni, injected_sni="",
        ssl_ok=ssl_ok, ssl_cert_cn=ssl_cn,
        is_cf=is_cf, is_vps=is_vps,
        compatible_hosts=compat, best_bug_host=best,
        probe_ms=probe_ms, ai_diagnosis=diag,
        server_type="CF" if is_cf else "VPS",
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FETCH ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _fetch(url: str) -> list[str]:
    if not deadline_ok(): return []
    try:
        time.sleep(random.uniform(0.02, 0.15))
        h = _headers()
        if "t.me/s/" in url:
            h["Referer"] = "https://t.me/"
        r = _sess().get(url, timeout=FETCH_TIMEOUT, headers=h,
                        allow_redirects=True, stream=False)
        if r.status_code == 429:
            time.sleep(min(int(r.headers.get("Retry-After", 5)), 8))
            r = _sess().get(url, timeout=FETCH_TIMEOUT, headers=_headers())
        if r.status_code not in (200, 206): return []
        text = r.text

        found = _CONFIG_RE.findall(text)

        if not found:
            b = re.sub(r"\s+", "", text)
            for pad in ("","=","=="):
                try:
                    dec   = base64.b64decode(b + pad).decode("utf-8", errors="ignore")
                    found = _CONFIG_RE.findall(dec)
                    if found: break
                except Exception: continue

        if not found:
            for line in text.splitlines():
                line = line.strip()
                if len(line) > 20 and not line.startswith(("vless://","vmess://")):
                    try:
                        dec   = base64.b64decode(line + "==").decode("utf-8", errors="ignore")
                        found.extend(_CONFIG_RE.findall(dec))
                    except Exception: pass

        if not found and "t.me" in url:
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = (clean.replace("&amp;","&").replace("&#43;","+")
                         .replace("&#61;","=").replace("%3A",":").replace("%2F","/"))
            found = _CONFIG_RE.findall(clean)

        out = list(dict.fromkeys(c for c in found if ":443" in c))
        if out: log.info(f"✓ {len(out):>4}  ←  {url[:65]}")
        return out

    except requests.exceptions.SSLError:
        try:
            r2 = requests.get(url, timeout=FETCH_TIMEOUT, headers=_headers(), verify=False)
            return list(dict.fromkeys(c for c in _CONFIG_RE.findall(r2.text) if ":443" in c))
        except Exception: return []
    except Exception: return []



SOURCES = [
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
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub6.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub7.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub8.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity_base64.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
    "https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_base64_Sub.txt",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/All.txt",
    "https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/Vmess.txt",
    "https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/Vless.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/combine/v2raySub.txt",
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free",
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/v2ray/v2raysub",
    "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription1",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription2",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription3",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription4",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription5",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription6",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription7",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription8",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all3",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vless",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub",
    "https://raw.githubusercontent.com/itsyebekhe/HiN-VPN/main/subscription/normal/mix",
    "https://raw.githubusercontent.com/itsyebekhe/HiN-VPN/main/subscription/base64/mix",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2",
    "https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/merged.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server2.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server3.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server4.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server5.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server6.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server7.txt",
    "https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt",
    "https://raw.githubusercontent.com/IranianCypherpunks/sub/main/config",
    "https://raw.githubusercontent.com/IranianCypherpunks/sub/main/configB64",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/1/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/2/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/3/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/4/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/5/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/6/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/7/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/8/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/9/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/10/config",
    "https://raw.githubusercontent.com/vxiaov/free_proxies/main/v2ray/v2ray.share.txt",
    "https://raw.githubusercontent.com/vxiaov/free_proxies/main/vmess/vmess.share.txt",
    "https://raw.githubusercontent.com/vxiaov/free_proxies/main/vless/vless.share.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/all_configs.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/vless_configs.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/vmess_configs.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/G-Core.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/openai.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/cloudflare.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/NiREvil.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/CF-IPs.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/DigiCloud.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Proton.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/GlobalVPN.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/TurboVPN.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/SkyVPN.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/SVR.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Sentry.md",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
    "https://raw.githubusercontent.com/Surfboardv2ray/v2ray-cf/main/sub",
    "https://raw.githubusercontent.com/Surfboardv2ray/Proxy/main/Raw",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vless",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vmess",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/subs/v2ray",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Mix/mix.txt",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Vmess/vmess.txt",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Vless/vless.txt",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/vmess.txt",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/vless.txt",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/mix.txt",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/vmess",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/vless",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/mix.txt",
    "https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/vless.txt",
    "https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/vmess.txt",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/sub",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/best",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_outside_iran.txt",
    "https://raw.githubusercontent.com/ermaozi01/free_clash_vpn/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/node.txt",
    "https://raw.githubusercontent.com/AliAnonymous/v2configs/main/All/config.txt",
    "https://raw.githubusercontent.com/AliAnonymous/v2configs/main/vmess/config.txt",
    "https://raw.githubusercontent.com/AliAnonymous/v2configs/main/vless/config.txt",
    "https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/merged.txt",
    "https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/vless.txt",
    "https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/vmess.txt",
    "https://raw.githubusercontent.com/dimzon/scaling-robot/main/all",
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list.yml",
    "https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/mix_base64",
    "https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/mix",
    "https://raw.githubusercontent.com/Iam-HealthS/Vless-Vmess-Trojan/main/subscription/vless",
    "https://raw.githubusercontent.com/Iam-HealthS/Vless-Vmess-Trojan/main/subscription/vmess",
    "https://raw.githubusercontent.com/hermansh-id/belajar-script-proxy/main/sub/vmess",
    "https://raw.githubusercontent.com/hermansh-id/belajar-script-proxy/main/sub/vless",
    "https://raw.githubusercontent.com/GalaxyCom2023/v2ray/main/sub",
    "https://raw.githubusercontent.com/GalaxyCom2023/Xray-sub/main/sub",
    "https://raw.githubusercontent.com/free18/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/mganotas/outbound/main/raw.txt",
    "https://raw.githubusercontent.com/mganotas/outbound/main/raw_b64.txt",
    "https://raw.githubusercontent.com/4everfree/FreeNode/master/md/freecpn.md",
    "https://raw.githubusercontent.com/Moli-X/Resources/main/Subscription/Collect.txt",
    "https://raw.githubusercontent.com/FreeVpnSubscriber/FreeVpn/main/v2ray.txt",
    "https://raw.githubusercontent.com/V2Hub/V2Hub.github.io/main/subs/v2ray",
    "https://raw.githubusercontent.com/V2Hub/V2Hub.github.io/main/subs/vmess",
    "https://raw.githubusercontent.com/V2Hub/V2Hub.github.io/main/subs/vless",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/default.txt",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/speed.txt",
    "https://raw.githubusercontent.com/proxypool404/v2ray/main/all.txt",
    "https://raw.githubusercontent.com/proxypool404/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/proxypool404/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/Airscker/V2Ray-Config-Pool/main/all.txt",
    "https://raw.githubusercontent.com/MrHedgehogArmenian/proxy/main/all.txt",
    "https://raw.githubusercontent.com/MrHedgehogArmenian/proxy/main/v2ray.txt",
    "https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml",
    "https://raw.githubusercontent.com/vpn0/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/VPN-Speed/V2ray-Config/main/sub.txt",
    "https://raw.githubusercontent.com/Misaka-blog/chromego_merge/main/sub/merged_proxies_new.yaml",
    "https://raw.githubusercontent.com/vveg26/chromego_merge/main/sub/merged_proxies_new.yaml",
    "https://raw.githubusercontent.com/jason5ng32/MyIP/main/public/v2ray.txt",
    "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/topfreeproxy/V2RaySub.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/proxies/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/proxies/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/proxies/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/proxies/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/proxies/mix",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/normal/mix",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/normal/vmess",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/normal/vless",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/sub.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Atlas.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Thunder.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/TotalVPN.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/OvpnSpider.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/PandaVPN.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/S-210-209.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/speedtest.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Mullvad.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Windscribe.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Opera.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Lantern.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/HMA.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Hotspot.md",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/TouchVPN.md",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/11/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/12/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/13/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/14/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/15/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/16/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/17/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/18/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/19/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/20/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/21/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/22/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/23/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/24/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/25/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/26/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/27/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/28/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/29/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/30/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/31/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/32/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/33/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/34/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/35/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/36/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/37/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/38/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/39/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/40/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/41/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/42/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/43/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/44/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/45/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/46/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/47/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/48/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/49/config",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/50/config",
    "https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Raw",
    "https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Vless",
    "https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Vmess",
    "https://raw.githubusercontent.com/peasoft/NoFilter/main/sub.meta.yaml",
    "https://raw.githubusercontent.com/abshare/abshare.github.io/main/README.md",
    "https://raw.githubusercontent.com/xiyaowong/freeFQ/main/sub",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/vmess/data.txt",
    "https://raw.githubusercontent.com/EAimTY/eaimty.github.io/master/proxies/vmess.txt",
    "https://raw.githubusercontent.com/cjx82630/clashconfig/master/clash5.yaml",
    "https://raw.githubusercontent.com/liwei2633/v2rayse/main/v2ray",
    "https://raw.githubusercontent.com/nikitattt/v2ray-subs/main/subs/sub.txt",
    "https://raw.githubusercontent.com/bugflux/free-vpn/main/v2ray",
    "https://raw.githubusercontent.com/FreeVpnLive/FreeVpnLive/main/v2ray.txt",
    "https://raw.githubusercontent.com/wudongdefeng/free/main/freesub/all.yaml",
    "https://raw.githubusercontent.com/LorenEteval/Furious/Origin/furious/Asset/subscription",
    "https://raw.githubusercontent.com/alibasha/V2ray-Config/main/mixed",
    "https://raw.githubusercontent.com/GalaxyCom2023/v2ray/main/sub",
    "https://raw.githubusercontent.com/KingdomProxy/v2ray-config/main/sub.txt",
    "https://raw.githubusercontent.com/Dreamer-Paul/Sub/main/V2",
    "https://raw.githubusercontent.com/vlessx/vlessx/main/vless.txt",
    "https://raw.githubusercontent.com/xjp9153/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/JohnHoos/JohnHoos/main/nodes.txt",
    "https://raw.githubusercontent.com/freev2rayserver/freev2rayserver/main/v2ray.txt",
    "https://raw.githubusercontent.com/khatamber/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/ZxxSin/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/goog22/v2ray-configs/main/warp.txt",
    "https://raw.githubusercontent.com/Parsasafari/V2ray-Config/main/configs.txt",
    "https://raw.githubusercontent.com/AbolhasanKedkiGhadi/FreeV2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/EasternNetProxies/EasternNetProxies/main/sub",
    "https://raw.githubusercontent.com/moeinf/v2ray/main/config.txt",
    "https://raw.githubusercontent.com/Ramin-Setoodehnia/v2ray/main/config",
    "https://raw.githubusercontent.com/mehdi-farsi/proxy/main/v2ray",
    "https://raw.githubusercontent.com/soudagar/V2ray/main/configs.txt",
    "https://raw.githubusercontent.com/V2rayfreeb/V2rayfreeb/main/V2ray.txt",
    "https://raw.githubusercontent.com/alfredhuang426/free-v2ray/main/config.txt",
    "https://raw.githubusercontent.com/PerFectHasH/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/openrunner/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/Hediyeh-dark/Proxy/main/vmess.txt",
    "https://raw.githubusercontent.com/Hediyeh-dark/Proxy/main/vless.txt",
    "https://raw.githubusercontent.com/HuTianQi030/-/main/y",
    "https://raw.githubusercontent.com/mystica553/vless/main/vless.txt",
    "https://raw.githubusercontent.com/Flik6/getNode/main/v2ray.txt",
    "https://raw.githubusercontent.com/freebaipiao/freebaipiao/main/zz.txt",
    "https://raw.githubusercontent.com/huwo1/proxy_nodes/main/base64.md",
    "https://raw.githubusercontent.com/huwo1/proxy_nodes/main/all.md",
    "https://raw.githubusercontent.com/IQ-deficient/shilling/main/base64",
    "https://raw.githubusercontent.com/HuiYuAI/XMRig/main/v2.txt",
    "https://raw.githubusercontent.com/amirali-dashti/v2ray-free/main/all.txt",
    "https://raw.githubusercontent.com/zeroc0de2022/TG-Scrapper-V2/main/out/result.txt",
    "https://raw.githubusercontent.com/bevccy/v2ray_share/main/v2ray",
    "https://raw.githubusercontent.com/shahpasandfun/shahpasan/main/configs.txt",
    "https://raw.githubusercontent.com/zargari956/zargari956/main/v2ray.txt",
    "https://raw.githubusercontent.com/bitefu/bitefu/main/v2ray.txt",
    "https://raw.githubusercontent.com/FreeNodes1/FreeNodes1/main/sub",
    "https://raw.githubusercontent.com/themohammadsa/free-v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/vpnhat/vpnhat/main/v2ray.txt",
    "https://raw.githubusercontent.com/Godisagirl/Proxy-Sub/main/Sub_base64/All",
    "https://raw.githubusercontent.com/Godisagirl/Proxy-Sub/main/Sub_normal/All",
    "https://raw.githubusercontent.com/oneclick-ai/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/B85/v2rayProxy/main/sub.txt",
    "https://raw.githubusercontent.com/ProxiesCollection/ProxiesCollection/main/sub",
    "https://raw.githubusercontent.com/DaRealFreak/cloudflare-ip-tester/master/testing/v2ray",
    "https://raw.githubusercontent.com/mlabalabala/v2ray-node/main/nodefree4clash.yaml",
    "https://raw.githubusercontent.com/v2rayse/node-list/main/wg.yaml",
    "https://raw.githubusercontent.com/ZywChannel/free/main/sub",
    "https://raw.githubusercontent.com/FQrabbit/SSTap-Rule/master/sub",
    "https://raw.githubusercontent.com/hossein-mohseni/v2ray/main/hossein-mohseni",
    "https://raw.githubusercontent.com/EminTorun007/free-vpn/main/v2ray.txt",
    "https://raw.githubusercontent.com/DamianHaynes/v2ray_clash/main/all.yaml",
    "https://raw.githubusercontent.com/ProxyManaager/proxy/main/sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_yaml.yml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/provider/Config.yaml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/mixed",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/vmess",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/vless",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all2",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vmess",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/type/vless",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/type/vmess",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/type/trojan",
    "https://raw.githubusercontent.com/ermaozi01/free_clash_vpn/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/adiwzx/freenode/main/adispeed.txt",
    "https://raw.githubusercontent.com/adiwzx/freenode/main/adiguard.txt",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub3",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub4",
    "https://raw.githubusercontent.com/free18/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/free18/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/free18/v2ray/main/mixed.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/clash.yaml",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/vmess",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/vless",
    "https://raw.githubusercontent.com/ts-sf/fly/main/clash",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/clash.yml",
    "https://raw.githubusercontent.com/aiboboxx/clashfree/main/clash.yml",
    "https://raw.githubusercontent.com/aiboboxx/clashfree/main/v2",
    "https://raw.githubusercontent.com/freefq/free/master/clash.yml",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/clash.yaml",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt",
    "https://raw.githubusercontent.com/m-alruize/V2ray-configs/main/configs.txt",
    "https://raw.githubusercontent.com/m-alruize/V2ray-configs/main/vmess.txt",
    "https://raw.githubusercontent.com/m-alruize/V2ray-configs/main/vless.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/ssr_sub.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/v2sub.txt",
    "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/combine/clashSub.txt",
    "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/topfreeproxy/ClashSub.txt",
    "https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/trojan.txt",
    "https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/clash.yaml",
    "https://raw.githubusercontent.com/IranianCypherpunks/sub/main/clash",
    "https://raw.githubusercontent.com/IranianCypherpunks/sub/main/shadowsocks",
    "https://raw.githubusercontent.com/HuiYuAI/XMRig/main/v1.txt",
    "https://raw.githubusercontent.com/HuiYuAI/XMRig/main/v3.txt",
    "https://raw.githubusercontent.com/HuiYuAI/XMRig/main/v4.txt",
    "https://raw.githubusercontent.com/vxiaov/free_proxies/main/clash/clash.provider.yaml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/soudagar/V2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/soudagar/V2ray/main/vless.txt",
    "https://raw.githubusercontent.com/soudagar/V2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/vless/data.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",
    "https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/vless",
    "https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/vmess",
    "https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/clash",
    "https://raw.githubusercontent.com/openrunner/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/openrunner/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/openrunner/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/a2470982985/getNode/main/clash.yaml",
    "https://raw.githubusercontent.com/a2470982985/getNode/main/vless.txt",
    "https://raw.githubusercontent.com/a2470982985/getNode/main/vmess.txt",
    "https://raw.githubusercontent.com/oneclick-ai/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/oneclick-ai/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/oneclick-ai/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/FreeVpnLive/FreeVpnLive/main/clash.yaml",
    "https://raw.githubusercontent.com/FreeVpnLive/FreeVpnLive/main/vmess.txt",
    "https://raw.githubusercontent.com/FreeVpnLive/FreeVpnLive/main/vless.txt",
    "https://raw.githubusercontent.com/V2rayfreeb/V2rayfreeb/main/clash.yaml",
    "https://raw.githubusercontent.com/vpnhat/vpnhat/main/clash.yaml",
    "https://raw.githubusercontent.com/vpnhat/vpnhat/main/vmess.txt",
    "https://raw.githubusercontent.com/vpnhat/vpnhat/main/vless.txt",
    "https://raw.githubusercontent.com/bugflux/free-vpn/main/vmess",
    "https://raw.githubusercontent.com/bugflux/free-vpn/main/vless",
    "https://raw.githubusercontent.com/bugflux/free-vpn/main/clash",
    "https://raw.githubusercontent.com/khatamber/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/khatamber/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/khatamber/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/VPN-Speed/V2ray-Config/main/vmess.txt",
    "https://raw.githubusercontent.com/VPN-Speed/V2ray-Config/main/vless.txt",
    "https://raw.githubusercontent.com/VPN-Speed/V2ray-Config/main/clash.yaml",
    "https://raw.githubusercontent.com/amirhoseindavarpanah/v2ray/main/sub",
    "https://raw.githubusercontent.com/amirhoseindavarpanah/v2ray/main/vmess",
    "https://raw.githubusercontent.com/amirhoseindavarpanah/v2ray/main/vless",
    "https://raw.githubusercontent.com/Ramin-Setoodehnia/v2ray/main/vmess",
    "https://raw.githubusercontent.com/Ramin-Setoodehnia/v2ray/main/vless",
    "https://raw.githubusercontent.com/mehdi-farsi/proxy/main/vmess",
    "https://raw.githubusercontent.com/mehdi-farsi/proxy/main/vless",
    "https://raw.githubusercontent.com/mehdi-farsi/proxy/main/clash",
    "https://raw.githubusercontent.com/amirali-dashti/v2ray-free/main/vmess.txt",
    "https://raw.githubusercontent.com/amirali-dashti/v2ray-free/main/vless.txt",
    "https://raw.githubusercontent.com/amirali-dashti/v2ray-free/main/clash.yaml",
    "https://raw.githubusercontent.com/moeinf/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/moeinf/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/moeinf/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/EminTorun007/free-vpn/main/vmess.txt",
    "https://raw.githubusercontent.com/EminTorun007/free-vpn/main/vless.txt",
    "https://raw.githubusercontent.com/EminTorun007/free-vpn/main/clash.yaml",
    "https://raw.githubusercontent.com/B85/v2rayProxy/main/vmess.txt",
    "https://raw.githubusercontent.com/B85/v2rayProxy/main/vless.txt",
    "https://raw.githubusercontent.com/B85/v2rayProxy/main/clash.yaml",
    "https://raw.githubusercontent.com/KingdomProxy/v2ray-config/main/vmess.txt",
    "https://raw.githubusercontent.com/KingdomProxy/v2ray-config/main/vless.txt",
    "https://raw.githubusercontent.com/KingdomProxy/v2ray-config/main/clash.yaml",
    "https://raw.githubusercontent.com/JohnHoos/JohnHoos/main/clash.yaml",
    "https://raw.githubusercontent.com/JohnHoos/JohnHoos/main/vmess.txt",
    "https://raw.githubusercontent.com/JohnHoos/JohnHoos/main/vless.txt",
    "https://raw.githubusercontent.com/mystica553/vless/main/clash.yaml",
    "https://raw.githubusercontent.com/mystica553/vless/main/vmess.txt",
    "https://raw.githubusercontent.com/zeroc0de2022/TG-Scrapper-V2/main/out/vmess.txt",
    "https://raw.githubusercontent.com/zeroc0de2022/TG-Scrapper-V2/main/out/vless.txt",
    "https://raw.githubusercontent.com/zeroc0de2022/TG-Scrapper-V2/main/out/clash.yaml",
    "https://raw.githubusercontent.com/Godisagirl/Proxy-Sub/main/Sub_base64/Vmess",
    "https://raw.githubusercontent.com/Godisagirl/Proxy-Sub/main/Sub_base64/Vless",
    "https://raw.githubusercontent.com/Godisagirl/Proxy-Sub/main/Sub_normal/Vmess",
    "https://raw.githubusercontent.com/Godisagirl/Proxy-Sub/main/Sub_normal/Vless",
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/vmess.txt",
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/vless.txt",
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/clash.yaml",
    "https://raw.githubusercontent.com/dimzon/scaling-robot/main/vmess",
    "https://raw.githubusercontent.com/dimzon/scaling-robot/main/vless",
    "https://raw.githubusercontent.com/dimzon/scaling-robot/main/clash",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/vmess_Sub.txt",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/vless_Sub.txt",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/mix_Sub.txt",
    "https://raw.githubusercontent.com/freefq/free/master/clash.yml",
    "https://raw.githubusercontent.com/freefq/free/master/README.md",
    "https://raw.githubusercontent.com/vveg26/chromego_merge/main/sub/base64.txt",
    "https://raw.githubusercontent.com/vveg26/chromego_merge/main/sub/clash.yaml",
    "https://raw.githubusercontent.com/Misaka-blog/chromego_merge/main/sub/base64.txt",
    "https://raw.githubusercontent.com/Misaka-blog/chromego_merge/main/sub/clash.yaml",
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list.yml",
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/README.md",
    "https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/clash.yaml",
    "https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/v2ray.txt",
    "https://raw.githubusercontent.com/vmessdr/vmess/master/clash",
    "https://raw.githubusercontent.com/vmessdr/vmess/master/v2ray",
    "https://raw.githubusercontent.com/Iam-HealthS/VMESS/main/clash",
    "https://raw.githubusercontent.com/Iam-HealthS/VMESS/main/vmess",
    "https://raw.githubusercontent.com/Iam-HealthS/VMESS/main/vless",
    "https://raw.githubusercontent.com/hermansh-id/belajar-script-proxy/main/sub/clash",
    "https://raw.githubusercontent.com/hermansh-id/belajar-script-proxy/main/sub/mixed",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/clash.yaml",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/vmess_configs.txt",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/vless_configs.txt",
    "https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/clash.yml",
    "https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/all.txt",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/clash.yaml",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/vmess",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/vless",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/clash_iran.yaml",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/clash_outside_iran.yaml",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vmess_iran.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vless_iran.txt",
    "https://raw.githubusercontent.com/mganotas/outbound/main/clash.yaml",
    "https://raw.githubusercontent.com/mganotas/outbound/main/vmess.txt",
    "https://raw.githubusercontent.com/mganotas/outbound/main/vless.txt",
    "https://raw.githubusercontent.com/Moli-X/Resources/main/Subscription/clash.yaml",
    "https://raw.githubusercontent.com/Moli-X/Resources/main/Subscription/vmess.txt",
    "https://raw.githubusercontent.com/Moli-X/Resources/main/Subscription/vless.txt",
    "https://raw.githubusercontent.com/4everfree/FreeNode/master/sub/clash.yaml",
    "https://raw.githubusercontent.com/4everfree/FreeNode/master/sub/v2ray.txt",
    "https://raw.githubusercontent.com/Airscker/V2Ray-Config-Pool/main/vmess.txt",
    "https://raw.githubusercontent.com/Airscker/V2Ray-Config-Pool/main/vless.txt",
    "https://raw.githubusercontent.com/Airscker/V2Ray-Config-Pool/main/clash.yaml",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/clash.yaml",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/vmess.txt",
    "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/vless.txt",
    "https://raw.githubusercontent.com/proxypool404/clash/main/vmess.yaml",
    "https://raw.githubusercontent.com/proxypool404/clash/main/vless.yaml",
    "https://raw.githubusercontent.com/proxypool404/clash/main/config.yaml",
    "https://raw.githubusercontent.com/MrHedgehogArmenian/proxy/main/clash.yaml",
    "https://raw.githubusercontent.com/MrHedgehogArmenian/proxy/main/vmess.txt",
    "https://raw.githubusercontent.com/MrHedgehogArmenian/proxy/main/vless.txt",
    "https://raw.githubusercontent.com/V2Hub/V2Hub.github.io/main/subs/clash.yaml",
    "https://raw.githubusercontent.com/V2Hub/V2Hub.github.io/main/subs/mix",
    "https://raw.githubusercontent.com/FreeVpnSubscriber/FreeVpn/main/clash.yaml",
    "https://raw.githubusercontent.com/FreeVpnSubscriber/FreeVpn/main/vmess.txt",
    "https://raw.githubusercontent.com/FreeVpnSubscriber/FreeVpn/main/vless.txt",
    "https://raw.githubusercontent.com/Airscker/V2Ray-Config-Pool/main/all.json",
    "https://raw.githubusercontent.com/ZywChannel/free/main/vmess",
    "https://raw.githubusercontent.com/ZywChannel/free/main/vless",
    "https://raw.githubusercontent.com/ZywChannel/free/main/clash.yaml",
    "https://raw.githubusercontent.com/adiwzx/freenode/main/adismartspeed.txt",
    "https://raw.githubusercontent.com/adiwzx/freenode/main/adivpn.txt",
    "https://raw.githubusercontent.com/liwei2633/v2rayse/main/vmess",
    "https://raw.githubusercontent.com/liwei2633/v2rayse/main/vless",
    "https://raw.githubusercontent.com/liwei2633/v2rayse/main/clash",
    "https://raw.githubusercontent.com/nikitattt/v2ray-subs/main/subs/clash.yaml",
    "https://raw.githubusercontent.com/nikitattt/v2ray-subs/main/subs/vmess.txt",
    "https://raw.githubusercontent.com/nikitattt/v2ray-subs/main/subs/vless.txt",
    "https://raw.githubusercontent.com/abshare/abshare.github.io/main/clash.yaml",
    "https://raw.githubusercontent.com/abshare/abshare.github.io/main/vmess.txt",
    "https://raw.githubusercontent.com/abshare/abshare.github.io/main/vless.txt",
    "https://raw.githubusercontent.com/xiyaowong/freeFQ/main/clash",
    "https://raw.githubusercontent.com/xiyaowong/freeFQ/main/vmess",
    "https://raw.githubusercontent.com/xiyaowong/freeFQ/main/vless",
    "https://raw.githubusercontent.com/alibasha/V2ray-Config/main/vmess",
    "https://raw.githubusercontent.com/alibasha/V2ray-Config/main/vless",
    "https://raw.githubusercontent.com/alibasha/V2ray-Config/main/clash.yaml",
    "https://raw.githubusercontent.com/ProxiesCollection/ProxiesCollection/main/clash.yaml",
    "https://raw.githubusercontent.com/ProxiesCollection/ProxiesCollection/main/vmess",
    "https://raw.githubusercontent.com/ProxiesCollection/ProxiesCollection/main/vless",
    "https://raw.githubusercontent.com/Dreamer-Paul/Sub/main/clash.yaml",
    "https://raw.githubusercontent.com/Dreamer-Paul/Sub/main/vmess",
    "https://raw.githubusercontent.com/Dreamer-Paul/Sub/main/vless",
    "https://raw.githubusercontent.com/free18/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/GalaxyCom2023/Xray-sub/main/clash.yaml",
    "https://raw.githubusercontent.com/GalaxyCom2023/Xray-sub/main/vmess",
    "https://raw.githubusercontent.com/GalaxyCom2023/Xray-sub/main/vless",
    "https://raw.githubusercontent.com/KingdomProxy/v2ray-config/main/all.txt",
    "https://raw.githubusercontent.com/vlessx/vlessx/main/clash.yaml",
    "https://raw.githubusercontent.com/vlessx/vlessx/main/vmess.txt",
    "https://raw.githubusercontent.com/xjp9153/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/xjp9153/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/xjp9153/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/freev2rayserver/freev2rayserver/main/clash.yaml",
    "https://raw.githubusercontent.com/freev2rayserver/freev2rayserver/main/vmess.txt",
    "https://raw.githubusercontent.com/freev2rayserver/freev2rayserver/main/vless.txt",
    "https://raw.githubusercontent.com/vpn0/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/vpn0/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/vpn0/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/ZxxSin/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/ZxxSin/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/ZxxSin/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/goog22/v2ray-configs/main/clash.yaml",
    "https://raw.githubusercontent.com/goog22/v2ray-configs/main/vmess.txt",
    "https://raw.githubusercontent.com/goog22/v2ray-configs/main/vless.txt",
    "https://raw.githubusercontent.com/Parsasafari/V2ray-Config/main/clash.yaml",
    "https://raw.githubusercontent.com/Parsasafari/V2ray-Config/main/vmess.txt",
    "https://raw.githubusercontent.com/Parsasafari/V2ray-Config/main/vless.txt",
    "https://raw.githubusercontent.com/AbolhasanKedkiGhadi/FreeV2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/AbolhasanKedkiGhadi/FreeV2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/AbolhasanKedkiGhadi/FreeV2ray/main/vless.txt",
    "https://raw.githubusercontent.com/EasternNetProxies/EasternNetProxies/main/clash.yaml",
    "https://raw.githubusercontent.com/EasternNetProxies/EasternNetProxies/main/vmess",
    "https://raw.githubusercontent.com/EasternNetProxies/EasternNetProxies/main/vless",
    "https://raw.githubusercontent.com/DamianHaynes/v2ray_clash/main/vmess.yaml",
    "https://raw.githubusercontent.com/DamianHaynes/v2ray_clash/main/vless.yaml",
    "https://raw.githubusercontent.com/LorenEteval/Furious/Origin/furious/Asset/subscription-clash",
    "https://raw.githubusercontent.com/IQ-deficient/shilling/main/clash",
    "https://raw.githubusercontent.com/IQ-deficient/shilling/main/vmess",
    "https://raw.githubusercontent.com/IQ-deficient/shilling/main/vless",
    "https://raw.githubusercontent.com/bevccy/v2ray_share/main/clash.yaml",
    "https://raw.githubusercontent.com/bevccy/v2ray_share/main/vmess",
    "https://raw.githubusercontent.com/bevccy/v2ray_share/main/vless",
    "https://raw.githubusercontent.com/alfredhuang426/free-v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/alfredhuang426/free-v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/alfredhuang426/free-v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/PerFectHasH/v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/PerFectHasH/v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/PerFectHasH/v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/Hediyeh-dark/Proxy/main/clash.yaml",
    "https://raw.githubusercontent.com/Hediyeh-dark/Proxy/main/all.txt",
    "https://raw.githubusercontent.com/HuTianQi030/-/main/clash",
    "https://raw.githubusercontent.com/HuTianQi030/-/main/vmess",
    "https://raw.githubusercontent.com/HuTianQi030/-/main/vless",
    "https://raw.githubusercontent.com/Flik6/getNode/main/clash.yaml",
    "https://raw.githubusercontent.com/Flik6/getNode/main/vmess.txt",
    "https://raw.githubusercontent.com/Flik6/getNode/main/vless.txt",
    "https://raw.githubusercontent.com/freebaipiao/freebaipiao/main/clash.yaml",
    "https://raw.githubusercontent.com/freebaipiao/freebaipiao/main/vmess.txt",
    "https://raw.githubusercontent.com/freebaipiao/freebaipiao/main/vless.txt",
    "https://raw.githubusercontent.com/huwo1/proxy_nodes/main/clash.yaml",
    "https://raw.githubusercontent.com/huwo1/proxy_nodes/main/vmess.md",
    "https://raw.githubusercontent.com/huwo1/proxy_nodes/main/vless.md",
    "https://raw.githubusercontent.com/wudongdefeng/free/main/freesub/clash.yaml",
    "https://raw.githubusercontent.com/wudongdefeng/free/main/freesub/v2ray.txt",
    "https://raw.githubusercontent.com/ProxyManaager/proxy/main/vmess.txt",
    "https://raw.githubusercontent.com/ProxyManaager/proxy/main/vless.txt",
    "https://raw.githubusercontent.com/ProxyManaager/proxy/main/clash.yaml",
    "https://raw.githubusercontent.com/jason5ng32/MyIP/main/public/clash.yaml",
    "https://raw.githubusercontent.com/jason5ng32/MyIP/main/public/vmess.txt",
    "https://raw.githubusercontent.com/jason5ng32/MyIP/main/public/vless.txt",
    "https://raw.githubusercontent.com/DaRealFreak/cloudflare-ip-tester/master/testing/clash",
    "https://raw.githubusercontent.com/mlabalabala/v2ray-node/main/nodefree4v2ray.yaml",
    "https://raw.githubusercontent.com/v2rayse/node-list/main/clash.yaml",
    "https://raw.githubusercontent.com/v2rayse/node-list/main/v2ray.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/merged_b64.txt",
    "https://raw.githubusercontent.com/shabane/kamaji/master/hub/clash.yaml",
    "https://raw.githubusercontent.com/shabane/kamaji/master/hub/vmess.txt",
    "https://raw.githubusercontent.com/shabane/kamaji/master/hub/vless.txt",
    "https://raw.githubusercontent.com/FreeNodes1/FreeNodes1/main/clash.yaml",
    "https://raw.githubusercontent.com/FreeNodes1/FreeNodes1/main/vmess",
    "https://raw.githubusercontent.com/FreeNodes1/FreeNodes1/main/vless",
    "https://raw.githubusercontent.com/B85/v2rayProxy/main/clash.yaml",
    "https://raw.githubusercontent.com/zargari956/zargari956/main/clash.yaml",
    "https://raw.githubusercontent.com/bitefu/bitefu/main/clash.yaml",
    "https://raw.githubusercontent.com/bitefu/bitefu/main/vmess.txt",
    "https://raw.githubusercontent.com/bitefu/bitefu/main/vless.txt",
    "https://raw.githubusercontent.com/themohammadsa/free-v2ray/main/clash.yaml",
    "https://raw.githubusercontent.com/themohammadsa/free-v2ray/main/vmess.txt",
    "https://raw.githubusercontent.com/themohammadsa/free-v2ray/main/vless.txt",
    "https://raw.githubusercontent.com/shahpasandfun/shahpasan/main/clash.yaml",
    "https://raw.githubusercontent.com/hossein-mohseni/v2ray/main/clash",
    "https://raw.githubusercontent.com/hossein-mohseni/v2ray/main/vmess",
    "https://raw.githubusercontent.com/hossein-mohseni/v2ray/main/vless",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/clash",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/vmess",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/vless",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/clash.yaml",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/vmess.txt",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/vless.txt",
    "https://t.me/s/v2_team",
    "https://t.me/s/V2ray_Alpha",
    "https://t.me/s/V2Ray_VLESS_VMess",
    "https://t.me/s/Cloudfront_VPN",
    "https://t.me/s/CDN_V2RAY",
    "https://t.me/s/v2rayng_org",
    "https://t.me/s/v2rayNG_Backup",
    "https://t.me/s/FreeV2rays",
    "https://t.me/s/free_v2rayyy",
    "https://t.me/s/IPV2RAY",
    "https://t.me/s/PrivateVPNs",
    "https://t.me/s/v2ray_outlinekey",
    "https://t.me/s/FreeVless",
    "https://t.me/s/freeNodes",
    "https://t.me/s/meli_proxi",
    "https://t.me/s/ShadowProxy66",
    "https://t.me/s/v2ray1_ng",
    "https://t.me/s/VmessProtocol",
    "https://t.me/s/DigiV2ray",
    "https://t.me/s/V2RayTz",
    "https://t.me/s/v2rayen",
    "https://t.me/s/v2ray_collector",
    "https://t.me/s/VlessConfig",
    "https://t.me/s/XrayFreeConfig",
    "https://t.me/s/XrayTunnel",
    "https://t.me/s/DirectVPN",
    "https://t.me/s/freevlesskey",
    "https://t.me/s/frev2rayng",
    "https://t.me/s/v2ray_free_conf",
    "https://t.me/s/vmessconfig",
    "https://t.me/s/freeconfigv2",
    "https://t.me/s/FreeV2ray4u",
    "https://t.me/s/V2ray4Iran",
    "https://t.me/s/iP_CF",
    "https://t.me/s/ConfigsHub",
    "https://t.me/s/v2rayNGn",
    "https://t.me/s/VPN_NAT",
    "https://t.me/s/vlessconfig",
    "https://t.me/s/v2ray_configs_pool",
    "https://t.me/s/VPN_Hell",
    "https://t.me/s/proxy_wars",
    "https://t.me/s/v2rayshop",
    "https://t.me/s/mahsaproxi",
    "https://t.me/s/v2rayngvpn",
    "https://t.me/s/VpnSkyy",
    "https://t.me/s/servervpniran",
    "https://t.me/s/V2RayOxygen",
    "https://t.me/s/v2rayprotocols",
    "https://t.me/s/GetConfig",
    "https://t.me/s/vpnfail_v2ray",
    "https://t.me/s/V2rayNG_Collector",
    "https://t.me/s/Freee_VPN",
    "https://t.me/s/prrooxy",
    "https://t.me/s/v2ray_vpn_ir",
    "https://t.me/s/VpnFail",
    "https://t.me/s/V2RayIranStable",
    "https://t.me/s/GozarVPN",
    "https://t.me/s/v2_configs",
    "https://t.me/s/YANEY_VPN",
    "https://t.me/s/fast_v2ray",
    "https://t.me/s/freenode_v2ray",
    "https://t.me/s/freeconfig4all",
    "https://t.me/s/Hiddify",
    "https://t.me/s/v2rayng_vpn",
    "https://t.me/s/AllProxies",
    "https://t.me/s/IranProxies",
    "https://t.me/s/VPN_Proxy_Free",
    "https://t.me/s/NetworkNinja",
    "https://t.me/s/vpnhat",
    "https://t.me/s/ProxyStore2023",
    "https://t.me/s/OutlineVpnOfficial",
    "https://t.me/s/ProxyMTProto",
    "https://t.me/s/v2iplocation",
    "https://t.me/s/mtproto_v2rayfree",
    "https://t.me/s/v2ray_rules",
    "https://t.me/s/proxy_mtproto2",
    "https://t.me/s/free_shadowsocks_v2ray",
    "https://t.me/s/freev2rayssr",
    "https://t.me/s/v2rayng_v",
    "https://t.me/s/v2rayng_config",
    "https://t.me/s/v2ray_configs_hub",
    "https://t.me/s/v2rayfreeconfig",
    "https://t.me/s/vmess_vless_free",
    "https://t.me/s/FreeVpnVless",
    "https://t.me/s/freevpnvmess",
    "https://t.me/s/free_v2ray_config",
    "https://t.me/s/v2ray_vmess_vless",
    "https://t.me/s/V2rayFreeProxy",
    "https://t.me/s/VlessVmess",
    "https://t.me/s/vless_vmess_config",
    "https://t.me/s/v2rayconfigs",
    "https://t.me/s/free_config_v2ray",
    "https://t.me/s/V2rayFree",
    "https://t.me/s/FreeConfigV2",
    "https://t.me/s/v2_free",
    "https://t.me/s/FreeV2rayServer",
    "https://t.me/s/v2ray_server_free",
    "https://t.me/s/ProxyV2ray",
    "https://t.me/s/VpnV2ray",
    "https://t.me/s/v2ray_proxy_free",
    "https://t.me/s/FreeVpnProxy",
    "https://t.me/s/VPN_Free_Configs",
    "https://t.me/s/free_vpn_v2ray",
    "https://t.me/s/FreeVpnConfig",
    "https://t.me/s/vpn_free_config",
    "https://t.me/s/free_configs_vpn",
    "https://t.me/s/FreeServerV2ray",
    "https://t.me/s/V2rayServer",
    "https://t.me/s/free_vmess",
    "https://t.me/s/FreeVmess",
    "https://t.me/s/vmess_free",
    "https://t.me/s/freevmessconfig",
    "https://t.me/s/vmessvpn",
    "https://t.me/s/VmessFree",
    "https://t.me/s/vmess_configs",
    "https://t.me/s/vmess_vless",
    "https://t.me/s/VmessVless",
    "https://t.me/s/FreeVlessConfig",
    "https://t.me/s/vless_free",
    "https://t.me/s/freevless",
    "https://t.me/s/vless_configs",
    "https://t.me/s/VlessFree",
    "https://t.me/s/vlessvpn",
    "https://t.me/s/vless_proxy",
    "https://t.me/s/FreeProxy443",
    "https://t.me/s/proxy443",
    "https://t.me/s/free_proxy_443",
    "https://t.me/s/ssl443",
    "https://t.me/s/FreeSSL443",
    "https://t.me/s/vpnssl",
    "https://t.me/s/sslvpn",
    "https://t.me/s/ssl_vpn_free",
    "https://t.me/s/FreeSSLVPN",
    "https://t.me/s/VPNConfig",
    "https://t.me/s/vpn_configs",
    "https://t.me/s/FreeVPNConfigs",
    "https://t.me/s/vpnconfig",
    "https://t.me/s/vpnconfigfree",
    "https://t.me/s/V2rayCDN",
    "https://t.me/s/cdn_proxy",
    "https://t.me/s/cloudflare_proxy",
    "https://t.me/s/CloudflareV2ray",
    "https://t.me/s/cfproxy",
    "https://t.me/s/CfV2ray",
    "https://t.me/s/cf_v2ray",
    "https://t.me/s/CFreedom",
    "https://t.me/s/free_cloudfront",
    "https://t.me/s/CloudFrontProxy",
    "https://t.me/s/cloudfrontvpn",
    "https://t.me/s/VpsProxy",
    "https://t.me/s/vps_free",
    "https://t.me/s/FreeVPS",
    "https://t.me/s/vps_v2ray",
    "https://t.me/s/VPSConfig",
    "https://t.me/s/vps_configs",
    "https://t.me/s/FreeVPSConfig",
    "https://t.me/s/vps_proxy",
    "https://t.me/s/ProxyFreeVPS",
    "https://t.me/s/AWSProxy",
    "https://t.me/s/aws_proxy",
    "https://t.me/s/FreeAWSProxy",
    "https://t.me/s/aws_v2ray",
    "https://t.me/s/OracleProxy",
    "https://t.me/s/oracle_proxy",
    "https://t.me/s/FreeOracleProxy",
    "https://t.me/s/oracle_v2ray",
    "https://t.me/s/OracleVPN",
    "https://t.me/s/DigitalOceanProxy",
    "https://t.me/s/do_proxy",
    "https://t.me/s/FreeDigitalOcean",
    "https://t.me/s/HetznerProxy",
    "https://t.me/s/hetzner_proxy",
    "https://t.me/s/FreeHetzner",
    "https://t.me/s/GCPProxy",
    "https://t.me/s/gcp_proxy",
    "https://t.me/s/FreeGCPProxy",
    "https://t.me/s/gcp_v2ray",
    "https://t.me/s/AzureProxy",
    "https://t.me/s/azure_proxy",
    "https://t.me/s/FreeAzureProxy",
    "https://t.me/s/azure_v2ray",
    "https://t.me/s/IranianProxy",
    "https://t.me/s/iran_proxy",
    "https://t.me/s/IranianVPN",
    "https://t.me/s/iran_v2ray",
    "https://t.me/s/IranVPN",
    "https://t.me/s/FreeIranProxy",
    "https://t.me/s/iran_vpn",
    "https://t.me/s/proxyiran",
    "https://t.me/s/GlobalProxy",
    "https://t.me/s/global_proxy",
    "https://t.me/s/FreeGlobalProxy",
    "https://t.me/s/WorldProxy",
    "https://t.me/s/world_proxy",
    "https://t.me/s/FreeWorldProxy",
    "https://t.me/s/MultiProxy",
    "https://t.me/s/multi_proxy",
    "https://t.me/s/MixProxy",
    "https://t.me/s/mix_proxy",
    "https://t.me/s/AllProxy",
    "https://t.me/s/all_proxy",
    "https://t.me/s/ProxyHub",
    "https://t.me/s/proxy_hub",
    "https://t.me/s/FreeProxyHub",
    "https://t.me/s/ProxyPool",
    "https://t.me/s/proxy_pool",
    "https://t.me/s/FreeProxyPool",
    "https://t.me/s/ConfigHub",
    "https://t.me/s/config_hub",
    "https://t.me/s/FreeConfigHub",
    "https://t.me/s/ConfigPool",
    "https://t.me/s/config_pool",
    "https://t.me/s/FreeConfigPool",
    "https://t.me/s/v2rayhub",
    "https://t.me/s/V2rayHub",
    "https://t.me/s/v2raypool",
    "https://t.me/s/V2rayPool",
    "https://t.me/s/V2rayConfig",
    "https://t.me/s/v2rayconfig",
    "https://t.me/s/FreeV2rayConfig",
    "https://t.me/s/V2rayConfigFree",
    "https://t.me/s/v2rayfreee",
    "https://t.me/s/V2rayFreeee",
    "https://t.me/s/ProxyFreeConfig",
    "https://t.me/s/FreeProxyConfig",
    "https://t.me/s/proxy_free_config",
    "https://t.me/s/free_proxy_config",
    "https://t.me/s/NightFox_VPN",
    "https://t.me/s/F_Proxy",
    "https://t.me/s/HiddifyNG",
    "https://t.me/s/Hiddify_Configs",
    "https://t.me/s/Sing_Box_Config",
    "https://t.me/s/XrayConfig",
    "https://t.me/s/xray_config",
    "https://t.me/s/FreeXrayConfig",
    "https://t.me/s/xray_configs",
    "https://t.me/s/XrayFree",
    "https://t.me/s/xrayfree",
    "https://t.me/s/XrayProxy",
    "https://t.me/s/xray_proxy",
    "https://t.me/s/FreeXrayProxy",
    "https://t.me/s/xray_free_config",
    "https://t.me/s/XrayFreeConfig2",
    "https://t.me/s/ClashConfig",
    "https://t.me/s/clash_config",
    "https://t.me/s/FreeClashConfig",
    "https://t.me/s/clash_free",
    "https://t.me/s/ClashFree",
    "https://t.me/s/ClashProxy",
    "https://t.me/s/clash_proxy",
    "https://t.me/s/FreeClashProxy",
    "https://t.me/s/HiddifyConfig",
    "https://t.me/s/hiddify_config",
    "https://t.me/s/FreeHiddifyConfig",
    "https://t.me/s/HiddifyFree",
    "https://t.me/s/hiddify_free",
]

def collect_configs() -> list[str]:
    """يجمع من المصادر مع AI ranking وتخطي الميتة."""
    dead   = ai_dead()
    active = [u for u in SOURCES if u not in dead]
    ranked = ai_rank_sources(active)
    # 80% ranked + 20% random للتنويع
    split  = int(len(ranked) * 0.80)
    rest   = ranked[split:]; random.shuffle(rest)
    ordered = (ranked[:split] + rest)[:600]  # أقصى 600 مصدر

    log.info(f"🌐 Fetching {len(ordered)}/{len(SOURCES)} sources "
             f"[{FETCH_WORKERS}w | {len(dead)} dead skipped]")

    all_raw: list[str] = []
    src_counts: dict   = {}

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        fmap = {ex.submit(_fetch, u): u for u in ordered}
        for fut in as_completed(fmap):
            if not deadline_ok(): break
            url = fmap[fut]
            try:
                results = fut.result()
                src_counts[url] = len(results)
                all_raw.extend(results)
            except Exception:
                src_counts[url] = 0

    # تحديث AI memory
    for url, cnt in src_counts.items():
        ai_src_update(url, cnt)

    unique = list(dict.fromkeys(all_raw))
    good   = sum(1 for c in src_counts.values() if c > 0)
    log.info(f"📦 {len(unique)} unique | {good}/{len(ordered)} active sources")
    return unique


def run_checks(raws: list[str]) -> list[V2Config]:
    """
    فحص الكونفيجات مع:
    ✅ Hard Deadline — يوقف نفسه في الوقت المحدد
    ✅ MAX_CHECK_RAWS — لا يفحص أكثر من اللازم
    ✅ Self-healing — يلتقط الأخطاء ويكمل
    ✅ Smart sort — الـ IPs المعروفة أولاً
    """
    # ترتيب ذكي: IPs معروفة → CF → VPS
    with _ai_lock:
        good = set(_AI.get("good_ips", []))
    def _sk(x):
        mm = re.search(r"@([^:/]+):", x)
        ip = mm.group(1) if mm else ""
        return (
            ip not in good,
            not any(k in x.lower() for k in CF_KEYWORDS),
            not any(k in x.lower() for k in VPS_KEYWORDS),
        )
    raws = sorted(raws, key=_sk)[:MAX_CHECK_RAWS]

    remain = deadline_left()
    log.info(f"⚡ Checking {len(raws)} configs "
             f"[{CHECK_WORKERS}w | stop@{STOP_AFTER_FOUND} | ⏳{remain}s left]")

    live: list[V2Config] = []
    stop = threading.Event()
    lock = threading.Lock()
    errs = [0]

    def _w(raw: str) -> Optional[V2Config]:
        if stop.is_set() or not deadline_ok(): return None
        try:
            return check_raw(raw)
        except Exception:
            with lock: errs[0] += 1
            return None

    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as ex:
        futs = {ex.submit(_w, r): r for r in raws}
        for fut in as_completed(futs):
            # ── Hard Deadline Guard ──────────────────────────────────
            if not deadline_ok():
                stop.set()
                log.warning(f"⏰ Hard deadline — {len(live)} found, stopping")
                try: ex.shutdown(wait=False, cancel_futures=True)
                except Exception: pass
                break

            if stop.is_set():
                try: fut.cancel()
                except Exception: pass
                continue

            try:
                res = fut.result(timeout=25)
            except Exception:
                res = None

            if res:
                with lock:
                    live.append(res)
                    n = len(live)
                    if n % 10 == 0:
                        log.info(f"  📊 {n} live | ⏳{deadline_left()}s | {ai_report()}")
                    if n >= STOP_AFTER_FOUND:
                        stop.set()
                        log.info(f"🛑 Stop@{STOP_AFTER_FOUND} reached")

    log.info(f"✅ {len(live)} live | {errs[0]} errors healed")
    return live


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GEO ENRICHMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_geo: dict = {}; _gl = threading.Lock()

def get_geo(ip: str) -> tuple[str, str, str]:
    with _gl:
        if ip in _geo: return _geo[ip]
    for url in [
        f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp",
        f"https://ipapi.co/{ip}/json/",
    ]:
        try:
            rj = _sess().get(url, timeout=3, headers=_headers()).json()
            if rj.get("status") == "success" or rj.get("country_code"):
                cc  = rj.get("countryCode") or rj.get("country_code","??")
                co  = rj.get("country","Unknown")
                isp = rj.get("isp","")
                with _gl: _geo[ip] = (cc, co, isp)
                return cc, co, isp
        except Exception: pass
    return "??", "Unknown", ""

def enrich(cfg: V2Config) -> V2Config:
    try:
        ip = socket.gethostbyname(cfg.host)
        cc, co, isp = get_geo(ip)
        cfg.country_code = cc; cfg.country = co; cfg.isp = isp
        cfg.is_cf  = cfg.is_cf  or is_cf_ip(ip)
        cfg.is_vps = cfg.is_vps or any(k in isp.lower() for k in ("vps","cloud","server","data"))
    except Exception: pass
    return cfg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CACHE → V2Config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def cache_to_configs(data: list[dict]) -> list[V2Config]:
    result = []
    for c in data:
        try:
            result.append(V2Config(
                raw=c["raw"], raw_patched=c["raw_p"],
                host=c["host"], port=c["port"],
                proto=c["proto"], ping_ms=c["ping"], probe_ms=c.get("probe",0),
                original_sni="", injected_sni="",
                ssl_ok=c.get("ssl",False), ssl_cert_cn="",
                is_cf=c.get("is_cf",False), is_vps=c.get("is_vps",False),
                compatible_hosts=c.get("compat",[]),
                best_bug_host=c.get("best",""),
                country_code=c.get("cc","??"), country=c.get("country","Unknown"),
                isp=c.get("isp",""),
                ai_diagnosis=c.get("diag","♻️ from cache"),
                server_type="CF" if c.get("is_cf") else "VPS",
            ))
        except Exception: pass
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MESSAGE BUILDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _ping_lbl(ms: int) -> str:
    if ms < 100: return "⚡ Excellent"
    if ms < 200: return "✅ Good"
    if ms < 400: return "🟡 OK"
    return "🔴 Slow"

def _rating(cfg: V2Config) -> str:
    s = cfg.score()
    if s > 8000: return "🏆 Elite"
    if s > 5000: return "⭐⭐⭐ Premium"
    if s > 2000: return "⭐⭐ Good"
    return "⭐ Basic"

def _operators(cfg: V2Config) -> str:
    ops = []
    compat = set(cfg.compatible_hosts)
    if compat & set(TARGET_HOSTS["oodi"]): ops.append("📶 Oodi")
    if compat & set(TARGET_HOSTS["zain"]): ops.append("📶 Zain")
    return " | ".join(ops) if ops else "❓ Unknown"

def build_message(cfg: V2Config) -> str:
    """رسالة أنيقة ومختصرة — كل المعلومات المهمة بدون تكرار."""
    nc   = len(cfg.compatible_hosts)
    nt   = len(ALL_BUG_HOSTS)
    flag = {"US":"🇺🇸","DE":"🇩🇪","NL":"🇳🇱","FR":"🇫🇷","GB":"🇬🇧",
            "SG":"🇸🇬","JP":"🇯🇵","HK":"🇭🇰","KR":"🇰🇷","CA":"🇨🇦",
            "AU":"🇦🇺","IN":"🇮🇳","BR":"🇧🇷","RU":"🇷🇺","TR":"🇹🇷"}.get(cfg.country_code, "🌍")
    ops  = _operators(cfg)
    tier = _rating(cfg)
    type_icon = ("⚡" if cfg.is_cf else "") + ("🚀" if cfg.is_vps else "")
    ping_icon = "🟢" if cfg.ping_ms < 150 else "🟡" if cfg.ping_ms < 350 else "🔴"
    # قائمة هوستات مختصرة في سطر واحد
    hosts_line = " | ".join(f"<code>{h}</code>" for h in cfg.compatible_hosts[:4])
    if nc > 4: hosts_line += f" +{nc-4}"

    return (
        f"🤖 <b>Ashaq AI Hunter v8</b> — {tier}\n"
        f"─────────────────────────\n"
        f"{flag} <b>{cfg.country}</b>  {type_icon}  {cfg.isp or ''}\n"
        f"{ping_icon} <b>{cfg.ping_ms}ms</b>  •  🔌 {cfg.proto}  •  🔒 {'✅' if cfg.ssl_ok else '⚠️'}\n"
        f"📡 <b>{ops}</b>\n"
        f"─────────────────────────\n"
        f"🎯 <b>Bug Hosts ({nc}/{nt}):</b>\n"
        f"{hosts_line}\n"
        f"─────────────────────────\n"
        f"📝 أضف Bug Host الذي يناسب شبكتك في التطبيق\n"
        f"─────────────────────────\n"
        f"<code>{cfg.raw_patched}</code>\n"
        f"─────────────────────────\n"
        f"🕒 {datetime.now(timezone.utc).strftime('%H:%M UTC • %d/%m/%Y')}  |  @V2rayashaq"
    )


def send_tg(cfg: V2Config) -> bool:
    if not BOT_TOKEN: return False
    payload = {
        "chat_id": CHAT_ID, "text": build_message(cfg),
        "parse_mode": "HTML", "disable_web_page_preview": True,
        "reply_markup": {"inline_keyboard": [[
            {"text": "📢 Channel", "url": "https://t.me/V2rayashaq"},
            {"text": "👤 Admin",   "url": f"https://t.me/{ADMIN_USER.lstrip('@')}"},
        ]]}
    }
    for attempt in range(3):
        try:
            res = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json=payload, timeout=15)
            if res.status_code == 429:
                w = res.json().get("parameters",{}).get("retry_after",20)
                time.sleep(w); continue
            if res.ok: return True
            log.warning(f"TG {res.status_code}: {res.text[:80]}")
            return False
        except Exception as e:
            log.warning(f"TG attempt {attempt+1}: {e}")
            time.sleep(3)
    return False


def save_sub(cfgs: list[V2Config]) -> None:
    top  = cfgs[:MAX_SUB_CONFIGS]
    blob = "\n".join(c.raw_patched for c in top)
    try:
        open(SUB_FILE, "w", encoding="utf-8").write(
            base64.b64encode(blob.encode()).decode())
        log.info(f"💾 Sub saved: {len(top)} configs → {SUB_FILE}")
    except Exception as e:
        log.error(f"Sub save failed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main() -> None:
    global _deadline, CUSTOM_SNI

    # ── Hard Deadline ──────────────────────────────────────────────────────
    _deadline = time.time() + HARD_DEADLINE_MINS * 60
    log.info(f"⏰ Hard deadline set: {HARD_DEADLINE_MINS}m from now")

    ap = argparse.ArgumentParser(description="V2Ray AI Hunter v8")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sni", default="")
    args = ap.parse_args()
    if args.sni: CUSTOM_SNI = args.sni.strip()

    t0 = time.time()
    log.info("╔══════════════════════════════════════════════════════╗")
    log.info("║  🤖 V2RAY ULTIMATE HUNTER v8 — AI EDITION           ║")
    log.info(f"║  {len(SOURCES):<4} sources | {HARD_DEADLINE_MINS}m deadline | WS+TLS+443        ║")
    log.info("╚══════════════════════════════════════════════════════╝")
    log.info(
        f"🧠 AI: run#{_AI['runs']} | {len(_AI['good_ips'])} good IPs | "
        f"{len(ai_dead())} dead src | sni={'auto' if not CUSTOM_SNI else CUSTOM_SNI}"
    )
    if args.dry_run: log.info("🔇 Dry-run mode — no Telegram posting")

    # ── 1. Load cache (فقط الأحدث من ساعتين لضمان الجودة) ──────────────────
    cached_raw = cache_load()
    # فلتر إضافي: تجاهل الكونفيجات المحفوظة قبل آخر fix
    cached = cache_to_configs(cached_raw)
    if cached: log.info(f"♻️  {len(cached)} cached configs loaded (< {_CACHE_TTL//3600}h)")

    # ── 2. Collect ────────────────────────────────────────────────────────
    raws: list[str] = []
    if deadline_ok():
        raws = collect_configs()
    if not raws and not cached:
        log.error("Nothing collected + no cache — exit"); return

    # ── 3. Check fresh ────────────────────────────────────────────────────
    fresh: list[V2Config] = []
    if raws and deadline_ok():
        fresh = run_checks(raws)

    # ── 4. Merge (fresh + cache, no duplicates) ───────────────────────────
    fresh_hosts = {c.host for c in fresh}
    live = fresh + [c for c in cached if c.host not in fresh_hosts]
    if not live:
        log.error("No live configs (fresh + cache) — exit"); return

    # ── 5. Geo enrich ─────────────────────────────────────────────────────
    if fresh and deadline_ok():
        log.info(f"🔍 Geo enrichment ({len(fresh)} configs) ...")
        with ThreadPoolExecutor(max_workers=GEO_WORKERS) as ex:
            enriched = list(ex.map(enrich, fresh))
        enriched_hosts = {c.host for c in enriched}
        live = enriched + [c for c in cached if c.host not in enriched_hosts]

    # ── 6. Sort by score ──────────────────────────────────────────────────
    # ترتيب بـ AI score الحقيقي: ping + probe + compat_count
    live.sort(key=lambda c: ai_score_config(c.ping_ms, c.probe_ms, len(c.compatible_hosts)), reverse=True)

    # ── 7. Top report ─────────────────────────────────────────────────────
    log.info(f"\n📊 Top {min(10,len(live))} configs:")
    log.info("  #  Type     Ping  Probe  Compat  CC   Host")
    log.info("  " + "─" * 58)
    for i, c in enumerate(live[:10], 1):
        t  = ("🚀" if c.is_vps else "  ") + ("⚡" if c.is_cf else "  ") + \
             ("🔒" if c.ssl_ok else "  ")
        p  = f"{c.probe_ms}ms" if c.probe_ms else "  —"
        src= "♻" if "cache" in c.ai_diagnosis.lower() else " "
        log.info(f"  {i:>2}{src} {t} {c.ping_ms:>4}ms {p:>5}  "
                 f"{len(c.compatible_hosts):>2}/{len(ALL_BUG_HOSTS)}  "
                 f"{c.country_code:<3}  {c.host[:30]}")

    # ── 8. Post to Telegram ───────────────────────────────────────────────
    posted = 0
    for cfg in live:
        if posted >= MAX_POSTS: break
        if not deadline_ok(): break
        if args.dry_run:
            log.info(f"[DRY] {cfg.host} | {cfg.ai_diagnosis[:55]}")
            posted += 1
        else:
            if send_tg(cfg):
                posted += 1
                log.info(f"📨 {posted}/{MAX_POSTS}: {cfg.host} → {cfg.best_bug_host}")
                time.sleep(2)

    # ── 9. Save ───────────────────────────────────────────────────────────
    save_sub(live)
    cache_save(live)

    # ── 10. Update AI memory ──────────────────────────────────────────────
    with _ai_lock:
        _AI["runs"]   += 1
        _AI["posted"] += posted
        _AI["last"]    = datetime.now(timezone.utc).isoformat()[:16]
    _ai_save(_AI)

    elapsed = int(time.time() - t0)
    log.info(
        f"\n🏁 Done in {elapsed}s | {len(fresh)} fresh | "
        f"{len(cached)} cached | {posted} posted | {ai_report()}"
    )


if __name__ == "__main__":
    main()
