# v2ray_hunter.py (بعد التعديل مع إضافة تحسينات التشخيص)
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🤖 V2RAY ULTIMATE HUNTER v7 — AI EDITION — ASHAQ TEAM                     ║
║  ذكاء اصطناعي حقيقي يحاكي Claude/GPT — يصطاد السيرفرات الشغالة فقط       ║
║  857 Sources | AI Bug-Host Engine | CF Smart SNI | Zero-Data Filter        ║
║  Self-Healing | Auto-Diagnosis | Multi-Path Probe | Operator Intelligence  ║
╚══════════════════════════════════════════════════════════════════════════════╝

AI BRAIN — كيف يفكر الذكاء الاصطناعي في v7:
  1. يجمع الكونفيجات من 857 مصدر بشكل متوازٍ
  2. لكل سيرفر: يشغّل 5 اختبارات متتالية كطبيب يفحص مريض
  3. يكتشف نوع السيرفر (CF/VPS/CDN) ويختار استراتيجية مختلفة لكل نوع
  4. يجرّب كل Bug Host من 14 هوست بالتوازي ويختار الأسرع
  5. يحقن Bug Host مباشرةً في الكونفيج — يعمل بضغطة زر واحدة
  6. يشخّص المشاكل تلقائياً ويكتب تقرير ذكي عن كل سيرفر
  7. يتعلم من كل جولة: يعطي أولوية للهوستات الناجحة في الجولة القادمة

HOW TO USE:
  python v2ray_hunter.py              ← تشغيل عادي بذكاء كامل
  python v2ray_hunter.py --dry-run   ← بدون نشر تيليغرام
  python v2ray_hunter.py --sni X    ← تثبيت SNI محدد

ENV VARS:
  BOT_TOKEN  — توكن بوت تيليغرام
  CUSTOM_SNI — SNI ثابت (اختياري)
  ADMIN_TG   — يوزر الأدمن
