#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  🤖 V2RAY ULTIMATE HUNTER v10 — VIRUS MODE — ASHAQ TEAM               ║
# ║  974+ Sources | Self-Evolving | Aggressive AI | CF WS+TLS+443          ║
# ║  يطور نفسه كل جولة — يضيف مصادر — يتعلم — لا يتوقف                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
from __future__ import annotations
import os,sys,re,json,time,ssl,socket,base64,random,hashlib
import threading,argparse,ipaddress,logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import requests, urllib3
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
        logging.FileHandler("v2ray_hunt.log", encoding="utf-8", mode="a"),
    ],
)
log = logging.getLogger("V10")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN   = os.environ.get("BOT_TOKEN","")
CHAT_ID     = "@V2rayashaq"
ADMIN_USER  = "@genie_2000"
CUSTOM_SNI  = os.environ.get("CUSTOM_SNI","")
SUB_FILE    = "sub_link.txt"
TARGET_PORT = 443

MAX_POSTS       = 5
MAX_SUB         = 200
STOP_AFTER      = 50
MAX_CHECK_RAWS  = 10000

# Aggressive timeouts
TCP_TIMEOUT   = 2.0
SSL_TIMEOUT   = 3.0
PROBE_TIMEOUT = 3.5
FETCH_TIMEOUT = 10
MAX_PING_MS   = 800

FETCH_WORKERS = 150
CHECK_WORKERS = 150
GEO_WORKERS   = 40

# Hard deadline — يُضبط في main() فقط
HARD_DEADLINE_MINS = 18
_deadline: float = 0.0

def deadline_ok() -> bool:
    return _deadline == 0.0 or time.time() < _deadline

