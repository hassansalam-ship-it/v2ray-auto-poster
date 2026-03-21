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
    elif rate < 0.02:
        return {"name":"BALANCED","max_ping":700,"max_probe":2500,"min_compat":1}
    else:
        return {"name":"STRICT","max_ping":600,"max_probe":2000,"min_compat":2}

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
            r = requests.get(url, headers=headers, timeout=8, verify=False)
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
CF_KW  = ("cloudflare","104.16.","104.17.","104.18.","104.19.","104.20.",
           "104.21.","172.64.","172.65.","172.66.","172.67.","1.1.1.","1.0.0.")
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
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/provider/Config.txt",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub6",
    "https://raw.githubusercontent.com/freefq/free/master/vless",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash-meta.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/V2Ray",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/ss-sub",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/openai.txt",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes/all",
    "https://raw.githubusercontent.com/ErfanNamira/FreeLink/main/Links.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/en/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/fa/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/splitted/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/splitted/vless",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_raw.txt",
    "https://raw.githubusercontent.com/Airscker/DeadPool/main/abbb.md",
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/actives.txt",
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt",
    "https://raw.githubusercontent.com/khaled-alselwady/free-proxy-and-vpn/main/V2ray/v2ray.txt",
    "https://raw.githubusercontent.com/mahdibland/SSAggregator/master/sub/sub_merge_base64.txt",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/best.txt",
    "https://raw.githubusercontent.com/resasanian/Mirza/main/sub.txt",
    "https://raw.githubusercontent.com/Fukki-Z/nodefree/main/update",
    "https://raw.githubusercontent.com/Fukki-Z/nodefree/main/update/20231001",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vless",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vmess",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/mix4",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/mix3",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/all3",
    "https://raw.githubusercontent.com/vveg26/get_proxy/main/substrings/v2ray.txt",
    "https://raw.githubusercontent.com/vveg26/get_proxy/main/substrings/vmess.txt",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/mix",
    "https://raw.githubusercontent.com/Surfboardv2ray/Proxy-sorter/main/submerge/output.txt",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.txt",
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet_WSS.txt",
    "https://raw.githubusercontent.com/mheidari98/.proxy/main/tls",
    "https://raw.githubusercontent.com/Surfboardv2ray/v2ray-worker-sub/master/Eternity",
    "https://raw.githubusercontent.com/itsyebekhe/PSG/main/CONFIGS/Normal/mix",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/all-in-one",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Temp/TG-CF",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/Temp/TG",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/meta",
    "https://raw.githubusercontent.com/hkaa0/permalink/main/proxy/V2ray",
    "https://raw.githubusercontent.com/hkaa0/permalink/main/proxy/Shadowsocks.md",
    "https://raw.githubusercontent.com/vpnhat/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/Incognito-Coder/SimpleSub/main/Xray/Normal/all",
    "https://raw.githubusercontent.com/Incognito-Coder/SimpleSub/main/Xray/Base64/all",
    "https://raw.githubusercontent.com/Jia-Pingwa/free-v2ray-merge/main/output/v2ray",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity_base64.txt",
    "https://raw.githubusercontent.com/parhamb7/parhamb7/main/sub",
    "https://raw.githubusercontent.com/VerveProxy/SubVerve/main/Normal/sub1.txt",
    "https://raw.githubusercontent.com/VerveProxy/SubVerve/main/Normal/sub2.txt",
    "https://raw.githubusercontent.com/4n0nymou3/ss-config-updater/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/EACOJ/free/master/VMess-VLESS",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/reality",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/reality",
    "https://raw.githubusercontent.com/proxy-list/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/V2RaySub/V2RaySub/main/Subs/Sub_1",
    "https://raw.githubusercontent.com/V2RaySub/V2RaySub/main/Subs/Sub_2",
    "https://raw.githubusercontent.com/V2RaySub/V2RaySub/main/Subs/Sub_3",
    "https://raw.githubusercontent.com/V2RaySub/V2RaySub/main/Subs/Sub_4",
    "https://t.me/s/V2pedia",
    "https://t.me/s/XskyGroup",
    "https://t.me/s/free4allVPN",
    "https://t.me/s/vpn_xv",
    "https://t.me/s/freewireguard",
    "https://t.me/s/FreeVlessVpn",
    "https://t.me/s/Vpnreality",
    "https://t.me/s/FreakConfig",
    "https://t.me/s/v2ray_outlineorg",
    "https://t.me/s/proxyymeliii",
    "https://t.me/s/ArV2ray",
    "https://t.me/s/MsV2ray",
    "https://t.me/s/iranvpnet",
    "https://t.me/s/UnlimitedDev",
    "https://t.me/s/Outline_Vpn",
    "https://t.me/s/vmess_vless_v2rayng",
    "https://t.me/s/vless_vmess",
    "https://t.me/s/vmess_free1",
    "https://t.me/s/NIM_VPN_ir",
    "https://t.me/s/Configforvpn01",
    "https://t.me/s/NetAccount_ir",
    "https://t.me/s/v2_vmess",
    "https://t.me/s/Awlix_ir",
    "https://t.me/s/proxystore11",
    "https://t.me/s/link_proxy",
    "https://t.me/s/shadowsocks_v2rayng",
    "https://t.me/s/v2ray_swhil",
    "https://t.me/s/comv2ray",
    "https://t.me/s/V2rayNGmat",
    "https://t.me/s/Lockey_VPN",
    "https://t.me/s/SafeNet_Server",
    "https://t.me/s/SSV2ray",
    "https://t.me/s/v2ray_configs",
    "https://t.me/s/ElitePVPN",
    "https://t.me/s/VPN_Master_ir1",
    "https://t.me/s/ShadowSocks_s",
    "https://t.me/s/oneclickvpnkeys",
    "https://t.me/s/v2line",
    "https://t.me/s/Free_V2rayyy",
    "https://t.me/s/V2RayNGConfig",
    "https://t.me/s/proxies_r",
    "https://t.me/s/CFproxyServer",
    "https://t.me/s/ConfigsHUB",
    "https://sub.nicevpn.top/full",
    "https://sub.nicevpn.top/full-new",
    "https://proxy.yugidepgvip.workers.dev/",
    "https://v2ray.ding.free.hr/Vmesspublic",
    "https://v2ray.ding.free.hr/Vpublic",
    "https://proxypool.freeair888.workers.dev/clash/proxies",
    "https://raw.iqiq.io/freev2ray",
    "https://freev2ray.org/",
    "https://www.v2share.top/api/v1/client/subscribe?token=free",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STRUCTURE VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_PATH_RE = re.compile(
    r"^/(?:ws|vws|linkvws|link|v2ray|proxy|grpc|wss?|ray|xray|"
    r"vmess|vless|relay|[a-zA-Z0-9_-]{2,30})(?:/.*)?$"
)

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
_LOCKED = (
    "zain.com","oodi.com","mobily.com","stc.com","ooredoo.",
    "etisalat.","du.ae","vodafone.sa","tedata.","batelco.",
    "omantel.","nawras.","wimax.","wana.",
)

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
    sni=extract_sni(raw).lower().strip()
    if not sni: return False
    return any(p in sni for p in _LOCKED)

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