"""

import os, re, ssl, sys, json, time, socket, base64, hashlib, ipaddress
import logging, threading, argparse, requests, random
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
log = logging.getLogger("V7-AI")
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s │ %(levelname)-7s │ %(message)s", "%H:%M:%S")
_ch  = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt); _ch.setLevel(logging.INFO)
log.addHandler(_ch)
try:
    _fh = logging.FileHandler("v2ray_hunt.log", encoding="utf-8")
    _fh.setFormatter(_fmt); _fh.setLevel(logging.DEBUG)
    log.addHandler(_fh)
except Exception: pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANTI-BOT v4 — الجيل الرابع من التخفي
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
]

def _headers() -> dict:
    ua = random.choice(_UAS)
    h = {
        "User-Agent": ua, "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate, br", "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none",
        "Cache-Control": random.choice(["max-age=0", "no-cache"]),
    }
    if "Chrome" in ua and "Edg" not in ua:
        h["Sec-CH-UA"] = '"Chromium";v="124","Google Chrome";v="124","Not-A.Brand";v="99"'
        h["Sec-CH-UA-Mobile"] = "?0"; h["Sec-CH-UA-Platform"] = '"Windows"'
    return h

def _mk_session() -> requests.Session:
    s = requests.Session()
    r = Retry(total=3, backoff_factor=0.5, status_forcelist=[429,500,502,503,504],
              allowed_methods=["GET"], raise_on_status=False)
    a = HTTPAdapter(max_retries=r, pool_connections=50, pool_maxsize=200)
    s.mount("https://", a); s.mount("http://", a)
    return s

_tl = threading.local()
def _sess() -> requests.Session:
    if not hasattr(_tl, "s"): _tl.s = _mk_session()
    return _tl.s

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
CHAT_ID    = "@V2rayashaq"
ADMIN_USER = os.environ.get("ADMIN_TG", "@genie_2000")
SUB_FILE   = "sub_link.txt"
CUSTOM_SNI = os.environ.get("CUSTOM_SNI", "")

MAX_POSTS        = 5
MAX_SUB_CONFIGS  = 200
FETCH_WORKERS    = 30                # تم التخفيض من 60
CHECK_WORKERS    = 40                # تم التخفيض من 80
FETCH_TIMEOUT    = 12
TCP_TIMEOUT      = 2.0
SSL_TIMEOUT      = 3.5
PROBE_TIMEOUT    = 4.0
MAX_PING_MS      = 700
STOP_AFTER_FOUND = 900
TARGET_PORT      = 443
MIN_COMPAT_HOSTS = 1

# ── ثوابت جديدة للتحكم بالوقت والحجم ───────────────────────────────
MAX_CONFIGS_TO_CHECK = 2000        # أقصى عدد كونفيج يتم فحصهم (يسرع كثيراً)
PROBE_BATCH_SIZE = 4                # عدد Bug Hosts في كل دفعة فحص
MAX_RUNTIME_SECONDS = 1200          # 20 دقيقة – حد آمن لـ GitHub Actions

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TARGET BUG HOSTS — القائمة الكاملة المحدَّثة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ── Bug Hosts المعتمدة للفحص — المستخدم يحط الهوست بنفسه في التطبيق ──
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
TARGET_HOSTS: dict[str, list[str]] = {
    "oodi": ALL_BUG_HOSTS[:],   # كل الهوستات = Oodi
    "zain": ["m.tiktok.com"],
    "voxi": [],                  # لا يوجد voxi في هذه القائمة
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI MEMORY — يتذكر ما نجح في الجولات السابقة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI PERSISTENT MEMORY x10 — يتعلم ويتحسن مع كل جولة تلقائياً
#  يحفظ على ملف JSON: مصادر جيدة/ضعيفة، Bug Hosts، MD5 cache
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import hashlib as _hashlib

_AI_CACHE_FILE = "ai_memory.json"
_ai_lock = threading.Lock()

def _load_ai_memory() -> dict:
    default = {
        "version": 7,
        "winning_hosts":  {},  "failing_hosts":  {},
        "source_scores":  {},  "seen_md5":       [],
        "known_good_ips": [],  "total_runs":     0,
        "total_tested":   0,   "total_passed":   0,
        "total_posted":   0,   "last_run":       "",
    }
    try:
        with open(_AI_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in default.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return default

def _save_ai_memory(m: dict) -> None:
    try:
        m["seen_md5"]       = m.get("seen_md5", [])[-5000:]
        m["known_good_ips"] = list(set(m.get("known_good_ips", [])))[-500:]
        with open(_AI_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, separators=(",",":"))
    except Exception as e:
        log.warning(f"AI save failed: {e}")

_ai_memory: dict = _load_ai_memory()

def ai_mark_good_ip(ip: str) -> None:
    with _ai_lock:
        good = _ai_memory.setdefault("known_good_ips", [])
        if ip not in good: good.append(ip)

def ai_is_good_ip(ip: str) -> bool:
    with _ai_lock:
        return ip in _ai_memory.get("known_good_ips", [])

def ai_is_seen(raw: str) -> bool:
    """MD5 cache — لا يعيد فحص ما فُحص من قبل."""
    h = _hashlib.md5(raw.encode()).hexdigest()
    with _ai_lock:
        seen = _ai_memory.setdefault("seen_md5", [])
        if h in seen: return True
        seen.append(h); return False

def ai_update(bug_host: str, success: bool) -> None:
    with _ai_lock:
        key = "winning_hosts" if success else "failing_hosts"
        _ai_memory[key][bug_host] = _ai_memory[key].get(bug_host, 0) + 1
        _ai_memory["total_tested"] += 1
        if success: _ai_memory["total_passed"] += 1

def ai_update_source(url: str, hits: int, fails: int) -> None:
    """يُحدّث تقييم مصدر بعد الجلب."""
    with _ai_lock:
        sc = _ai_memory.setdefault("source_scores", {})
        if url not in sc:
            sc[url] = {"hits": 0, "fails": 0, "yield": 0.0, "runs": 0}
        sc[url]["hits"]  += hits
        sc[url]["fails"] += fails
        sc[url]["runs"]  += 1
        total = sc[url]["hits"] + sc[url]["fails"]
        sc[url]["yield"] = sc[url]["hits"] / total if total else 0.0

def ai_dead_sources() -> set:
    """مصادر ميتة: 0 hits من 10+ محاولات — تُحذف من الجولة."""
    with _ai_lock:
        sc = _ai_memory.get("source_scores", {})
    dead = set()
    for url, s in sc.items():
        total = s.get("hits",0) + s.get("fails",0)
        if total >= 10 and s.get("yield",1.0) < 0.01:
            dead.add(url)
    return dead

def ai_best_order() -> list[str]:
    """يرتب Bug Hosts بناءً على معدل النجاح الكلي (جميع الجولات)."""
    with _ai_lock:
        wins  = _ai_memory["winning_hosts"]
        fails = _ai_memory["failing_hosts"]
    def score(h):
        w = wins.get(h,0); f = fails.get(h,0); t = w+f
        return (w/t) if t else 0.5
    return sorted(ALL_BUG_HOSTS, key=score, reverse=True)

def ai_rank_sources(sources: list) -> list:
    """يرتب المصادر: الأعلى yield أولاً، الجديدة في المنتصف، الميتة في الآخر."""
    with _ai_lock:
        sc = _ai_memory.get("source_scores", {})
    def rank(u):
        s = sc.get(u, {}); t = s.get("hits",0) + s.get("fails",0)
        if t == 0:    return 0.45   # جديد → فرصة
        if t < 5:     return 0.40   # بيانات قليلة
        y = s.get("yield",0.0)
        if y < 0.01:  return 0.0    # ميت
        return y
    return sorted(sources, key=rank, reverse=True)

def ai_report() -> str:
    m = _ai_memory
    rate  = (m["total_passed"] / m["total_tested"] * 100) if m["total_tested"] else 0
    top   = sorted(m["winning_hosts"].items(), key=lambda x: -x[1])[:3]
    tops  = ", ".join(f"{h.split('.')[1]}({n})" for h,n in top) or "—"
    dead  = len(ai_dead_sources())
    return (
        f"🤖 AI x10 | Run #{m['total_runs']} | "
        f"{m['total_passed']}/{m['total_tested']} ({rate:.1f}%) | "
        f"Top: {tops} | 💀Dead: {dead}"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CF IP DETECTION — كشف Cloudflare بالـ CIDR الدقيق
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

VPS_KEYWORDS = [
    "oracle","google","amazon","aws","digitalocean","hetzner","ovh","linode",
    "vultr","azure","contabo","alibaba","tencent","rackspace","leaseweb",
    "choopa","quadranet","frantech","datacamp","cloudflare","fastly","akamai",
    "cdn77","stackpath","clouvider","hostwinds","liquidweb","vps","datacenter","hosting",
]
CF_KEYWORDS = [
    "cloudfront","cdn","worker","pages.dev","nodes.com","cloudflare","cfcdn","cfip",
    "104.","172.64.","172.65.","172.66.","172.67.","162.158.","198.41.",
]

CONFIG_RE = re.compile(r"(?:vless|vmess)://[^\s#\"\'<>\]\[]+")

SOURCES: list[str] = [

    # ═══════════════════════════════════════════════════════════════
    #  BLOCK A — GitHub collectors (original ~130 sources)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    #  BLOCK B — GitHub NEW 1000+ sources (added in v4)
    # ═══════════════════════════════════════════════════════════════

    # ── soroushmirzaei full collection ────────────────────────────
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/proxies/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/proxies/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/proxies/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/proxies/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/proxies/mix",

    # ── yebekhe extended ──────────────────────────────────────────
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/normal/mix",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/normal/vmess",
    "https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/normal/vless",

    # ── barry-far extended ────────────────────────────────────────
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/sub.txt",

    # ── NiREvil full repo ─────────────────────────────────────────
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

    # ── LalatinaHub extended ──────────────────────────────────────
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

    # ── Surfboardv2ray extended ───────────────────────────────────
    "https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Raw",
    "https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Vless",
    "https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Vmess",

    # ── Auto-merge & aggregator repos ────────────────────────────
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

    # ── New unique repos not in original list ─────────────────────
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

    # ── Independent unique repos (all new) ────────────────────────
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

    # ── Rarely scraped unique sources (all new) ───────────────────
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

    # ═══════════════════════════════════════════════════════════════
    #  BLOCK C — Telegram channels (original ~80 + new ~150)
    # ═══════════════════════════════════════════════════════════════

    # Original channels
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

    # New Telegram channels (150+)
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

CONFIG_RE = re.compile(r'(?:vless|vmess)://[^\s#"\'<>\]\[]+')



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODEL v7
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
    ai_diagnosis:     str   = ""   # تقرير AI عن هذا السيرفر
    server_type:      str   = ""   # "CF" / "VPS" / "CDN" / "Unknown"

    def score(self) -> int:
        s = 800 if self.is_vps else 0
        s += 600 if self.is_cf  else 0
        s += 400 if self.ssl_ok else 0
        # Bug Host compatibility — القلب الحقيقي للتقييم
        oodi = set(TARGET_HOSTS["oodi"]); zain = set(TARGET_HOSTS["zain"])
        voxi = set(TARGET_HOSTS["voxi"]); compat = set(self.compatible_hosts)
        s += len(compat & oodi) * 1000
        s += len(compat & zain) * 900
        s += len(compat & voxi) * 800
        if len(compat) >= len(ALL_BUG_HOSTS): s += 3000  # Elite: كل الهوستات
        # HTTP probe speed
        if self.probe_ms > 0:
            if   self.probe_ms < 100: s += 1200
            elif self.probe_ms < 200: s += 900
            elif self.probe_ms < 400: s += 600
            elif self.probe_ms < 700: s += 300
        # TCP ping
        if   self.ping_ms < 80:  s += 1000
        elif self.ping_ms < 150: s += 700
        elif self.ping_ms < 300: s += 400
        elif self.ping_ms < 500: s += 200
        return s


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SNI ENGINE v7 — حقن Bug Host بدلاً من التفريغ الأعمى
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_SNI_KEYS = ("sni", "host", "peer", "servername", "server-name")

def _extract_vless_sni(raw: str) -> str:
    for k in _SNI_KEYS:
        m = re.search(rf"[?&]{k}=([^&\s#]+)", raw, re.IGNORECASE)
        if m and m.group(1): return m.group(1)
    return ""

def _extract_vmess_sni(raw: str) -> str:
    try:
        b64 = raw[len("vmess://"):]
        for pad in ("","=","==","==="):
            try:
                obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                for k in _SNI_KEYS:
                    if obj.get(k): return str(obj[k])
                break
            except Exception: continue
    except Exception: pass
    return ""

def extract_sni(raw: str) -> str:
    return _extract_vmess_sni(raw) if raw.startswith("vmess://") else _extract_vless_sni(raw)

def _set_param(url: str, key: str, value: str) -> str:
    """يضبط قيمة param موجود أو يضيفه — يستخدم lambda لأمان الأحرف الخاصة."""
    pat = re.compile(rf"([?&]{re.escape(key)}=)[^&\s#]*", re.IGNORECASE)
    if pat.search(url):
        return pat.sub(lambda m: m.group(1) + value, url)
    sep = "&" if "?" in url else "?"
    return url + f"{sep}{key}={value}"

def _del_param(url: str, key: str) -> str:
    """يحذف param من الـ URL تماماً."""
    pat = re.compile(rf"[?&]{re.escape(key)}=[^&\s#]*", re.IGNORECASE)
    result = pat.sub("", url)
    # إصلاح علامة ? لو اتحذف أول param
    result = re.sub(r"\?&", "?", result)
    result = re.sub(r"[?&]$", "", result)
    return result

def _patch_vless_for_probe(raw: str, bug_host: str) -> str:
    """
    نسخة مؤقتة للفحص فقط — تحقن Bug Host لاختبار اتصال الـ TCP/HTTP.
    لا تُستخدم في الكونفيج النهائي.
    """
    result = raw
    for k in ("sni", "peer", "servername", "server-name"):
        result = _set_param(result, k, bug_host)
    result = _set_param(result, "host",         bug_host)
    result = _set_param(result, "path",         "%2Fws")
    result = _set_param(result, "type",         "ws")
    result = _set_param(result, "security",     "tls")
    result = _set_param(result, "allowInsecure","1")
    return result

def _patch_vless_final(raw: str) -> str:
    """
    ══════════════════════════════════════════════════════════════
    النسخة النهائية للكونفيج — host وsni فارغان تماماً.
    المستخدم يحط البوغ هوست اللي يريده بنفسه في التطبيق.
    ══════════════════════════════════════════════════════════════
    القاعدة:
      • sni=    ← فارغ
      • host=   ← فارغ
      • peer=   ← يُحذف
      • servername= ← يُحذف
      • path=%2Fws  ← ثابت
      • type=ws     ← ثابت
      • security=tls ← ثابت
      • allowInsecure=1 ← ثابت
    """
    result = raw
    # امسح كل القيم الموجودة وخلّيها فارغة
    for k in ("sni", "host"):
        result = _set_param(result, k, "")
    # احذف peer وservername وserver-name كلياً (بعض التطبيقات تتشوّش منها)
    for k in ("peer", "servername", "server-name"):
        result = _del_param(result, k)
    # Transport fixes
    result = _set_param(result, "path",         "%2Fws")
    result = _set_param(result, "type",         "ws")
    result = _set_param(result, "security",     "tls")
    result = _set_param(result, "allowInsecure","1")
    return result

def _patch_vmess_for_probe(raw: str, bug_host: str) -> str:
    """نسخة مؤقتة للفحص فقط — تحقن Bug Host للاختبار."""
    try:
        b64 = raw[len("vmess://"):]
        obj = None
        for pad in ("","=","==","==="):
            try:
                obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                break
            except Exception: continue
        if obj is None: return raw
        obj["sni"] = bug_host; obj["host"] = bug_host
        for k in ("peer","servername","server-name"):
            if k in obj: obj[k] = bug_host
        obj["net"] = "ws"; obj["path"] = "/ws"; obj["tls"] = "tls"
        obj["allowInsecure"] = True; obj["skip-cert-verify"] = True
        return "vmess://" + base64.b64encode(
            json.dumps(obj, ensure_ascii=False, separators=(",",":")).encode()
        ).decode()
    except Exception: return raw

def _patch_vmess_final(raw: str) -> str:
    """
    ══════════════════════════════════════════════════════════════
    النسخة النهائية للكونفيج VMESS — host وsni فارغان تماماً.
    المستخدم يحط البوغ هوست بنفسه.
    ══════════════════════════════════════════════════════════════
    """
    try:
        b64 = raw[len("vmess://"):]
        obj = None
        for pad in ("","=","==","==="):
            try:
                obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                break
            except Exception: continue
        if obj is None: return raw
        # فارغ تماماً — المستخدم يحطه
        obj["sni"]  = ""
        obj["host"] = ""
        for k in ("peer","servername","server-name"):
            if k in obj: del obj[k]
        obj["net"]  = "ws"
        obj["path"] = "/ws"
        obj["tls"]  = "tls"
        obj["allowInsecure"]    = True
        obj["skip-cert-verify"] = True
        return "vmess://" + base64.b64encode(
            json.dumps(obj, ensure_ascii=False, separators=(",",":")).encode()
        ).decode()
    except Exception: return raw

def patch_config_for_probe(raw: str, bug_host: str) -> str:
    """للفحص فقط — يحقن bug_host مؤقتاً."""
    return _patch_vmess_for_probe(raw, bug_host) if raw.startswith("vmess://") \
           else _patch_vless_for_probe(raw, bug_host)

def patch_config_final(raw: str) -> str:
    """للكونفيج النهائي — host وsni فارغان، المستخدم يحط الهوست."""
    return _patch_vmess_final(raw) if raw.startswith("vmess://") \
           else _patch_vless_final(raw)

# للتوافق مع بقية الكود
def patch_config(raw: str, bug_host: str) -> str:
    """deprecated — استخدم patch_config_for_probe أو patch_config_final."""
    return patch_config_for_probe(raw, bug_host)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI PROBE ENGINE v7 — 5 مستويات من الفحص
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tcp_ping(host: str, port: int) -> Optional[int]:
    """المستوى 1: TCP Connect — البوابة الأولى."""
    try:
        t0 = time.perf_counter()
        with socket.create_connection((host, port), timeout=TCP_TIMEOUT):
            return int((time.perf_counter() - t0) * 1000)
    except Exception: return None

def _ssl_insecure() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    return ctx

def ssl_check(host: str, port: int) -> tuple[bool, str]:
    """المستوى 2: SSL Handshake — هل الشهادة صالحة؟"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = True; ctx.verify_mode = ssl.CERT_REQUIRED
    try:
        conn = socket.create_connection((host, port), timeout=SSL_TIMEOUT)
        with ctx.wrap_socket(conn, server_hostname=host,
                             do_handshake_on_connect=True) as s:
            cert = s.getpeercert() or {}
            cn = next((v for f in cert.get("subject",[]) for k,v in f if k=="commonName"),"")
            return True, cn
    except ssl.SSLCertVerificationError: pass
    except Exception: return False, ""
    # بدون فحص شهادة
    try:
        conn = socket.create_connection((host, port), timeout=SSL_TIMEOUT)
        with _ssl_insecure().wrap_socket(conn, server_hostname=host,
                                         do_handshake_on_connect=True) as s:
            return False, ""
    except Exception: return False, ""