def deadline_left() -> int:
    if _deadline == 0.0: return 9999
    return max(0, int(_deadline - time.time()))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUG HOSTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALL_BUG_HOSTS = [
    "m.tiktok.com","www.snapchat.com","m.instagram.com",
    "m.facebook.com","www.wechat.com","m.youtube.com",
    "www.pubgmobile.com","web.telegram.org","open.spotify.com",
    "web.whatsapp.com","invite.viber.com","en.help.roblox.com",
]
TARGET_HOSTS = {
    "oodi": ALL_BUG_HOSTS[:],
    "zain": ["m.tiktok.com"],
    "voxi": [],
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI PERSISTENT MEMORY — يتعلم ويتطور كل جولة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_AI_FILE  = "ai_memory.json"
_ai_lock  = threading.Lock()
_AI_SCHEMA = {
    "v":10, "runs":0, "posted":0, "last":"",
    "bug_wins":{}, "bug_fails":{},
    "src_hits":{}, "src_fails":{},
    "good_ips":[], "bad_ips":[], "seen_md5":[],
    "path_wins":{}, "host_wins":{},
    "total_checked":0, "total_passed":0,
    "avg_ping":0.0, "avg_probe":0.0, "cf_ratio":0.5,
    "filter_stats":{"total":0,"struct":0,"locked":0,"tcp":0,"probe":0,"passed":0},
    # Self-evolution data
    "discovered_sources":[],  # مصادر اكتشفها AI
    "source_keywords":[],     # كلمات مفتاحية وجدها
    "evolution_log":[],       # سجل التطور
}

def _ai_load() -> dict:
    try:
        d = json.loads(open(_AI_FILE,encoding="utf-8").read())
        for k,v in _AI_SCHEMA.items():
            if k not in d: d[k] = v if not isinstance(v,dict) else {**v}
            elif isinstance(v,dict) and isinstance(d[k],dict):
                for kk,vv in v.items():
                    d[k].setdefault(kk,vv)
        return d
    except Exception:
        return dict(_AI_SCHEMA)

def _ai_save(m:dict) -> None:
    try:
        m["seen_md5"]            = m.get("seen_md5",[])[-10000:]
        m["good_ips"]            = list(set(m.get("good_ips",[])))[-1000:]
        m["bad_ips"]             = list(set(m.get("bad_ips",[])))[-500:]
        m["discovered_sources"]  = m.get("discovered_sources",[])[-500:]
        m["evolution_log"]       = m.get("evolution_log",[])[-50:]
        open(_AI_FILE,"w",encoding="utf-8").write(
            json.dumps(m,ensure_ascii=False,separators=(",",":")))
    except Exception as e:
        log.warning(f"AI save: {e}")

_AI:dict = _ai_load()

# ── AI core functions ────────────────────────────────────────────────────
def ai_seen(raw:str) -> bool:
    h = hashlib.md5(raw.encode()).hexdigest()
    with _ai_lock:
        seen = _AI.setdefault("seen_md5",[])
        if h in seen: return True
        seen.append(h); return False

def ai_good_ip(ip:str):
    with _ai_lock:
        g=_AI.setdefault("good_ips",[]); 
        if ip not in g: g.append(ip)

def ai_bad_ip(ip:str):
    with _ai_lock:
        b=_AI.setdefault("bad_ips",[])
        if ip not in b: b.append(ip)

def ai_is_bad_ip(ip:str) -> bool:
    with _ai_lock: return ip in _AI.get("bad_ips",[])

def ai_bug_update(bh:str, ok:bool):
    with _ai_lock:
        k="bug_wins" if ok else "bug_fails"
        _AI[k][bh] = _AI[k].get(bh,0)+1

def ai_path_win(path:str):
    with _ai_lock:
        _AI.setdefault("path_wins",{})[path] = _AI["path_wins"].get(path,0)+1

def ai_src_update(url:str, hits:int):
    with _ai_lock:
        if hits>0: _AI["src_hits"][url]  = _AI["src_hits"].get(url,0)+hits
        else:      _AI["src_fails"][url] = _AI["src_fails"].get(url,0)+1

def ai_stat(key:str):
    with _ai_lock:
        fs = _AI.setdefault("filter_stats",dict(_AI_SCHEMA["filter_stats"]))
        fs[key] = fs.get(key,0)+1

def ai_record_win(ping:int, probe:int, is_cf:bool):
    with _ai_lock:
        _AI["total_passed"] = _AI.get("total_passed",0)+1
        n = max(_AI["total_passed"],1)
        _AI["avg_ping"]   = (_AI.get("avg_ping",0)*(n-1)+ping)/n
        _AI["avg_probe"]  = (_AI.get("avg_probe",0)*(n-1)+probe)/n
        _AI["cf_ratio"]   = (_AI.get("cf_ratio",0.5)*(n-1)+(1 if is_cf else 0))/n

def ai_order() -> list:
    with _ai_lock:
        w=dict(_AI.get("bug_wins",{})); f=dict(_AI.get("bug_fails",{}))
    def sc(h):
        ww=w.get(h,0); ff=f.get(h,0); t=ww+ff
        return ww/t if t else 0.5
    return sorted(ALL_BUG_HOSTS, key=sc, reverse=True)

def ai_best_paths() -> list:
    with _ai_lock:
        pw = dict(_AI.get("path_wins",{}))
    base = ["/ws","/linkvws","/vws","/link","/v2ray","/"]
    if not pw: return base
    top = sorted(pw.items(),key=lambda x:-x[1])
    ordered = [p for p,_ in top]
    for p in base:
        if p not in ordered: ordered.append(p)
    return ordered[:6]

def ai_dead_sources() -> set:
    with _ai_lock:
        hits=_AI.get("src_hits",{}); fails=_AI.get("src_fails",{})
    dead=set()
    for url,ff in fails.items():
        hh=hits.get(url,0)
        if hh+ff>=10 and hh==0: dead.add(url)
    return dead

def ai_rank_sources(srcs:list) -> list:
    dead=ai_dead_sources()
    live=[u for u in srcs if u not in dead]
    with _ai_lock: h=dict(_AI.get("src_hits",{}))
    return sorted(live,key=lambda u:h.get(u,-1),reverse=True)

def ai_mode() -> dict:
    """AI يحدد وضعه بناءً على الأداء — Aggressive / Balanced / Strict"""
    with _ai_lock:
        runs    = _AI.get("runs",0)
        checked = max(_AI.get("total_checked",1),1)
        passed  = _AI.get("total_passed",0)
    rate = passed/checked
    if runs < 5 or rate < 0.002:
        return {"name":"AGGRESSIVE","max_ping":800,"max_probe":3000,"min_compat":1}
    elif rate < 0.05:
        return {"name":"BALANCED","max_ping":700,"max_probe":3000,"min_compat":1}
    else:
        return {"name":"STRICT","max_ping":600,"max_probe":2500,"min_compat":1}

def ai_diagnose() -> str:
    with _ai_lock:
        fs=dict(_AI.get("filter_stats",{}))
        runs=_AI.get("runs",0); passed=_AI.get("total_passed",0)
        checked=_AI.get("total_checked",1)
    t=max(fs.get("total",1),1)
    mode=ai_mode()["name"]
    return (
        f"🤖 v10|{mode}|Run#{runs}|"
        f"Pass:{fs.get('passed',0)/t*100:.1f}%|"
        f"Struct:{fs.get('struct',0)/t*100:.1f}%|"
        f"TCP:{fs.get('tcp',0)/t*100:.1f}%|"
        f"Probe:{fs.get('probe',0)/t*100:.1f}%|"
        f"Total:{passed}/{checked}"
    )

def ai_report() -> str:
    with _ai_lock:
        w=sum(_AI.get("bug_wins",{}).values())
        t=w+sum(_AI.get("bug_fails",{}).values())
        runs=_AI.get("runs",0)
        top=sorted(_AI.get("host_wins",{}).items(),key=lambda x:-x[1])[:2]
        disc=len(_AI.get("discovered_sources",[]))
    rate=w/t*100 if t else 0
    tops=",".join(h.split(".")[1]+f"({n})" for h,n in top) or "—"
    return f"AI#{runs} {w}/{t}({rate:.0f}%) top:{tops} disc:{disc}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SELF-EVOLUTION ENGINE — يكتشف مصادر جديدة تلقائياً
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# كلمات مفتاحية تدل على مصادر v2ray
_V2_KEYWORDS = [
    "vless","vmess","v2ray","xray","v2rayng","v2rayn",
    "proxy","vpn","config","sub","subscription","clash",
    "free","node","server","cf","cloudflare","ws","tls",
    "shadowsocks","trojan","outlineVPN","outline",
]

_GITHUB_SEARCH_URLS = [
    "https://api.github.com/search/repositories?q=vless+vmess+free&sort=updated&per_page=30",
    "https://api.github.com/search/repositories?q=v2ray+configs+free&sort=updated&per_page=30",
    "https://api.github.com/search/repositories?q=vmess+vless+443+ws&sort=updated&per_page=30",
    "https://api.github.com/search/repositories?q=free+proxy+v2ray+sub&sort=stars&per_page=30",
]

_TG_SEARCH_CHANNELS = [
    "https://t.me/s/v2ray_configs",
    "https://t.me/s/proxy_mtproto",
    "https://t.me/s/v2ray1_ng",
    "https://t.me/s/VlessConfig",
    "https://t.me/s/ConfigsHUB",
    "https://t.me/s/PrivateVPNs",
]

def evolve_discover_sources(existing_urls: set) -> list:
    """
    🦠 VIRUS MODE — يكتشف مصادر جديدة تلقائياً من:
    1. GitHub API — أحدث repos
    2. Telegram channels — links في المحتوى
    3. مصادر مكتشفة سابقاً — يتبع links
    """
    new_sources = []
    headers = {
        "User-Agent":"Mozilla/5.0 (compatible; V2RayBot/1.0)",
        "Accept":"application/json,text/html",
    }

    # ── 1. GitHub API Discovery ────────────────────────────────────────────
    for url in _GITHUB_SEARCH_URLS[:2]:  # أول 2 فقط لتوفير الوقت
        if not deadline_ok(): break
        try:
            r = requests.get(url, headers=headers, timeout=4, verify=False)
            if not r.ok: continue
            data = r.json()
            for repo in data.get("items",[]):
                raw_base = f"https://raw.githubusercontent.com/{repo['full_name']}/{repo.get('default_branch','main')}"
                # جرّب ملفات شائعة
                for fname in ["sub.txt","v2ray.txt","all.txt","configs.txt","nodes.txt",
                               "vmess.txt","vless.txt","mix.txt","sub"]:
                    candidate = f"{raw_base}/{fname}"
                    if candidate not in existing_urls:
                        new_sources.append(candidate)
                # أيضاً README قد يحتوي links
        except Exception: pass

    # ── 2. Telegram Channel Scraping for Links ─────────────────────────────
    url_re = re.compile(r'https?://(?:raw\.githubusercontent\.com|t\.me/s/)[^\s\'"<>]+')
    for tg_url in _TG_SEARCH_CHANNELS[:3]:
        if not deadline_ok(): break
        try:
            r = requests.get(tg_url, headers=headers, timeout=8, verify=False)
            if not r.ok: continue
            text = r.text
            # استخرج links
            found = url_re.findall(text)
            for link in found:
                if link not in existing_urls and any(k in link.lower() for k in _V2_KEYWORDS):
                    new_sources.append(link)
        except Exception: pass

    # ── 3. Follow discovered sources for more links ────────────────────────
    with _ai_lock:
        prev_disc = list(_AI.get("discovered_sources",[]))[-20:]
    for prev_url in prev_disc[:5]:
        if not deadline_ok(): break
        try:
            r = requests.get(prev_url, headers=headers, timeout=6, verify=False)
            if not r.ok: continue
            found = url_re.findall(r.text)
            for link in found:
                if link not in existing_urls:
                    new_sources.append(link)
        except Exception: pass

    # Dedup
    seen = set(existing_urls)
    unique_new = []
    for s in new_sources:
        if s not in seen:
            seen.add(s)
            unique_new.append(s)

    if unique_new:
        with _ai_lock:
            disc = _AI.setdefault("discovered_sources",[])
            disc.extend(unique_new)
            _AI.setdefault("evolution_log",[]).append({
                "ts": datetime.now(timezone.utc).isoformat()[:16],
                "new": len(unique_new),
            })
        log.info(f"🦠 Evolution: +{len(unique_new)} new sources discovered!")

    return unique_new

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WORKING CACHE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_CACHE_FILE = "working_cache.json"
_CACHE_VER  = "v10-aggressive"
_CACHE_TTL  = 3*3600

def cache_load() -> list:
    try:
        data=json.loads(open(_CACHE_FILE,encoding="utf-8").read())
        if data and data[0].get("ver") != _CACHE_VER:
            log.info("♻️  Cache version mismatch — discarding")
            return []
        fresh=[c for c in data if time.time()-c.get("ts",0)<_CACHE_TTL]
        log.info(f"♻️  Cache: {len(fresh)}/{len(data)}")
        return fresh
    except Exception: return []

def cache_save(cfgs:list):
    try:
        data=[{
            "ver":_CACHE_VER,"raw":c.raw,"raw_p":c.raw_patched,
            "host":c.host,"port":c.port,"proto":c.proto,
            "ping":c.ping_ms,"probe":c.probe_ms,
            "compat":c.compatible_hosts,"best":c.best_bug_host,
            "cc":c.country_code,"country":c.country,"isp":c.isp,
            "is_cf":c.is_cf,"is_vps":c.is_vps,
            "diag":c.ai_diagnosis,"ssl":c.ssl_ok,"ts":time.time(),
        } for c in cfgs[:200]]
        open(_CACHE_FILE,"w",encoding="utf-8").write(
            json.dumps(data,ensure_ascii=False,separators=(",",":")))
        log.info(f"💾 Cache: {len(data)} saved")
    except Exception as e: log.warning(f"Cache: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CF DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_CF_NETS = [ipaddress.ip_network(c) for c in [
    "103.21.244.0/22","103.22.200.0/22","103.31.4.0/22",
    "104.16.0.0/13","104.24.0.0/14","108.162.192.0/18",
    "131.0.72.0/22","141.101.64.0/18","162.158.0.0/15",
    "172.64.0.0/13","173.245.48.0/20","188.114.96.0/20",
    "190.93.240.0/20","197.234.240.0/22","198.41.128.0/17",
]]
# CF IPs + CF domain patterns (Workers, Pages, R2, etc.)
CF_KW  = (
    # CF IPs
    "cloudflare","104.16.","104.17.","104.18.","104.19.","104.20.",
    "104.21.","172.64.","172.65.","172.66.","172.67.","1.1.1.","1.0.0.",
    # CF domain patterns — Cloudflare Workers/Pages/R2
    ".workers.dev",".pages.dev",".r2.dev",".cf-ipfs.com",
    # CF random subdomain patterns (e.g. broad-sky-9360.k7uztejf...)
    # تعرف على الـ pattern: word-word-digits.randomhash
    # نتحقق بـ regex في is_cf_domain()
)