def ws_probe(host:str,port:int,bug_host:str,path:str="/ws")->Optional[int]:
    """
    AGGRESSIVE PROBE:
    ✅ 101 = WebSocket nشط (أفضل)
    ✅ 400+CF-Ray+v2path = CF Worker موجود (v2ray يتعامل معه)
    ✅ 200+WS headers = VPS WebSocket
    ❌ كل شيء آخر
    """
    if not deadline_ok(): return None
    ctx=_ssl_ctx()
    # AI يختار أفضل paths
    ai_paths=ai_best_paths()
    if path not in ai_paths: ai_paths.insert(0,path)
    v2_paths={"/ws","/linkvws","/vws","/link","/v2ray","/ray","/xray","/proxy"}

    for try_path in ai_paths[:5]:
        try:
            t0=time.perf_counter()
            conn=socket.create_connection((host,port),timeout=PROBE_TIMEOUT)
            conn.settimeout(PROBE_TIMEOUT)
            sock=ctx.wrap_socket(conn,server_hostname=bug_host)
            key=base64.b64encode(os.urandom(16)).decode()
            req=(
                f"GET {try_path} HTTP/1.1\r\nHost: {bug_host}\r\n"
                f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
                f"Origin: https://{bug_host}\r\n"
                f"User-Agent: Go-http-client/2.0\r\n\r\n"
            )
            sock.sendall(req.encode())
            resp=b""
            dl=time.perf_counter()+PROBE_TIMEOUT
            while time.perf_counter()<dl:
                try:
                    chunk=sock.recv(4096)
                    if not chunk: break
                    resp+=chunk
                    if b"\r\n\r\n" in resp: break
                except Exception: break
            elapsed=int((time.perf_counter()-t0)*1000)
            try: sock.close()
            except Exception: pass
            if not resp: continue
            first=resp.split(b"\r\n")[0].decode(errors="ignore").strip()
            if not first.startswith("HTTP"): continue
            parts=first.split()
            status=int(parts[1]) if len(parts)>=2 and parts[1].isdigit() else 0
            rl=resp.lower()
            is_cf=b"cf-ray:" in rl or b"server: cloudflare" in rl
            has_ws=b"upgrade: websocket" in rl or b"sec-websocket-accept" in rl
            is_v2p=try_path in v2_paths or bool(re.match(r"^/(ws|link|vws|ray|xray|vmess|vless|proxy)",try_path,re.I))

            if status==101:
                ai_bug_update(bug_host,True); ai_path_win(try_path)
                log.debug(f"  ✅101 {host}←{bug_host}{try_path} {elapsed}ms")
                return elapsed
            if status==200 and has_ws:
                ai_bug_update(bug_host,True); ai_path_win(try_path)
                log.debug(f"  ✅200+WS {host}←{bug_host} {elapsed}ms")
                return elapsed
            if status==400 and is_cf and is_v2p:
                ai_bug_update(bug_host,True); ai_path_win(try_path)
                log.debug(f"  ✅400+CF {host}←{bug_host}{try_path} {elapsed}ms")
                return elapsed
            log.debug(f"  ❌{status} cf={is_cf} {try_path} {host}←{bug_host}")
        except Exception: pass

    ai_bug_update(bug_host,False)
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
        ai_stat("struct"); return None
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
    is_cf  =(is_cf_ip(ip) if ip else False) or any(k in (host+raw).lower() for k in CF_KW)
    is_vps = any(k in (host+raw).lower() for k in VPS_KW)

    # 4. Probe
    if CUSTOM_SNI:
        ms=ws_probe(host,port,CUSTOM_SNI)
        if ms is None: ai_stat("probe"); return None
        compat,best,probe_ms=[CUSTOM_SNI],CUSTOM_SNI,ms
    else:
        # مرّر domain السيرفر لفحص VPS أولاً
        compat,best,probe_ms=multi_probe(host,port,raw, server_sni=host)
        if len(compat)<mode["min_compat"]:
            ai_stat("probe")
            if ip: ai_bad_ip(ip)
            return None
        if probe_ms>mode["max_probe"]: return None

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
    log.info(f"📦 {len(unique)} unique | {good}/{len(ordered)} active")
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

    def _w(raw:str)->Optional[V2Config]:
        if stop.is_set() or not deadline_ok(): return None
        try: return check_raw(raw)
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

    log.info(f"✅ {len(live)} live | {errs[0]} errors | {ai_diagnose()}")
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
    if not BOT_TOKEN: return False
    payload={
        "chat_id":CHAT_ID,"text":build_message(cfg),
        "parse_mode":"HTML","disable_web_page_preview":True,
        "reply_markup":{"inline_keyboard":[[
            {"text":"📢 Channel","url":"https://t.me/V2rayashaq"},
            {"text":"👤 Admin","url":f"https://t.me/{ADMIN_USER.lstrip('@')}"},
        ]]}
    }
    for attempt in range(3):
        try:
            res=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                              json=payload,timeout=15)
            if res.status_code==429:
                w=res.json().get("parameters",{}).get("retry_after",20)
                time.sleep(w); continue
            if res.ok: return True
            log.warning(f"TG {res.status_code}: {res.text[:80]}")
            return False
        except Exception as e:
            log.warning(f"TG #{attempt+1}: {e}"); time.sleep(3)
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

    # ── 1. Self-Evolution — اكتشف مصادر جديدة ─────────────────────────────
    existing_urls=set(SOURCES)|set(_AI.get("discovered_sources",[]))
    new_discovered=[]
    if deadline_left() > 15*60:  # فقط إذا عندنا وقت كافٍ
        log.info("🦠 Evolution scan starting...")
        new_discovered=evolve_discover_sources(existing_urls)

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