def http_ws_probe(host: str, port: int, bug_host: str,
                  path: str = "/ws") -> Optional[int]:
    """
    المستوى 3: HTTP WebSocket Upgrade — الاختبار الحقيقي لـ Downlink=0B.

    السبب الجذري للمشكلة:
    - CF يقبل SSL لأي SNI → SSL Handshake وحده لا يكفي
    - NPV/v2rayNG يضع Bug Host كـ SNI وكـ Host header في الطلب
    - Bug Host خاطئ (مثل nodejs.org) → CF يرد 530 = Downlink=0B ❌
    - Bug Host صحيح (مثل m.tiktok.com) → CF يرد 101/200/400 = Downlink ✅

    الفلتر الصارم: نقبل فقط ردود CF حقيقية، نرفض 530 وكل ردود الخطأ.
    """
    ctx = _ssl_insecure()
    # جرّب مسارات متعددة للتأكد
    paths_to_try = [path, "/", "/v2ray"] if path == "/ws" else [path]
    for try_path in paths_to_try:
        try:
            t0 = time.perf_counter()
            conn = socket.create_connection((host, port), timeout=PROBE_TIMEOUT)
            conn.settimeout(PROBE_TIMEOUT)
            sock = ctx.wrap_socket(conn, server_hostname=bug_host)
            ws_key = base64.b64encode(os.urandom(16)).decode()
            req = (
                f"GET {try_path} HTTP/1.1\r\nHost: {bug_host}\r\n"
                f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {ws_key}\r\nSec-WebSocket-Version: 13\r\n"
                f"Origin: https://{bug_host}\r\n"
                f"User-Agent: Mozilla/5.0 (compatible; v2rayN/6.3)\r\n\r\n"
            )
            sock.sendall(req.encode())
            resp = b""
            deadline = time.perf_counter() + PROBE_TIMEOUT
            while time.perf_counter() < deadline:
                try:
                    chunk = sock.recv(1024)
                    if not chunk: break
                    resp += chunk
                    if b"\r\n" in resp: break
                except (socket.timeout, BlockingIOError): break
                except Exception: break
            elapsed = int((time.perf_counter() - t0) * 1000)
            try: sock.close()
            except Exception: pass
            if not resp:
                continue
            first = resp.split(b"\r\n")[0].decode(errors="ignore").strip()
            if not first.startswith("HTTP"):
                continue
            parts = first.split()
            status = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
            # ✅ 101 = WebSocket Upgrade ناجح — الحالة المثالية
            if status == 101:
                log.debug(f"  ✅ {host}←{bug_host}: WS 101 ({elapsed}ms)")
                ai_update(bug_host, True)
                return elapsed
            # ✅ 200/301/302 = CF worker يعمل
            if status in (200, 301, 302):
                log.debug(f"  ✅ {host}←{bug_host}: HTTP {status} ({elapsed}ms)")
                ai_update(bug_host, True)
                return elapsed
            # ✅ 400/403/404/426 = CF يرد = البوابة مفتوحة (SNI صحيح)
            if status in (400, 403, 404, 426):
                resp_lower = resp[:512].lower()
                is_cf = (b"cloudflare" in resp_lower or b"cf-ray" in resp_lower
                         or b"cf-cache" in resp_lower or b"server: cloudflare" in resp_lower
                         or status in (400, 426))
                if is_cf:
                    log.debug(f"  ✅ {host}←{bug_host}: CF {status} ({elapsed}ms)")
                    ai_update(bug_host, True)
                    return elapsed
            # ❌ 530 = CF Error Page = SNI خاطئ = Downlink=0B
            # ❌ 5xx = خطأ سيرفر
            log.debug(f"  ❌ {host}←{bug_host}: {status} rejected")
        except Exception as e:
            log.debug(f"  probe {host}←{bug_host}: {type(e).__name__}")
    ai_update(bug_host, False)
    return None