# CF domain regex patterns
import re as _re
_CF_DOMAIN_PATTERNS = (
    ".workers.dev", ".pages.dev", ".r2.dev",
    ".cf-ipfs.com", ".cloudflare.net", ".cloudflare.com",
)

def is_cf_domain(host: str) -> bool:
    """يكتشف CF Workers/Pages/proxy بالـ domain."""
    hl = host.lower()
    # CF IP keywords
    if any(k in hl for k in CF_KW): return True
    # CF domain suffixes
    if any(hl.endswith(p) or p in hl for p in _CF_DOMAIN_PATTERNS): return True
    # CF Workers random pattern: word-word-1234.randomhash8
    # e.g. broad-sky-9360.k7uztejf2draa3r7.workers.dev
    parts = hl.split(".")
    if len(parts) >= 2:
        # pattern: contains digits after hyphens = CF Worker subdomain
        first = parts[0]
        segs  = first.split("-")
        if len(segs) >= 2 and segs[-1].isdigit():
            return True
    return False
VPS_KW = ("vps","server","host","vir","linode","digital","vultr","aws",
           "azure","hetz","oracle","ovh","gcp","google","upcloud")

def is_cf_ip(ip:str) -> bool:
    try:
        a=ipaddress.ip_address(ip)
        return any(a in n for n in _CF_NETS)
    except Exception: return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HTTP SESSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]
_sess_local = threading.local()
def _hdr()->dict: return {"User-Agent":random.choice(_UAS),"Accept":"*/*","Connection":"keep-alive"}
def _sess()->requests.Session:
    s=getattr(_sess_local,"s",None)
    if s is None: s=requests.Session(); s.verify=False; _sess_local.s=s
    return s

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dataclass
class V2Config:
    raw:str; raw_patched:str; host:str; port:int
    ping_ms:int; proto:str; original_sni:str; injected_sni:str
    ssl_ok:bool=False; ssl_cert_cn:str=""
    country_code:str="??"; country:str="Unknown"; isp:str=""
    is_vps:bool=False; is_cf:bool=False
    compatible_hosts:list=field(default_factory=list)
    best_bug_host:str=""; probe_ms:int=0
    ai_diagnosis:str=""; server_type:str=""

    def score(self)->int:
        s=800 if self.is_cf else 0
        s+=500 if self.is_vps else 0
        s+=300 if self.ssl_ok else 0
        compat=set(self.compatible_hosts)
        s+=len(compat&set(TARGET_HOSTS["oodi"]))*900
        s+=len(compat&set(TARGET_HOSTS["zain"]))*800
        if len(compat)>=len(ALL_BUG_HOSTS): s+=3000
        if   self.probe_ms<150: s+=1200
        elif self.probe_ms<300: s+=900
        elif self.probe_ms<600: s+=500
        if   self.ping_ms<80:   s+=1000
        elif self.ping_ms<150:  s+=700
        elif self.ping_ms<300:  s+=400
        return s

_CONFIG_RE = re.compile(r"(?:vless|vmess)://[^\s#\"'<>\]\[]+")


SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity_base64.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_base64_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub6.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub7.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub8.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/en/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/fa/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/splitted/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/splitted/vmess",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Temp/TG-CF",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Temp/TG",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/meta",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/all-in-one",
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/actives.txt",
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vless",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vmess",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/mix",
    "https://raw.githubusercontent.com/Surfboardv2ray/Proxy-sorter/main/submerge/output.txt",
    "https://raw.githubusercontent.com/itsyebekhe/HiN-VPN/main/subscription/normal/mix",
    "https://raw.githubusercontent.com/itsyebekhe/HiN-VPN/main/subscription/base64/mix",
    "https://raw.githubusercontent.com/itsyebekhe/PSG/main/CONFIGS/Normal/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vmess",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vmess",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vless",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vmess",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all3",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/mix4",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/all",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/vmess",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/vless",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/tls",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_raw.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/all_configs.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/vless_configs.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/vmess_configs.txt",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt",
    "https://raw.githubusercontent.com/ErfanNamira/FreeLink/main/Links.txt",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/best.txt",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/sub.txt",
    "https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/V2Ray",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/merged.txt",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2",
    "https://raw.githubusercontent.com/hkaa0/permalink/main/proxy/V2ray",
    "https://raw.githubusercontent.com/vveg26/get_proxy/main/substrings/v2ray.txt",
    "https://raw.githubusercontent.com/HuiYuAI/XMRig/main/v2.txt",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes/all",
    "https://raw.githubusercontent.com/EACOJ/free/master/VMess-VLESS",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vless_iran.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/vmess_iran.txt",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription1",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription2",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription3",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription4",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription5",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription6",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription7",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription8",
    "https://raw.githubusercontent.com/Incognito-Coder/SimpleSub/main/Xray/Normal/all",
    "https://raw.githubusercontent.com/Incognito-Coder/SimpleSub/main/Xray/Base64/all",
    "https://raw.githubusercontent.com/VerveProxy/SubVerve/main/Normal/sub1.txt",
    "https://raw.githubusercontent.com/VerveProxy/SubVerve/main/Normal/sub2.txt",
    "https://raw.githubusercontent.com/VerveProxy/SubVerve/main/Normal/sub3.txt",
    "https://raw.githubusercontent.com/4n0nymou3/ss-config-updater/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/IranianCypherpunks/sub/main/config",
    "https://raw.githubusercontent.com/Jia-Pingwa/free-v2ray-merge/main/output/v2ray",
    "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/combine/v2raySub.txt",
    "https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/All.txt",
    "https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/Vmess.txt",
    "https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/Vless.txt",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/aiboboxx/clashfree/main/clash.yml",
    "https://raw.githubusercontent.com/vveg26/chromego_merge/main/sub/clashProxies.yaml",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash-meta.yaml",
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/v2ray/v2raysub",
    "https://raw.githubusercontent.com/khaled-alselwady/free-proxy-and-vpn/main/V2ray/v2ray.txt",
    "https://raw.githubusercontent.com/Fukki-Z/nodefree/main/update",
    "https://raw.githubusercontent.com/vpnhat/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/parhamb7/parhamb7/main/sub",
    "https://raw.githubusercontent.com/HuiYuAI/XMRig/main/v3.txt",
    "https://raw.githubusercontent.com/Airscker/DeadPool/main/abbb.md",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity_base64.txt",
    "https://t.me/s/iP_CF",
    "https://t.me/s/CFproxyServer",
    "https://t.me/s/ConfigsHUB",
    "https://t.me/s/V2pedia",
    "https://t.me/s/VlessConfig",
    "https://t.me/s/v2ray_configs_pool",
    "https://t.me/s/free4allVPN",
    "https://t.me/s/FreeVlessVpn",
    "https://t.me/s/FreakConfig",
    "https://t.me/s/ArV2ray",
    "https://t.me/s/MsV2ray",
    "https://t.me/s/PrivateVPNs",
    "https://t.me/s/freev2rayssr",
    "https://t.me/s/fast_v2ray",
    "https://t.me/s/DirectVPN",
    "https://t.me/s/vmess_vless_v2rayng",
    "https://t.me/s/V2RayTz",
    "https://t.me/s/vless_vmess",
    "https://t.me/s/vmess_free1",
    "https://t.me/s/NIM_VPN_ir",
    "https://t.me/s/v2_vmess",
    "https://t.me/s/proxystore11",
    "https://t.me/s/shadowsocks_v2rayng",
    "https://t.me/s/v2ray_swhil",
    "https://t.me/s/comv2ray",
    "https://t.me/s/Lockey_VPN",
    "https://t.me/s/SafeNet_Server",
    "https://t.me/s/SSV2ray",
    "https://t.me/s/v2ray_configs",
    "https://t.me/s/ElitePVPN",
    "https://t.me/s/VPN_Master_ir1",
    "https://t.me/s/oneclickvpnkeys",
    "https://t.me/s/v2line",
    "https://t.me/s/Free_V2rayyy",
    "https://t.me/s/V2RayNGConfig",
    "https://t.me/s/proxies_r",
    "https://t.me/s/XskyGroup",
    "https://t.me/s/v2ray1_ng",
    "https://t.me/s/vpn_xv",
    "https://t.me/s/hiddify_free",
    "https://t.me/s/ShadowProxy66",
    "https://t.me/s/UnlimitedDev",
    "https://t.me/s/Outline_Vpn",
    "https://t.me/s/link_proxy",
    "https://t.me/s/Configforvpn01",
    "https://t.me/s/NetAccount_ir",
    "https://t.me/s/v2ray_ng_iran",
    "https://t.me/s/free_v2ray_servers",
    "https://t.me/s/V2Ray_FreedomIran",
    "https://t.me/s/ip_cf_clean",
    "https://t.me/s/vmess_vless",
    "https://t.me/s/v2rayng_v",
    "https://t.me/s/v2ray_alpha",
    "https://t.me/s/flyv2ray",
    "https://t.me/s/proxy_kafee",
]




# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STRUCTURE VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# قبول أي path يبدأ بـ / — نترك الـ probe يقرر
_PATH_RE = re.compile(r"^/[^\s]*$")

def _vmess_obj(raw:str) -> Optional[dict]:
    try:
        b64=raw[8:]
        for pad in ("","=","==","==="):
            try: return json.loads(base64.b64decode(b64+pad).decode("utf-8",errors="ignore"))
            except Exception: continue
    except Exception: pass
    return None

def is_valid_struct(raw:str) -> bool:
    """يقبل VMESS/VLESS + WS + TLS + 443"""
    if raw.startswith("vmess://"):
        obj=_vmess_obj(raw)
        if not obj: return False
        if str(obj.get("port","")) != "443":            return False
        if obj.get("net","") not in ("ws","websocket"): return False
        if obj.get("tls","") not in ("tls","xtls"):     return False
        if str(obj.get("aid","0")) not in ("0",""):      return False
        path=obj.get("path","")
        if path and not _PATH_RE.match(path):           return False
        return True
    else:
        rl=raw.lower()
        if "type=ws" not in rl and "net=ws" not in rl:   return False
        if ":443" not in raw:                              return False
        if "security=tls" not in rl and "tls" not in rl: return False
        m=re.search(r"[?&]path=([^&\s#]+)",raw,re.I)
        if m:
            p=m.group(1).replace("%2F","/").replace("%2f","/")
            if p and not _PATH_RE.match(p): return False
        return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROVIDER LOCK DETECTION
#  نرفض فقط السيرفرات المقفولة لموفر — أي SNI آخر مقبول (probe يستبدله)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Provider ISP domains - hard-reject
_LOCKED = (
    "zain.com","oodi.com","mobily.com","stc.com","ooredoo.",
    "etisalat.","du.ae","vodafone.sa","tedata.","batelco.",
    "omantel.","nawras.","wimax.","wana.",
)
# IPs regex
_IP4_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
# Bug Hosts set
_BUG_SET = {b.lower() for b in ALL_BUG_HOSTS}

def extract_sni(raw:str) -> str:
    keys=("sni","host","peer","servername","server-name")
    if raw.startswith("vmess://"):
        obj=_vmess_obj(raw)
        if obj:
            for k in keys:
                if obj.get(k): return str(obj[k])
        return ""
    for k in keys:
        m=re.search(rf"[?&]{k}=([^&\s#]+)",raw,re.I)
        if m and m.group(1): return m.group(1)
    return ""

def is_provider_locked(raw:str) -> bool:
    """
    Blacklist ذكية — نرفض فقط:
    1. موفرون ISP معروفون (zain.com, oodi.com, etc.)
    2. مواقع عامة واضحة ليست proxy (google.com, youtube.com, etc.)
    3. نقبل كل شيء آخر → الـ probe يقرر

    السبب: الـ Whitelist رفضت 61.5% من الكونفيجات الصحيحة
    """
    sni = extract_sni(raw).lower().strip()
    if not sni: return False  # فارغ = مقبول دائماً

    # موفرو الإنترنت المحليون — لا يمكن تجاوزهم
    if any(p in sni for p in _LOCKED): return True

    # مواقع عامة واضحة — ليست v2ray proxy
    # مواقع عامة — ليست proxy (باستثناء Bug Hosts)
    _OBVIOUS_NOT_PROXY = (
        "google.com","youtube.com","amazon.com","microsoft.com",
        "apple.com","openai.com","github.com","netflix.com",
        "speedtest.net","ookla.com","fast.com","wikipedia.org",
        "reddit.com","twitter.com","x.com","linkedin.com",
    )
    # تحقق مع استثناء Bug Hosts
    if sni not in _BUG_SET:
        if any(sni == d or sni.endswith("."+d) for d in _OBVIOUS_NOT_PROXY):
            return True

    return False  # كل شيء آخر → probe يقرر

def extract_path(raw:str) -> str:
    if raw.startswith("vmess://"):
        obj=_vmess_obj(raw)
        if obj:
            p=obj.get("path","")
            return p if p else "/ws"
        return "/ws"
    m=re.search(r"[?&]path=([^&\s#]+)",raw,re.I)
    if m:
        p=m.group(1).replace("%2F","/").replace("%2f","/")
        return p if p.startswith("/") else "/"+p
    return "/ws"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PATCH ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _sp(url:str,key:str,val:str)->str:
    pat=re.compile(rf"([?&]{re.escape(key)}=)[^&\s#]*",re.I)
    if pat.search(url): return pat.sub(lambda m:m.group(1)+val,url)
    sep="&" if "?" in url else "?"; return url+f"{sep}{key}={val}"

def _dp(url:str,key:str)->str:
    url=re.sub(rf"[?&]{re.escape(key)}=[^&\s#]*","",url,flags=re.I)
    url=re.sub(r"\?&","?",url); return re.sub(r"[?&]$","",url)