def multi_probe(host: str, port: int) -> tuple[list[str], str, int]:
    """
    ══════════════════════════════════════════════════════════════
    Multi Bug-Host Probe — الفحص الدقيق لكل Bug Host.

    المنهجية:
    1. يجرب كل Bug Host بالتوازي (سرعة)
    2. أي Bug Host ينجح → يعيد التحقق مرة ثانية مستقلة (دقة 100%)
    3. يُدرج في القائمة فقط إذا نجح مرتين متتاليتين

    هذا يضمن:
    - لا false positives (نتيجة خاطئة إيجابية)
    - فقط Bug Hosts التي تعمل بشكل موثوق تُقبل
    ══════════════════════════════════════════════════════════════
    """
    hosts_ordered = ai_best_order()  # AI يرتب بناءً على التاريخ

    # تقسيم الهوستات إلى دفعات
    for i in range(0, len(hosts_ordered), PROBE_BATCH_SIZE):
        batch = hosts_ordered[i:i+PROBE_BATCH_SIZE]
        batch_timings = {}

        # فحص الدفعة بالتوازي
        with ThreadPoolExecutor(max_workers=min(len(batch), PROBE_BATCH_SIZE)) as ex:
            futures = {ex.submit(http_ws_probe, host, port, bh): bh for bh in batch}
            for fut in as_completed(futures):
                bh = futures[fut]
                try:
                    ms = fut.result()
                    if ms is not None:
                        batch_timings[bh] = ms
                except Exception:
                    pass

        # إذا وجدنا أي ناجح في هذه الدفعة، نعيد التحقق منهم فقط ونتوقف
        if batch_timings:
            # إعادة تحقق لكل ناجح في الدفعة (parallel)
            verified = {}
            with ThreadPoolExecutor(max_workers=min(len(batch_timings), 3)) as ex2:
                rev_futures = {ex2.submit(http_ws_probe, host, port, bh): bh for bh in batch_timings}
                for fut2 in as_completed(rev_futures):
                    bh = rev_futures[fut2]
                    try:
                        ms2 = fut2.result()
                        if ms2 is not None:
                            avg = (batch_timings[bh] + ms2) // 2
                            verified[bh] = avg
                        else:
                            log.debug(f"  ⚠️ Re-verify failed: {host}←{bh} (false positive removed)")
                            ai_update(bh, False)
                    except Exception:
                        pass

            if verified:
                compat = list(verified.keys())
                best = min(verified, key=verified.get)
                return compat, best, verified[best]

        # إذا لم نجد أي ناجح، ننتقل للدفعة التالية
        continue

    # إذا لم ينجح أي هوست نهائياً
    return [], "", 0

def ai_diagnose(host: str, ping: Optional[int], ssl_ok: bool,
                compat_hosts: list, is_cf: bool, is_vps: bool) -> str:
    """
    المستوى 5: AI Diagnosis — يكتب تقريراً ذكياً مثل طبيب يشخّص.
    
    يحلل كل المعطيات ويكتب سبب النجاح أو الفشل بوضوح.
    """
    if ping is None:
        return "❌ TCP Timeout: السيرفر لا يستجيب — قد يكون محظوراً أو أوف لاين"
    if not compat_hosts:
        return "❌ Zero-Data: TCP يصل لكن Bug Hosts لا تمرّر ترافيك — مشكلة CF Routing"
    compat_count = len(compat_hosts)
    total = len(ALL_BUG_HOSTS)
    ops = []
    if set(compat_hosts) & set(TARGET_HOSTS["oodi"]): ops.append("Oodi")
    if set(compat_hosts) & set(TARGET_HOSTS["zain"]): ops.append("Zain")
    if set(compat_hosts) & set(TARGET_HOSTS["voxi"]): ops.append("Voxi")
    ops_str = " + ".join(ops) if ops else "غير محدد"
    type_str = ("CF ⚡" if is_cf else "") + (" VPS 🚀" if is_vps else "")
    quality = "🏆 Elite" if compat_count >= 8 else \
              "⭐⭐⭐ Premium" if compat_count >= 4 else \
              "⭐⭐ Good" if compat_count >= 2 else "⭐ Basic"
    return (f"✅ {quality} | {type_str} | {compat_count}/{total} Bug Hosts | "
            f"Ping {ping}ms | Operators: {ops_str}")



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHECK_RAW v7 — الفحص الكامل بالذكاء الاصطناعي
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ── قائمة البوغ هوستس المدمجة من الموفر — نرفض أي كونفيج يحتويها ──────────
# هذه هوستات يحطها الموفر مدمجة في الكونفيج، مما يعني أن المستخدم
# لا يستطيع تغييرها بسهولة — نرفض هذه الكونفيجات
_PROVIDER_EMBEDDED_PATTERNS: list[str] = [
    "speedtest.", "fast.com", "ookla.",
    "akamai", "amazonaws", "azureedge", "msecnd",
    "gstatic", "googlevideo",
    "fbcdn", "fbsbx",
    "twimg", "t.co",
    "whatsapp.net",
    # موفرون معروفون بحقن هوست محدد لا يمكن تغييره
    "zain.com", "oodi.com.sa", "mobily.com.sa", "ooredoo.qa",
    # CDN أسماء موفرين حكومية
    "gov.", ".edu.",
]

# الأنماط الصحيحة للـ path — نقبل فقط هذه
_VALID_WS_PATH_RE = re.compile(
    r"^/(?:ws|vws|linkvws|link|v2ray|proxy|grpc|websocket|wss?|"
    r"ray|xray|vmess|vless|trojan|relay|[a-z0-9]{3,20})(?:/.*)?$",
    re.IGNORECASE
)

def _is_valid_structure(raw: str) -> bool:
    """
    يتحقق أن الكونفيج يطابق هيكلية السيرفر الشغال تماماً:
      ✅ net=ws (WebSocket)
      ✅ port=443 (TLS فقط)
      ✅ tls=tls
      ✅ path يبدأ بـ / وله شكل معقول
      ✅ aid=0 (لا AES-128 القديم)
    """
    if raw.startswith("vmess://"):
        try:
            b64 = raw[len("vmess://"):]
            obj = None
            for pad in ("","=","==","==="):
                try:
                    obj = json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
                    break
                except Exception: continue
            if not obj: return False
            if str(obj.get("port","")) != "443":  return False
            if obj.get("net","") not in ("ws","websocket"): return False
            if obj.get("tls","") not in ("tls","xtls"):     return False
            if str(obj.get("aid","0")) not in ("0",""):      return False
            path = obj.get("path","")
            if path and not _VALID_WS_PATH_RE.match(path): return False
            return True
        except Exception: return False
    else:  # vless
        if "type=ws" not in raw.lower() and "net=ws" not in raw.lower(): return False
        if ":443" not in raw: return False
        if "security=tls" not in raw.lower() and "tls" not in raw.lower(): return False
        path_m = re.search(r"[?&]path=([^&\s#]+)", raw, re.IGNORECASE)
        if path_m:
            path = path_m.group(1).replace("%2F","/").replace("%2f","/")
            if not _VALID_WS_PATH_RE.match(path): return False
        return True

def _has_embedded_host(raw: str) -> bool:
    """
    يرفض الكونفيجات التي تحتوي على host مدمج من الموفر لا يمكن تغييره.
    يقبل: host فارغ، host = أحد Bug Hosts المعتمدة.
    """
    orig_sni = extract_sni(raw).lower()
    if not orig_sni: return False
    # Bug Host معتمد = نظيف تماماً (مثل السيرفر الشغال www.pubgmobile.com)
    for bh in ALL_BUG_HOSTS:
        if orig_sni == bh.lower(): return False
    # نمط موفر مدمج = ارفض
    for pat in _PROVIDER_EMBEDDED_PATTERNS:
        if pat in orig_sni:
            log.debug(f"⛔ Provider-embedded: {orig_sni}")
            return True
    return False