def patch_final(raw:str, server_is_cf:bool=False) -> str:
    """
    الكونفيج النهائي — يتصرف بناءً على نوع السيرفر:

    CF Server:  host="" sni="" فارغ → المستخدم يحط Bug Host
    VPS Server: host=domain sni=domain → لا تغيير (VPS يتحقق من SNI يطابق شهادته)

    السبب: VPS مثل v2ray.codefyinc.com شهادة TLS = domain السيرفر
    إذا حططنا Bug Host كـ SNI → TLS handshake يفشل → Downlink=0B
    """
    orig_path = extract_path(raw)
    orig_sni  = extract_sni(raw)
    m_host    = re.search(r"@([^:/\s\]#]+):", raw)
    server_domain = m_host.group(1) if m_host else ""

    # للـ VPS: دائماً استخدم server_domain (ليس orig_sni الذي قد يكون Bug Host قديم)
    _BH_SET = {bh.lower() for bh in ALL_BUG_HOSTS}
    def _vps_sni():
        # إذا orig_sni = Bug Host → استخدم server_domain
        if orig_sni and orig_sni.lower() not in _BH_SET:
            return orig_sni  # SNI مخصص من صاحب السيرفر
        return server_domain  # domain السيرفر نفسه

    if raw.startswith("vmess://"):
        try:
            obj = _vmess_obj(raw)
            if not obj: return raw
            if server_is_cf:
                obj["sni"] = ""; obj["host"] = ""
                for k in ("peer","servername","server-name"): obj.pop(k,None)
            else:
                vsni = _vps_sni()
                obj["sni"]  = vsni
                obj["host"] = vsni
            obj["net"]  = "ws"; obj["path"] = orig_path; obj["tls"] = "tls"
            obj["allowInsecure"] = True; obj["skip-cert-verify"] = True
            return "vmess://" + base64.b64encode(
                json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode()).decode()
        except Exception: return raw
    else:
        r = raw
        if server_is_cf:
            for k in ("sni","host"): r = _sp(r, k, "")
            for k in ("peer","servername","server-name"): r = _dp(r, k)
        else:
            vsni = _vps_sni()
            if vsni:
                for k in ("sni","host"): r = _sp(r, k, vsni)
        r = _sp(r,"type","ws"); r = _sp(r,"security","tls")
        r = _sp(r,"allowInsecure","1")
        return r

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROBE ENGINE — الأكثر عدوانية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def tcp_ping(host:str,port:int)->Optional[int]:
    try:
        t0=time.perf_counter()
        with socket.create_connection((host,port),timeout=TCP_TIMEOUT): pass
        return int((time.perf_counter()-t0)*1000)
    except Exception: return None

def _ssl_ctx()->ssl.SSLContext:
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    return ctx

def ssl_check(host:str,port:int)->tuple:
    try:
        ctx=_ssl_ctx()
        conn=socket.create_connection((host,port),timeout=SSL_TIMEOUT)
        conn.settimeout(SSL_TIMEOUT)
        s=ctx.wrap_socket(conn,server_hostname=host)
        cert=s.getpeercert(); s.close()
        cn=""
        if cert:
            for f in cert.get("subject",()):
                for k,v in f:
                    if k=="commonName": cn=v; break
        return True,cn
    except Exception: return False,""

def ws_probe(host:str, port:int, bug_host:str, path:str="/ws") -> Optional[int]:
    """
    STRICT PROBE — يضمن Downlink ≠ 0B

    القاعدة الوحيدة التي تضمن الشغل:
    ✅ 101 Switching Protocols = WebSocket قائم = UUID مسجل = Downlink OK
       CF لا يرد 101 إلا إذا Worker نشط وراءه

    ✅ 200 + Upgrade:websocket (VPS فقط، ليس CF)
       VPS يرد 200 مع WS headers = يقبل WebSocket

    ❌ 400 + CF-Ray = CF حي لكن UUID غير مسجل = Downlink=0B
    ❌ HTTPS GET = كل CF يرده = false positive
    ❌ أي status آخر
    """
    if not deadline_ok(): return None
    ctx = _ssl_ctx()
    ai_paths = ai_best_paths()
    if path not in ai_paths: ai_paths.insert(0, path)

    for try_path in ai_paths[:5]:
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
                f"User-Agent: Go-http-client/2.0\r\n\r\n"
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
            elapsed = int((time.perf_counter()-t0)*1000)
            try: sock.close()
            except Exception: pass
            if not resp: continue

            first  = resp.split(b"\r\n")[0].decode(errors="ignore").strip()
            if not first.startswith("HTTP"): continue
            parts  = first.split()
            status = int(parts[1]) if len(parts)>=2 and parts[1].isdigit() else 0
            rl     = resp.lower()
            is_cf  = b"cf-ray:" in rl or b"server: cloudflare" in rl
            has_ws_upgrade = (b"upgrade: websocket" in rl or
                              b"sec-websocket-accept" in rl)

            # ✅ 101 = WebSocket ناجح = UUID مسجل = يعمل 100%
            if status == 101:
                ai_bug_update(bug_host, True); ai_path_win(try_path)
                log.debug(f"  ✅101 {host}←{bug_host}{try_path} {elapsed}ms")
                return elapsed

            # ✅ VPS: 200 مع WS headers = يقبل WebSocket
            if status == 200 and has_ws_upgrade and not is_cf:
                ai_bug_update(bug_host, True); ai_path_win(try_path)
                log.debug(f"  ✅200+WS(VPS) {host}←{bug_host} {elapsed}ms")
                return elapsed

            # ❌ كل شيء آخر مرفوض
            # 400+CF = CF حي لكن UUID ميت = Downlink=0B
            # 530 = CF error = SNI خاطئ
            # 403/404/5xx = ميت
            log.debug(f"  ❌{status} cf={is_cf} {host}←{bug_host}{try_path}")

        except Exception as e:
            log.debug(f"  ❌{type(e).__name__} {host}←{bug_host}")

    ai_bug_update(bug_host, False)
    return None


def multi_probe(host:str, port:int, raw:str="", server_sni:str="") -> tuple:
    """
    يفحص كل Bug Host بالتوازي.
    للـ VPS: يُضيف أيضاً domain السيرفر نفسه كـ SNI اختبار أولي.
    إذا VPS يعمل بـ domain السيرفر → يُضاف كـ compat host مميز.
    """
    if not deadline_ok(): return [],"",-1
    ordered   = ai_order()
    cfg_path  = extract_path(raw) if raw else "/ws"

    # للـ VPS: ابدأ بفحص domain السيرفر نفسه
    # هذا يكتشف إذا السيرفر VPS حقيقي يعمل بـ SNI الخاص به
    vps_check_sni = server_sni or host  # domain السيرفر
    timings: dict = {}

    # أولاً: فحص domain السيرفر (سريع — يكشف VPS vs CF)
    if vps_check_sni and vps_check_sni not in ordered:
        ms_vps = ws_probe(host, port, vps_check_sni, path=cfg_path)
        if ms_vps is not None:
            timings[vps_check_sni] = ms_vps
            # VPS يعمل بـ domain الخاص — لا نحتاج Bug Hosts
            # أضف كـ best وأرجع فوراً
            with _ai_lock:
                hw = _AI.setdefault("host_wins",{})
                hw[vps_check_sni] = hw.get(vps_check_sni,0)+1
            return [vps_check_sni], vps_check_sni, ms_vps

    # Bug Host probe (للـ CF IPs)
    def _pbh(bh:str)->Optional[int]:
        return ws_probe(host, port, bh, path=cfg_path)

    with ThreadPoolExecutor(max_workers=min(len(ordered),12)) as ex:
        futs={ex.submit(_pbh,bh):bh for bh in ordered}
        for fut in as_completed(futs):
            bh=futs[fut]
            try:
                ms=fut.result()
                if ms is not None: timings[bh]=ms
            except Exception: pass

    if not timings: return [],"",-1
    compat = list(timings)
    best   = min(timings, key=timings.get)
    with _ai_lock:
        hw = _AI.setdefault("host_wins",{})
        hw[best] = hw.get(best,0)+1
    return compat, best, timings[best]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHECK_RAW — الفحص الكامل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_raw(raw:str)->Optional[V2Config]:
    if not deadline_ok(): return None
    if ai_seen(raw):       return None

    ai_stat("total")
    with _ai_lock: _AI["total_checked"]=_AI.get("total_checked",0)+1

    m=re.search(r"@([^:/\s\]#]+):(\d+)",raw)
    if not m: return None
    host=m.group(1)
    try: port=int(m.group(2))
    except ValueError: return None
    if port!=TARGET_PORT: return None

    if not is_valid_struct(raw):
        ai_stat("struct")
        log.debug(f"  ⛔struct {raw[:60]}")
        return None
    if is_provider_locked(raw):
        ai_stat("locked"); return None

    proto="VLESS" if raw.startswith("vless://") else "VMESS"
    orig_sni=extract_sni(raw)

    # 1. TCP
    ping=tcp_ping(host,port)
    mode=ai_mode()
    if ping is None or ping>mode["max_ping"]:
        ai_stat("tcp"); return None

    # 2. SSL
    ssl_ok,ssl_cn=ssl_check(host,port)

    # 3. CF/VPS
    try:    ip=socket.gethostbyname(host)
    except Exception: ip=""
    if ip and ai_is_bad_ip(ip): return None
    is_cf  = (is_cf_ip(ip) if ip else False) or is_cf_domain(host)
    is_vps = any(k in (host+raw).lower() for k in VPS_KW)

    # 4. Probe
    if CUSTOM_SNI:
        ms=ws_probe(host,port,CUSTOM_SNI)
        if ms is None: ai_stat("probe"); return None
        compat,best,probe_ms=[CUSTOM_SNI],CUSTOM_SNI,ms
    else:
        # مرّر domain السيرفر لفحص VPS أولاً
        compat,best,probe_ms=multi_probe(host,port,raw, server_sni=host)
        if len(compat) < mode["min_compat"]:
            ai_stat("probe")
            if ip: ai_bad_ip(ip)
            return None   # probe فشل = لا ننشر
        if probe_ms > mode["max_probe"]: return None

    # 5. Patch — CF يفرّغ SNI، VPS يحتفظ بـ domain
    raw_p=patch_final(raw, server_is_cf=is_cf)
    if ip: ai_good_ip(ip)
    ai_stat("passed")
    ai_record_win(ping,probe_ms,is_cf)

    nc=len(compat); nt=len(ALL_BUG_HOSTS)
    ops=[]
    if set(compat)&set(TARGET_HOSTS["oodi"]): ops.append("Oodi")
    if set(compat)&set(TARGET_HOSTS["zain"]): ops.append("Zain")
    q="🏆" if nc>=8 else "⭐⭐⭐" if nc>=4 else "⭐⭐" if nc>=2 else "⭐"
    tp=("CF⚡" if is_cf else "")+(" VPS🚀" if is_vps else "")
    diag=f"✅{q}|{tp}|{nc}/{nt}|{ping}ms|{'+'.join(ops) or '?'}"

    log.info(f"✅ {host}|{proto}|{nc}/{nt}|{ping}ms→{best[:20]}")
    return V2Config(
        raw=raw,raw_patched=raw_p,host=host,port=port,ping_ms=ping,proto=proto,
        original_sni=orig_sni,injected_sni="",ssl_ok=ssl_ok,ssl_cert_cn=ssl_cn,
        is_cf=is_cf,is_vps=is_vps,compatible_hosts=compat,best_bug_host=best,
        probe_ms=probe_ms,ai_diagnosis=diag,server_type="CF" if is_cf else "VPS",
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FETCH ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _fetch(url:str)->list:
    if not deadline_ok(): return []
    try:
        time.sleep(random.uniform(0.01,0.1))
        h=_hdr()
        if "t.me/s/" in url: h["Referer"]="https://t.me/"
        r=_sess().get(url,timeout=FETCH_TIMEOUT,headers=h,allow_redirects=True,stream=False)
        if r.status_code==429:
            time.sleep(min(int(r.headers.get("Retry-After",5)),8))
            r=_sess().get(url,timeout=FETCH_TIMEOUT,headers=_hdr())
        if r.status_code not in (200,206): return []
        text=r.text
        found=_CONFIG_RE.findall(text)
        if not found:
            b=re.sub(r"\s+","",text)
            for pad in ("","=","=="):
                try:
                    dec=base64.b64decode(b+pad).decode("utf-8",errors="ignore")
                    found=_CONFIG_RE.findall(dec)
                    if found: break
                except Exception: continue
        if not found:
            for line in text.splitlines():
                line=line.strip()
                if len(line)>20 and not line.startswith(("vless://","vmess://")):
                    try:
                        dec=base64.b64decode(line+"==").decode("utf-8",errors="ignore")
                        found.extend(_CONFIG_RE.findall(dec))
                    except Exception: pass
        if not found and "t.me" in url:
            clean=re.sub(r"<[^>]+>"," ",text)
            clean=clean.replace("&amp;","&").replace("&#43;","+").replace("&#61;","=")
            found=_CONFIG_RE.findall(clean)
        out=list(dict.fromkeys(c for c in found if ":443" in c))
        if out: log.info(f"✓ {len(out):>4}  ←  {url[:65]}")
        return out
    except requests.exceptions.SSLError:
        try:
            r2=requests.get(url,timeout=FETCH_TIMEOUT,headers=_hdr(),verify=False)
            return list(dict.fromkeys(c for c in _CONFIG_RE.findall(r2.text) if ":443" in c))
        except Exception: return []
    except Exception: return []



def collect_configs(extra_sources:list=[])->list:
    """يجمع من كل المصادر + المكتشفة حديثاً"""
    dead=ai_dead_sources()
    all_sources=list(dict.fromkeys(SOURCES+extra_sources))
    active=[u for u in all_sources if u not in dead]
    ranked=ai_rank_sources(active)
    # 70% ranked (الأكثر إنتاجاً) + 30% random (للتنويع واكتشاف جديد)
    split=int(len(ranked)*0.70)
    rest=ranked[split:]; random.shuffle(rest)
    ordered=(ranked[:split]+rest)[:800]

    log.info(f"🌐 Fetching {len(ordered)}/{len(all_sources)} "
             f"[{FETCH_WORKERS}w | {len(dead)} dead | +{len(extra_sources)} new]")

    all_raw:list=[]
    src_hits:dict={}

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        fmap={ex.submit(_fetch,u):u for u in ordered}
        for fut in as_completed(fmap):
            if not deadline_ok(): break
            url=fmap[fut]
            try:
                results=fut.result()
                src_hits[url]=len(results)
                all_raw.extend(results)
            except Exception: src_hits[url]=0

    for url,cnt in src_hits.items():
        ai_src_update(url,cnt)

    unique=list(dict.fromkeys(all_raw))
    good=sum(1 for c in src_hits.values() if c>0)
    # لوق تفصيلي لمعرفة المشكلة
    ws_tls = [u for u in unique if ":443" in u and
              ("type=ws" in u.lower() or "net=ws" in u.lower() or '"net":"ws"' in u)]
    log.info(f"📦 {len(unique)} unique | {good}/{len(ordered)} active | ~{len(ws_tls)} WS+443")
    return unique


def run_checks(raws:list)->list:
    """فحص عدواني مع AI adaptive mode"""
    mode=ai_mode()
    log.info(f"🤖 Mode: {mode['name']} | ping<{mode['max_ping']}ms | probe<{mode['max_probe']}ms")

    # ترتيب: good IPs أولاً، ثم CF، ثم VPS
    with _ai_lock: good=set(_AI.get("good_ips",[]))
    def _sk(x):
        mm=re.search(r"@([^:/]+):",x)
        ip=mm.group(1) if mm else ""
        return (ip not in good,
                not any(k in x.lower() for k in CF_KW),
                not any(k in x.lower() for k in VPS_KW))
    raws=sorted(raws,key=_sk)[:MAX_CHECK_RAWS]

    log.info(f"⚡ Checking {len(raws)} [⏳{deadline_left()}s | stop@{STOP_AFTER} | {CHECK_WORKERS}w]")
    live:list=[]; stop=threading.Event(); lock=threading.Lock(); errs=[0]
    checked_count=[0]; last_log=[time.time()]

    def _w(raw:str)->Optional[V2Config]:
        if stop.is_set() or not deadline_ok(): return None
        try:
            result = check_raw(raw)
            with lock:
                checked_count[0] += 1
                # لوق كل 200 config مفحوص
                if checked_count[0] % 200 == 0:
                    t_now = time.time()
                    speed = 200 / max(t_now - last_log[0], 0.1)
                    last_log[0] = t_now
                    log.info(f"  🔍 {checked_count[0]} checked | {len(live)} live | "
                             f"{speed:.0f}/s | ⏳{deadline_left()}s | {ai_diagnose()[:60]}")
            return result
        except Exception:
            with lock: errs[0]+=1
            return None

    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as ex:
        futs={ex.submit(_w,r):r for r in raws}
        for fut in as_completed(futs):
            if not deadline_ok():
                stop.set()
                log.warning(f"⏰ Deadline — {len(live)} found")
                try: ex.shutdown(wait=False,cancel_futures=True)
                except Exception: pass
                break
            if stop.is_set():
                try: fut.cancel()
                except Exception: pass
                continue
            try: res=fut.result(timeout=35)
            except Exception: res=None
            if res:
                with lock:
                    live.append(res)
                    n=len(live)
                    if n%5==0:
                        log.info(f"  📊 {n} live | ⏳{deadline_left()}s | {ai_report()}")
                    if n>=STOP_AFTER:
                        stop.set()
                        log.info(f"🛑 Stop@{STOP_AFTER}")

    total_c = checked_count[0] if 'checked_count' in dir() else len(raws)
    log.info(
        f"✅ {len(live)} live | {total_c} checked | {errs[0]} errors\n"
        f"   {ai_diagnose()}"
    )
    return live


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GEO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_geo:dict={}; _gl=threading.Lock()

def get_geo(ip:str)->tuple:
    with _gl:
        if ip in _geo: return _geo[ip]
    for url in [
        f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp",
        f"https://ipapi.co/{ip}/json/",
    ]:
        try:
            rj=_sess().get(url,timeout=3,headers=_hdr()).json()
            if rj.get("status")=="success" or rj.get("country_code"):
                cc=rj.get("countryCode") or rj.get("country_code","??")
                co=rj.get("country","Unknown"); isp=rj.get("isp","")
                with _gl: _geo[ip]=(cc,co,isp)
                return cc,co,isp
        except Exception: pass
    return "??","Unknown",""

def enrich(cfg:V2Config)->V2Config:
    try:
        ip=socket.gethostbyname(cfg.host)
        cc,co,isp=get_geo(ip)
        cfg.country_code=cc; cfg.country=co; cfg.isp=isp
        cfg.is_cf=cfg.is_cf or is_cf_ip(ip)
        cfg.is_vps=cfg.is_vps or any(k in isp.lower() for k in ("vps","cloud","server","data","host"))
    except Exception: pass
    return cfg

def cache_to_configs(data:list)->list:
    result=[]
    for c in data:
        try:
            result.append(V2Config(
                raw=c["raw"],raw_patched=c["raw_p"],
                host=c["host"],port=c["port"],proto=c["proto"],
                ping_ms=c["ping"],probe_ms=c.get("probe",0),
                original_sni="",injected_sni="",
                ssl_ok=c.get("ssl",False),ssl_cert_cn="",
                is_cf=c.get("is_cf",False),is_vps=c.get("is_vps",False),
                compatible_hosts=c.get("compat",[]),best_bug_host=c.get("best",""),
                country_code=c.get("cc","??"),country=c.get("country","Unknown"),
                isp=c.get("isp",""),ai_diagnosis=c.get("diag","♻️"),
                server_type="CF" if c.get("is_cf") else "VPS",
            ))
        except Exception: pass
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MESSAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_FLAGS={"US":"🇺🇸","DE":"🇩🇪","NL":"🇳🇱","FR":"🇫🇷","GB":"🇬🇧","SG":"🇸🇬",
        "JP":"🇯🇵","HK":"🇭🇰","KR":"🇰🇷","CA":"🇨🇦","AU":"🇦🇺","IN":"🇮🇳",
        "TR":"🇹🇷","RU":"🇷🇺","SE":"🇸🇪","CH":"🇨🇭","FI":"🇫🇮","NO":"🇳🇴"}

def _tier(cfg:V2Config)->str:
    s=cfg.score()
    return "🏆 Elite" if s>8000 else "⭐⭐⭐" if s>5000 else "⭐⭐" if s>2000 else "⭐"

def _ops(cfg:V2Config)->str:
    compat=set(cfg.compatible_hosts)
    ops=[]
    if compat&set(TARGET_HOSTS["oodi"]): ops.append("📶 Oodi")
    if compat&set(TARGET_HOSTS["zain"]): ops.append("📶 Zain")
    return " | ".join(ops) or "❓"

def _ping_icon(ms:int)->str:
    return "🟢" if ms<150 else "🟡" if ms<350 else "🔴"

def build_message(cfg:V2Config)->str:
    nc=len(cfg.compatible_hosts); nt=len(ALL_BUG_HOSTS)
    flag=_FLAGS.get(cfg.country_code,"🌍")
    type_=("⚡CF" if cfg.is_cf else "")+(" 🚀VPS" if cfg.is_vps else "")
    hosts=" | ".join(f"<code>{h}</code>" for h in cfg.compatible_hosts[:4])
    if nc>4: hosts+=f" +{nc-4}"
    return (
        f"🤖 <b>Ashaq AI v10</b> — {_tier(cfg)}\n"
        f"──────────────────────\n"
        f"{flag} <b>{cfg.country}</b>  {type_}\n"
        f"{_ping_icon(cfg.ping_ms)} <b>{cfg.ping_ms}ms</b> • {cfg.proto} • {'🔒' if cfg.ssl_ok else '🔓'}\n"
        f"{_ops(cfg)}\n"
        f"──────────────────────\n"
        f"🎯 <b>Bug Hosts ({nc}/{nt}):</b>\n"
        f"{hosts}\n"
        f"──────────────────────\n"
        f"📝 أضف Bug Host في التطبيق\n"
        f"──────────────────────\n"
        f"<code>{cfg.raw_patched}</code>\n"
        f"──────────────────────\n"
        f"🕒 {datetime.now(timezone.utc).strftime('%H:%M UTC • %d/%m')}  |  @V2rayashaq"
    )

def send_tg(cfg:V2Config)->bool:
    """نشر مع retry قوي وتأكيد."""
    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN not set — cannot post to Telegram!")
        return False
    payload={
        "chat_id":CHAT_ID,"text":build_message(cfg),
        "parse_mode":"HTML","disable_web_page_preview":True,
        "reply_markup":{"inline_keyboard":[[
            {"text":"📢 Channel","url":"https://t.me/V2rayashaq"},
            {"text":"👤 Admin","url":f"https://t.me/{ADMIN_USER.lstrip('@')}"},
        ]]}
    }
    for attempt in range(5):   # 5 محاولات بدل 3
        try:
            res=requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json=payload, timeout=20)
            if res.status_code==429:
                w=res.json().get("parameters",{}).get("retry_after",30)
                log.warning(f"TG rate limit — waiting {w}s")
                time.sleep(min(w,60)); continue
            if res.ok:
                log.info(f"✅ TG sent OK: {cfg.host}")
                return True
            # خطأ من Telegram — اطبع التفاصيل
            log.warning(f"TG error {res.status_code}: {res.text[:200]}")
            if res.status_code == 400:
                # Bad Request — مشكلة في الرسالة، جرّب بدون HTML
                payload2 = dict(payload)
                payload2["parse_mode"] = ""
                payload2["text"] = "Config: " + cfg.host + "\n" + cfg.raw_patched[:300]

                payload2["text"] = "Config: " + cfg.host + " | " + cfg.raw_patched[:300]

                r2 = requests.post(
                    json=payload2, timeout=20)
                if r2.ok: return True
            return False
        except Exception as e:
            log.warning(f"TG attempt {attempt+1}/5: {type(e).__name__}: {e}")
            time.sleep(min(5*(attempt+1), 30))
    log.error("❌ All 5 TG attempts failed")
    return False