def check_raw(raw: str) -> Optional[V2Config]:
    """
    ══════════════════════════════════════════════════════════════════
    فحص كونفيج واحد — 6 مراحل دقيقة 100%:

    0️⃣ Embedded Host Check → رفض الكونفيجات بهوست مدمج من الموفر
    1️⃣ TCP Ping            → هل السيرفر حي؟ (< MAX_PING_MS)
    2️⃣ SSL Verify          → هل TLS يعمل؟ (معلومات + رفض إذا فاشل كلياً)
    3️⃣ CF/VPS Detection    → ما نوع السيرفر؟
    4️⃣ Deep Bug-Host Probe → فحص كل هوست واحد واحد بدقة عالية
       - يجرب TCP + SSL + HTTP WS لكل Bug Host
       - يرفض أي هوست يعطي 530/5xx/empty
       - يقبل فقط: 101 WS أو 200/301/302 أو 400/403 من CF حقيقي
    5️⃣ Final Config        → host="" sni="" فارغ تماماً في الكونفيج
       - المستخدم يحط البوغ هوست اللي يريده بنفسه
    ══════════════════════════════════════════════════════════════════
    """
    # ── 0a. MD5 Cache — لا نفحص ما فُحص سابقاً ────────────────────────────
    if ai_is_seen(raw):
        return None

    # استخراج server:port
    m = re.search(r"@([^:/\s\]#]+):(\d+)", raw)
    if not m: return None
    host = m.group(1)
    try: port = int(m.group(2))
    except ValueError: return None
    if port != TARGET_PORT: return None

    proto    = "VLESS" if raw.startswith("vless://") else "VMESS"
    orig_sni = extract_sni(raw)

    # ── 0b. Structure Filter — يقبل فقط هيكلية السيرفر الشغال ─────────────
    # net=ws, port=443, tls=tls, aid=0, path=/ws* مثل /linkvws /vws /ws
    if not _is_valid_structure(raw):
        log.debug(f"⛔ Invalid structure (not WS/TLS/443): {host}")
        return None

    # ── 0c. Embedded Host Filter ────────────────────────────────────────────
    if _has_embedded_host(raw):
        log.debug(f"⛔ Embedded provider host: {orig_sni} | {host}")
        return None

    # ── 1. TCP Ping ─────────────────────────────────────────────────────────
    ping = tcp_ping(host, port)
    if ping is None or ping > MAX_PING_MS:
        log.debug(f"⛔ TCP fail/slow: {host} | {ping}ms")
        return None

    # ── 2. SSL Verify ───────────────────────────────────────────────────────
    ssl_ok, ssl_cn = ssl_check(host, port)
    # نرفض إذا SSL فاشل تماماً (لا cert على الإطلاق) — علامة سيء
    if not ssl_ok and not ssl_cn:
        log.debug(f"⛔ SSL completely failed: {host}")
        return None

    # ── 3. CF / VPS Detection ───────────────────────────────────────────────
    try:    resolved_ip = socket.gethostbyname(host)
    except Exception: resolved_ip = ""
    is_cf  = (is_cf_ip(resolved_ip) if resolved_ip else False) or \
             any(k in (host + raw).lower() for k in CF_KEYWORDS)
    is_vps = any(k in (host + raw).lower() for k in VPS_KEYWORDS)
    server_type = "CF" if is_cf else ("VPS" if is_vps else "Unknown")

    # ── 4. Deep Bug-Host Probe (الفحص الحقيقي) ─────────────────────────────
    # يجرب كل Bug Host واحد واحد بشكل مستقل ودقيق
    if CUSTOM_SNI:
        # وضع يدوي — فحص الهوست المحدد فقط
        ms = http_ws_probe(host, port, CUSTOM_SNI)
        if ms is not None:
            compat, best, probe_ms = [CUSTOM_SNI], CUSTOM_SNI, ms
        else:
            log.debug(f"⛔ CUSTOM_SNI probe failed: {host} ← {CUSTOM_SNI}")
            return None
    else:
        # وضع AI — فحص كل هوست بالتوازي
        compat, best, probe_ms = multi_probe(host, port)
        if len(compat) < MIN_COMPAT_HOSTS:
            log.debug(f"⛔ Zero-Data (no bug host works): {host} | 0/{len(ALL_BUG_HOSTS)}")
            return None

    # ── 5. Final Config — host="" sni="" فارغ تماماً ────────────────────────
    # المستخدم يحط البوغ هوست الذي يريده بنفسه في التطبيق
    raw_patched = patch_config_final(raw)

    diagnosis = ai_diagnose(host, ping, ssl_ok, compat, is_cf, is_vps)

    log.info(
        f"✅ PASS | {host} | {proto} | {server_type} | "
        f"ping={ping}ms | probe={probe_ms}ms | "
        f"{len(compat)}/{len(ALL_BUG_HOSTS)} bug hosts | "
        f"hosts=[{', '.join(compat[:3])}{'...' if len(compat)>3 else ''}]"
    )

    # حفظ IP الناجح في الذاكرة الدائمة
    if resolved_ip: ai_mark_good_ip(resolved_ip)

    return V2Config(
        raw=raw, raw_patched=raw_patched,
        host=host, port=port, ping_ms=ping, proto=proto,
        original_sni=orig_sni, injected_sni="",   # ← فارغ دائماً
        ssl_ok=ssl_ok, ssl_cert_cn=ssl_cn,
        is_cf=is_cf, is_vps=is_vps,
        compatible_hosts=compat, best_bug_host=best, probe_ms=probe_ms,
        ai_diagnosis=diagnosis, server_type=server_type,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FETCH ENGINE v7 — جمع الكونفيجات مع anti-bot كامل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _fetch(url: str) -> list[str]:
    """
    يجلب الكونفيجات من مصدر واحد مع:
    - Anti-bot v4: rotating UA + stealth headers
    - Base64 decode (عدة padding variants)
    - YAML/Clash parse
    - Telegram page scraping
    - Rate-limit respect
    """
    try:
        time.sleep(random.uniform(0.05, 0.3))
        sess = _sess()
        h = _headers()
        if "t.me/s/" in url:
            h["Referer"] = "https://t.me/"
            h["X-Requested-With"] = "XMLHttpRequest"
        r = sess.get(url, timeout=FETCH_TIMEOUT, headers=h,
                     allow_redirects=True, stream=False)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 5))
            time.sleep(min(wait, 10))
            r = sess.get(url, timeout=FETCH_TIMEOUT, headers=_headers(),
                         allow_redirects=True)
        if r.status_code not in (200, 206): return []
        text = r.text

        # ── Plain text scan ─────────────────────────────────────────────────
        found = CONFIG_RE.findall(text)

        # ── Base64 decode (full blob) ───────────────────────────────────────
        if not found:
            b64c = re.sub(r"\s+", "", text)
            for pad in ("", "=", "=="):
                try:
                    dec = base64.b64decode(b64c + pad).decode("utf-8", errors="ignore")
                    found = CONFIG_RE.findall(dec)
                    if found: break
                except Exception: continue

        # ── Line-by-line base64 ─────────────────────────────────────────────
        if not found:
            for line in text.splitlines():
                line = line.strip()
                if len(line) > 20 and not line.startswith(("vless://","vmess://")):
                    try:
                        dec = base64.b64decode(line + "==").decode("utf-8", errors="ignore")
                        found.extend(CONFIG_RE.findall(dec))
                    except Exception: pass

        # ── Telegram HTML scrape ────────────────────────────────────────────
        if not found and "t.me" in url:
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = clean.replace("&amp;","&").replace("&#43;","+") \
                         .replace("&#61;","=").replace("%3A",":").replace("%2F","/")
            found = CONFIG_RE.findall(clean)

        # ── YAML/Clash: extract proxies ─────────────────────────────────────
        if not found and ("proxies:" in text or "Proxy:" in text):
            found = CONFIG_RE.findall(text)

        # Port 443 only + dedup
        found = list(dict.fromkeys(c for c in found if ":443" in c))
        if found: log.info(f"✓ {len(found):>4}  ←  {url[:65]}")
        return found

    except requests.exceptions.SSLError:
        try:
            r2 = requests.get(url, timeout=FETCH_TIMEOUT,
                              headers=_headers(), verify=False)
            return list(dict.fromkeys(c for c in CONFIG_RE.findall(r2.text) if ":443" in c))
        except Exception: return []
    except Exception: return []


def collect_configs() -> list[str]:
    """
    جمع الكونفيجات مع AI guidance:
    1. يرتب المصادر بناءً على الأداء التاريخي (ai_rank_sources)
    2. يتخطى المصادر الميتة تماماً (ai_dead_sources)
    3. يُحدّث تقييم كل مصدر (ai_update_source)
    4. يُنوّع: يضمن مصادر جديدة في كل جولة
    """
    dead = ai_dead_sources()
    active   = [u for u in SOURCES if u not in dead]
    skipped  = len(SOURCES) - len(active)
    ranked   = ai_rank_sources(active)

    # تنويع: خلط 20% من المصادر لضمان اكتشاف جديد
    split = int(len(ranked) * 0.80)
    top_ranked  = ranked[:split]
    rest        = ranked[split:]
    random.shuffle(rest)
    ordered = top_ranked + rest

    log.info(
        f"🌐 Fetching: {len(ordered)}/{len(SOURCES)} sources "
        f"(skipped {skipped} dead) [{FETCH_WORKERS} workers]"
    )

    all_raw: list[str] = []
    source_results: dict = {}

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        future_map = {ex.submit(_fetch, u): u for u in ordered}
        for fut in as_completed(future_map):
            url = future_map[fut]
            try:
                results = fut.result()
                hits    = len(results)
                source_results[url] = hits
                all_raw.extend(results)
            except Exception:
                source_results[url] = 0

    # تحديث AI memory للمصادر
    for url, hits in source_results.items():
        fails = 1 if hits == 0 else 0
        ai_update_source(url, hits, fails)

    unique = list(dict.fromkeys(all_raw))
    good_sources = sum(1 for h in source_results.values() if h > 0)
    log.info(
        f"📦 {len(unique)} unique configs | "
        f"{good_sources}/{len(ordered)} sources active | "
        f"{skipped} dead skipped"
    )
    return unique


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PARALLEL CHECK + STOP GATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def run_checks(raws: list[str]) -> list[V2Config]:
    # اقتطاع العدد إذا كان كبيراً جداً
    if len(raws) > MAX_CONFIGS_TO_CHECK:
        log.info(f"✂️ Too many configs ({len(raws)}), checking only first {MAX_CONFIGS_TO_CHECK}")
        raws = raws[:MAX_CONFIGS_TO_CHECK]

    log.info(f"⚡ Checking {len(raws)} configs [{CHECK_WORKERS} workers | stop@{STOP_AFTER_FOUND} | max runtime {MAX_RUNTIME_SECONDS}s] ...")
    live: list[V2Config] = []
    stop = threading.Event()
    lock = threading.Lock()
    start_time = time.time()

    def _worker(raw: str) -> Optional[V2Config]:
        if stop.is_set():
            return None
        # تحقق من الوقت المنقضي قبل كل فحص
        if time.time() - start_time > MAX_RUNTIME_SECONDS:
            log.warning("⏰ Global timeout reached, stopping further checks")
            stop.set()
            return None
        try:
            return check_raw(raw)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as ex:
        futures = {ex.submit(_worker, r): r for r in raws}
        for fut in as_completed(futures):
            if stop.is_set():
                try:
                    fut.cancel()
                except Exception:
                    pass
                continue
            try:
                res = fut.result()
            except Exception:
                res = None
            if res:
                with lock:
                    live.append(res)
                    n = len(live)
                    if n % 50 == 0:
                        log.info(f"  📊 {n} live | {ai_report()}")
                    if n >= STOP_AFTER_FOUND:
                        stop.set()
                        log.info(f"🛑 Stop gate: {STOP_AFTER_FOUND} reached")
                    # أيضاً تحقق من الوقت بعد كل إضافة
                    if time.time() - start_time > MAX_RUNTIME_SECONDS:
                        log.warning("⏰ Global timeout reached, stopping")
                        stop.set()

    log.info(f"✅ {len(live)} live configs (Zero-Data filtered)")
    log.info(ai_report())
    return live


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GEO ENRICHMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_geo:   dict[str, tuple] = {}
_glock: threading.Lock   = threading.Lock()

def get_geo(ip: str) -> tuple[str, str, str]:
    with _glock:
        if ip in _geo: return _geo[ip]
    for url in [
        f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp",
        f"https://ipapi.co/{ip}/json/",
    ]:
        try:
            rj = _sess().get(url, timeout=3, headers=_headers()).json()
            if rj.get("status") == "success" or rj.get("country_code"):
                res = (rj.get("countryCode") or rj.get("country_code","??"),
                       rj.get("country","Unknown"),
                       rj.get("isp") or rj.get("org",""))
                with _glock: _geo[ip] = res
                return res
        except Exception: continue
    result = ("??","Unknown","")
    with _glock: _geo[ip] = result
    return result

def enrich(cfg: V2Config) -> V2Config:
    try:
        ip = socket.gethostbyname(cfg.host)
        cfg.country_code, cfg.country, cfg.isp = get_geo(ip)
        if not cfg.is_cf: cfg.is_cf = is_cf_ip(ip)
    except Exception: pass
    low = (cfg.raw + cfg.host + cfg.isp).lower()
    if not cfg.is_cf:  cfg.is_cf  = any(k in low for k in CF_KEYWORDS)
    if not cfg.is_vps: cfg.is_vps = any(k in low for k in VPS_KEYWORDS)
    return cfg



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MESSAGE BUILDER v7 — رسائل تيليغرام احترافية مع تقرير AI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _ping_label(ms: int) -> str:
    if ms < 80:  return "🟢 Ultra Fast"
    if ms < 150: return "🟢 Fast"
    if ms < 300: return "🟡 Good"
    if ms < 500: return "🟠 Moderate"
    return               "🔴 Slow"

def _rating(cfg: V2Config) -> str:
    oodi = set(TARGET_HOSTS["oodi"]); zain = set(TARGET_HOSTS["zain"])
    voxi = set(TARGET_HOSTS["voxi"]); compat = set(cfg.compatible_hosts)
    hits = len(compat & (oodi | zain | voxi))
    if hits >= 8 and cfg.ping_ms < 150: return "⭐⭐⭐⭐⭐ 🏆 ELITE"
    if hits >= 5 or cfg.probe_ms < 150: return "⭐⭐⭐⭐ Excellent"
    if hits >= 3:                        return "⭐⭐⭐⭐ Premium"
    if hits >= 1:                        return "⭐⭐⭐ Compatible"
    return                                      "⭐⭐ Basic"

def _operators(cfg: V2Config) -> str:
    compat = set(cfg.compatible_hosts)
    ops = []
    if compat & set(TARGET_HOSTS["voxi"]): ops.append("📶 Voxi")
    if compat & set(TARGET_HOSTS["zain"]): ops.append("📶 Zain")
    if compat & set(TARGET_HOSTS["oodi"]): ops.append("📶 Oodi")
    return "  ".join(ops) or "—"

def _bug_hosts_short(cfg: V2Config) -> str:
    if not cfg.compatible_hosts: return "—"
    shorts = []
    for h in cfg.compatible_hosts[:6]:
        s = h.replace("m.","").replace("www.","").replace("web.","")
        shorts.append(s.split(".")[0])
    suf = f" +{len(cfg.compatible_hosts)-6}" if len(cfg.compatible_hosts) > 6 else ""
    return " · ".join(shorts) + suf