def save_sub(cfgs:list):
    top=cfgs[:MAX_SUB]
    blob="\n".join(c.raw_patched for c in top)
    try:
        open(SUB_FILE,"w",encoding="utf-8").write(
            base64.b64encode(blob.encode()).decode())
        log.info(f"💾 Sub: {len(top)} → {SUB_FILE}")
    except Exception as e: log.error(f"Sub: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main()->None:
    global _deadline, CUSTOM_SNI

    # ── Hard Deadline — يُضبط هنا فقط ────────────────────────────────────
    _deadline = time.time() + HARD_DEADLINE_MINS * 60

    ap=argparse.ArgumentParser(description="V2Ray AI Hunter v10")
    ap.add_argument("--dry-run",action="store_true")
    ap.add_argument("--sni",default="")
    args=ap.parse_args()
    if args.sni: CUSTOM_SNI=args.sni.strip()

    t0=time.time()
    mode=ai_mode()
    log.info("╔══════════════════════════════════════════════════════╗")
    log.info("║  🤖 V2RAY ULTIMATE HUNTER v10 — VIRUS MODE          ║")
    log.info(f"║  {len(SOURCES):<4} sources | {HARD_DEADLINE_MINS}m deadline | {mode['name']:10} mode       ║")
    log.info("╚══════════════════════════════════════════════════════╝")
    log.info(ai_diagnose())
    log.info(f"🧠 {ai_report()} | good:{len(_AI.get('good_ips',[]))} | sni={'auto' if not CUSTOM_SNI else CUSTOM_SNI}")
    if args.dry_run: log.info("🔇 Dry-run")

    # تحقق من BOT_TOKEN قبل أي شيء
    if not BOT_TOKEN and not args.dry_run:
        log.error("❌ BOT_TOKEN environment variable is NOT SET!")
        log.error("   Go to GitHub → Settings → Secrets → Add BOT_TOKEN")
    else:
        log.info(f"✅ BOT_TOKEN: {'***'+BOT_TOKEN[-4:] if BOT_TOKEN else 'NOT SET'}")

    # ── 1. Self-Evolution — اكتشف مصادر جديدة ─────────────────────────────
    existing_urls=set(SOURCES)|set(_AI.get("discovered_sources",[]))
    new_discovered=[]
    with _ai_lock: _runs = _AI.get("runs", 0)
    # Evolution فقط إذا عندنا وقت كافٍ وليس أول run
    if deadline_left() > 16*60 and _runs > 0:
        log.info("🦠 Evolution scan ...")
        new_discovered=evolve_discover_sources(existing_urls)
    elif _runs == 0:
        log.info("🦠 First run — skipping evolution to save time")

    # ── 2. Load Cache ──────────────────────────────────────────────────────
    cached_raw=cache_load()
    cached_objs=cache_to_configs(cached_raw)
    verified_cached=[]
    if cached_objs:
        log.info(f"♻️  Re-verifying {len(cached_objs)} cached ...")
        for c in cached_objs[:20]:
            if not deadline_ok(): break
            p=tcp_ping(c.host,c.port)
            if p is None or p>mode["max_ping"]: continue
            bh=c.best_bug_host or (c.compatible_hosts[0] if c.compatible_hosts else "")
            if bh:
                path=extract_path(c.raw) if c.raw else "/ws"
                ms=ws_probe(c.host,c.port,bh,path=path)
                if ms is None: continue
                c.probe_ms=ms
            verified_cached.append(c)
        log.info(f"♻️  {len(verified_cached)}/{len(cached_objs)} verified")

    # ── 3. Collect ─────────────────────────────────────────────────────────
    raws:list=[]
    if deadline_ok():
        extra=list(set(new_discovered)|set(_AI.get("discovered_sources",[])))
        raws=collect_configs(extra_sources=extra)
    if not raws and not verified_cached:
        log.error("Nothing collected — exit"); return

    # ── 4. Check ───────────────────────────────────────────────────────────
    fresh:list=[]
    if raws and deadline_ok():
        fresh=run_checks(raws)

    # ── 5. Merge ───────────────────────────────────────────────────────────
    fh={c.host for c in fresh}
    live=fresh+[c for c in verified_cached if c.host not in fh]
    if not live: log.error("No live configs — exit"); return

    # ── 6. Geo ─────────────────────────────────────────────────────────────
    if fresh and deadline_ok():
        log.info(f"🔍 Geo ({len(fresh)}) ...")
        with ThreadPoolExecutor(max_workers=GEO_WORKERS) as ex:
            enriched=list(ex.map(enrich,fresh))
        eh={c.host for c in enriched}
        live=enriched+[c for c in verified_cached if c.host not in eh]

    # ── 7. Sort ────────────────────────────────────────────────────────────
    live.sort(key=lambda c:c.score(),reverse=True)

    # ── 8. Report ──────────────────────────────────────────────────────────
    log.info(f"\n📊 Top {min(10,len(live))}:")
    log.info("  #   Type  Ping   Probe  Compat  CC   Host")
    for i,c in enumerate(live[:10],1):
        t=(("⚡" if c.is_cf else "  ")+(("🚀" if c.is_vps else "  "))+("🔒" if c.ssl_ok else "  "))
        log.info(f"  {i:>2}. {t} {c.ping_ms:>4}ms {c.probe_ms:>4}ms "
                 f"{len(c.compatible_hosts):>2}/{len(ALL_BUG_HOSTS)}  "
                 f"{c.country_code:<3}  {c.host[:30]}")

    # ── 9. Post ────────────────────────────────────────────────────────────
    posted=0
    for cfg in live:
        if posted>=MAX_POSTS: break
        if not deadline_ok(): break
        if args.dry_run:
            log.info(f"[DRY] {cfg.host} | {cfg.ai_diagnosis}"); posted+=1
        else:
            if send_tg(cfg):
                posted+=1
                log.info(f"📨 {posted}/{MAX_POSTS}: {cfg.host}→{cfg.best_bug_host}")
                time.sleep(2)

    # ── 10. Save ───────────────────────────────────────────────────────────
    save_sub(live); cache_save(live)

    # ── 11. Update AI memory ───────────────────────────────────────────────
    with _ai_lock:
        _AI["runs"]+=1; _AI["posted"]+=posted
        _AI["last"]=datetime.now(timezone.utc).isoformat()[:16]
    _ai_save(_AI)

    elapsed=int(time.time()-t0)
    log.info(
        f"\n🏁 {elapsed}s | {len(fresh)} fresh | {len(verified_cached)} cached | "
        f"{posted} posted | +{len(new_discovered)} discovered"
    )
    log.info(ai_diagnose())
    log.info(ai_report())


if __name__ == "__main__":
    main()