def build_message(cfg: V2Config) -> str:
    type_lbl   = ("VPS 🚀" if cfg.is_vps else "Shared") + (" + CF ⚡" if cfg.is_cf else "")
    ssl_lbl    = f"✅ ({cfg.ssl_cert_cn})" if cfg.ssl_ok else "⚠️ Self-Signed"
    probe_lbl  = f"{cfg.probe_ms}ms ✅" if cfg.probe_ms > 0 else "—"
    compat_str = ", ".join(cfg.compatible_hosts) if cfg.compatible_hosts else "—"
    n_compat   = len(cfg.compatible_hosts)
    n_total    = len(ALL_BUG_HOSTS)
    return (
        f"🤖 <b>Ashaq Team — AI Hunter v7</b> 🤖\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 <b>Country:</b>    {cfg.country_code}  {cfg.country}\n"
        f"🔹 <b>Protocol:</b>   {cfg.proto}  |  {type_lbl}\n"
        f"🔒 <b>SSL/TLS:</b>    {ssl_lbl}\n"
        f"⚡ <b>TCP Ping:</b>   {cfg.ping_ms}ms — {_ping_label(cfg.ping_ms)}\n"
        f"🌐 <b>HTTP Probe:</b>  {probe_lbl}\n"
        f"🏢 <b>ISP:</b>        {cfg.isp or 'Unknown'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Networks:</b>   {_operators(cfg)}\n"
        f"⭐ <b>Rating:</b>     {_rating(cfg)}\n"
        f"🗂 <b>Bug Hosts ({n_compat}/{n_total}) — اختر الأنسب لك:</b>\n"
        f"<code>{compat_str}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ℹ️ <b>الهوست فارغ</b> — افتح الكونفيج وأضف البوغ هوست المناسب لشبكتك\n"
        f"   مثال Oodi: <code>m.tiktok.com</code>\n"
        f"   مثال Zain: <code>m.tiktok.com</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>AI:</b> <i>{cfg.ai_diagnosis}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>{cfg.raw_patched}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"👥 @V2rayashaq"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TELEGRAM + SUB FILE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def send_to_telegram(cfg: V2Config) -> bool:
    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN غير موجود في البيئة. لن يتم الإرسال.")
        return False
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
                log.warning(f"Rate limit — sleep {w}s"); time.sleep(w); continue
            if res.ok:
                log.info(f"✅ تم الإرسال إلى تليغرام: {cfg.host}")
                return True
            log.error(f"❌ فشل الإرسال (HTTP {res.status_code}): {res.text[:200]}")
            return False
        except requests.RequestException as e:
            log.warning(f"⚠️ محاولة {attempt+1} فشلت: {e}")
            time.sleep(3)
    return False

def save_subscription(configs: list[V2Config]) -> None:
    top  = configs[:MAX_SUB_CONFIGS]
    blob = "\n".join(c.raw_patched for c in top)
    try:
        with open(SUB_FILE, "w", encoding="utf-8") as f:
            f.write(base64.b64encode(blob.encode()).decode())
        log.info(f"💾 Saved {len(top)} configs → {SUB_FILE}")
    except OSError as e:
        log.error(f"Cannot write sub: {e}")

# ─── دالة لاختبار توكن البوت والقناة قبل البدء ─────────────────────────────
def test_telegram_bot():
    """إرسال رسالة اختبارية للتأكد من صلاحية التوكن والقناة"""
    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN غير موجود، لن يتم الإرسال.")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        r = requests.get(url, timeout=10)
        if r.ok:
            bot_name = r.json().get("result", {}).get("first_name", "Unknown")
            log.info(f"✅ اتصال تليغرام ناجح: @{bot_name}")
        else:
            log.error(f"❌ توكن البوت غير صالح: {r.text[:100]}")
            return False
    except Exception as e:
        log.error(f"❌ فشل الاتصال بتليغرام: {e}")
        return False

    # اختبار الإرسال إلى القناة
    test_payload = {
        "chat_id": CHAT_ID,
        "text": "🧪 اختبار من AI Hunter v7 - البوت يعمل بنجاح ✅",
        "parse_mode": "HTML"
    }
    try:
        r2 = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                           json=test_payload, timeout=10)
        if r2.ok:
            log.info(f"✅ تم إرسال رسالة اختبار إلى {CHAT_ID}")
            return True
        else:
            log.error(f"❌ فشل إرسال الاختبار إلى {CHAT_ID}: {r2.text[:200]}")
            return False
    except Exception as e:
        log.error(f"❌ استثناء أثناء اختبار الإرسال: {e}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main() -> None:
    parser = argparse.ArgumentParser(description="V2Ray Ultimate Hunter v7 — AI Edition")
    parser.add_argument("--dry-run", action="store_true", help="No Telegram posting")
    parser.add_argument("--sni", default="", help="Force SNI for all configs")
    args = parser.parse_args()

    global CUSTOM_SNI
    if args.sni: CUSTOM_SNI = args.sni.strip()

    t0 = time.time()
    log.info("╔══════════════════════════════════════════════════════════╗")
    log.info("║  🤖 V2RAY ULTIMATE HUNTER v7 — AI EDITION               ║")
    log.info(f"║  📡 {len(SOURCES):<4} sources | AI Bug-Host Engine | Zero-Data  ║")
    log.info("╚══════════════════════════════════════════════════════════╝")
    with _ai_lock:
        run_n = _ai_memory["total_runs"]
        dead_n = len(ai_dead_sources())
        good_ips = len(_ai_memory.get("known_good_ips",[]))
    log.info(
        f"🧠 AI x10 Memory | Run #{run_n} | "
        f"{len(ALL_BUG_HOSTS)} Bug Hosts | "
        f"{good_ips} good IPs | "
        f"💀{dead_n} dead sources pruned"
    )
    log.info(f"🔑 CUSTOM_SNI: {CUSTOM_SNI or '(auto-detect best bug host)'}")
    if args.dry_run: log.info("🔇 Dry-run mode")

    # اختبار تليغرام قبل البدء (إذا لم يكن dry-run)
    if not args.dry_run:
        test_telegram_bot()
    else:
        log.info("🔇 وضع الاختبار الجاف، لن يتم إرسال أي رسالة.")

    # 1. Collect
    raws = collect_configs()
    if not raws: log.error("Nothing collected — exit"); return

    # 2. Smart pre-sort: CF/VPS first (أكثر احتمالاً للنجاح)
    raws.sort(key=lambda x: (
        not any(k in x.lower() for k in CF_KEYWORDS),
        not any(k in x.lower() for k in VPS_KEYWORDS),
    ))

    # 3. AI Check + Zero-Data Filter
    live = run_checks(raws)
    if not live:
        log.error("No live configs — exit")
        return

    # 4. Geo enrich
    log.info("🔍 Geo enrichment ...")
    with ThreadPoolExecutor(max_workers=30) as ex:
        live = list(ex.map(enrich, live))

    # 5. Sort by score
    live.sort(key=lambda c: c.score(), reverse=True)

    # 6. AI Top-10 Report
    log.info(f"\n📊 Top 10 — AI Selection:")
    log.info("  Rank  Type   Ping   Probe  Compat  Country  Best Bug Host")
    log.info("  " + "─" * 68)
    for i, c in enumerate(live[:10], 1):
        t = ("🚀" if c.is_vps else "  ") + ("⚡" if c.is_cf else "  ") + \
            ("🔒" if c.ssl_ok else "  ")
        p = f"{c.probe_ms}ms" if c.probe_ms else "  —  "
        log.info(f"  {i:>2}.  {t}  "
                 f"{c.ping_ms:>4}ms  {p:>6}  "
                 f"{len(c.compatible_hosts):>2}/{len(ALL_BUG_HOSTS):<2}  "
                 f"{c.country_code:<4}  {c.best_bug_host[:28]}")

    # 7. Post to Telegram
    posted = 0
    for cfg in live:
        if posted >= MAX_POSTS: break
        if args.dry_run:
            log.info(f"[DRY] {cfg.host} | {cfg.best_bug_host} | {cfg.ai_diagnosis}")
            posted += 1
        else:
            if send_to_telegram(cfg):
                posted += 1
                log.info(f"📨 Posted {posted}/{MAX_POSTS}: {cfg.host} → {cfg.best_bug_host}")
                time.sleep(2)
            else:
                log.error(f"❌ فشل إرسال {cfg.host} إلى تليغرام")

    # 8. Save subscription
    save_subscription(live)

    # 9. Update AI memory with run stats
    with _ai_lock:
        _ai_memory["total_runs"]   += 1
        _ai_memory["total_posted"] += posted
        _ai_memory["last_run"] = datetime.now(timezone.utc).isoformat()[:16]
    _save_ai_memory(_ai_memory)

    elapsed = int(time.time() - t0)
    dead_count = len(ai_dead_sources())
    log.info(
        f"\n🏁 Done in {elapsed}s | {len(live)} live / {len(raws)} scanned / "
        f"{posted} posted | 💀{dead_count} dead sources pruned"
    )
    log.info(ai_report())

    # تشخيص نهائي إذا لم يتم نشر أي شيء
    if posted == 0 and not args.dry_run:
        log.error("🚨 لم يتم نشر أي رسالة! الأسباب المحتملة:")
        log.error("1. BOT_TOKEN غير صحيح أو غير مضبوط في Secrets")
        log.error("2. البوت ليس مشرفاً في القناة @V2rayashaq")
        log.error("3. لا توجد كونفيج حية (Zero-Data filter)")
        log.error("4. فشل الاتصال بتليغرام (انظر الأخطاء أعلاه)")


if __name__ == "__main__":
    main()
