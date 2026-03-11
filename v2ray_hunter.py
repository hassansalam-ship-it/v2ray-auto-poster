“””
V2RAY ULTIMATE HUNTER v4 - ASHAQ TEAM

- Empty SNI only + Allow Insecure injected
- Self-evolving: discovers new sources, learns from success/failure
  “””
  import os, re, ssl, sys, json, time, socket, base64
  import logging, threading, argparse, requests
  from datetime import datetime, timezone
  from dataclasses import dataclass
  from typing import Optional
  from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── LOGGING ────────────────────────────────────────────────────

log = logging.getLogger(“V2Hunter”)
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter(”%(asctime)s | %(levelname)-7s | %(message)s”, “%H:%M:%S”)
_ch  = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt); _ch.setLevel(logging.INFO)
log.addHandler(_ch)
try:
_fh = logging.FileHandler(“v2ray_hunt.log”, encoding=“utf-8”)
_fh.setFormatter(_fmt); _fh.setLevel(logging.DEBUG)
log.addHandler(_fh)
except Exception:
pass

# ─── SETTINGS ───────────────────────────────────────────────────

BOT_TOKEN        = os.environ.get(“BOT_TOKEN”, “”)
CHAT_ID          = “@V2rayashaq”
ADMIN_USER       = os.environ.get(“ADMIN_TG”, “@genie_2000”)
SUB_FILE         = “sub_link.txt”
SOURCES_FILE     = “learned_sources.json”
STATS_FILE       = “source_stats.json”
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
“https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix”,
“https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vless”,
“https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/vmess”,
“https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/mix”,
“https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vless”,
“https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vmess”,
“https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub6.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub7.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub8.txt”,
“https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt”,
“https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt”,
“https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/mix”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed”,
“https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_Sub.txt”,
“https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub”,
“https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt”,
“https://raw.githubusercontent.com/freefq/free/master/v2”,
“https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2”,
“https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/All.txt”,
“https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray”,
“https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free”,
“https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all”,
“https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all3”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vless”,
“https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub”,
“https://raw.githubusercontent.com/itsyebekhe/HiN-VPN/main/subscription/normal/mix”,
“https://raw.githubusercontent.com/itsyebekhe/HiN-VPN/main/subscription/base64/mix”,
“https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt”,
“https://raw.githubusercontent.com/ts-sf/fly/main/v2”,
“https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt”,
“https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/merged.txt”,
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt”,
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt”,
“https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt”,
“https://raw.githubusercontent.com/IranianCypherpunks/sub/main/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/1/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/2/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/5/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/10/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/20/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/30/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/50/config”,
“https://raw.githubusercontent.com/vxiaov/free_proxies/main/v2ray/v2ray.share.txt”,
“https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/all_configs.txt”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/G-Core.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/cloudflare.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Atlas.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Mullvad.md”,
“https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt”,
“https://raw.githubusercontent.com/Surfboardv2ray/v2ray-cf/main/sub”,
“https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vless”,
“https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vmess”,
“https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Mix/mix.txt”,
“https://raw.githubusercontent.com/snakem982/proxypool/main/vmess.txt”,
“https://raw.githubusercontent.com/snakem982/proxypool/main/vless.txt”,
“https://raw.githubusercontent.com/mheidari98/.proxy/main/all”,
“https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/proxy.txt”,
“https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/mix.txt”,
“https://raw.githubusercontent.com/resasanian/Mirza/main/sub”,
“https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt”,
“https://raw.githubusercontent.com/ermaozi01/free_clash_vpn/main/subscribe/v2ray.txt”,
“https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/node.txt”,
“https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/merged.txt”,
“https://raw.githubusercontent.com/dimzon/scaling-robot/main/all”,
“https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/mix_base64”,
“https://raw.githubusercontent.com/hermansh-id/belajar-script-proxy/main/sub/vmess”,
“https://raw.githubusercontent.com/GalaxyCom2023/v2ray/main/sub”,
“https://raw.githubusercontent.com/free18/v2ray/main/v2ray.txt”,
“https://raw.githubusercontent.com/free18/v2ray/main/vmess.txt”,
“https://raw.githubusercontent.com/free18/v2ray/main/vless.txt”,
“https://raw.githubusercontent.com/mganotas/outbound/main/raw.txt”,
“https://raw.githubusercontent.com/Moli-X/Resources/main/Subscription/Collect.txt”,
“https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/default.txt”,
“https://raw.githubusercontent.com/proxypool404/v2ray/main/all.txt”,
“https://raw.githubusercontent.com/Airscker/V2Ray-Config-Pool/main/all.txt”,
“https://raw.githubusercontent.com/vpn0/v2ray/main/v2ray.txt”,
“https://raw.githubusercontent.com/VPN-Speed/V2ray-Config/main/sub.txt”,
“https://raw.githubusercontent.com/jason5ng32/MyIP/main/public/v2ray.txt”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/vless”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/vmess”,
“https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/mix”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vmess.txt”,
“https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/mixed”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vmess”,
“https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/v2ray.txt”,
“https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/vmess.txt”,
“https://raw.githubusercontent.com/dimzon/scaling-robot/main/vmess”,
“https://raw.githubusercontent.com/dimzon/scaling-robot/main/vless”,
“https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/vmess_Sub.txt”,
“https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/vless_Sub.txt”,
“https://t.me/s/v2_team”,
“https://t.me/s/V2ray_Alpha”,
“https://t.me/s/V2Ray_VLESS_VMess”,
“https://t.me/s/Cloudfront_VPN”,
“https://t.me/s/CDN_V2RAY”,
“https://t.me/s/v2rayng_org”,
“https://t.me/s/v2rayNG_Backup”,
“https://t.me/s/FreeV2rays”,
“https://t.me/s/free_v2rayyy”,
“https://t.me/s/IPV2RAY”,
“https://t.me/s/PrivateVPNs”,
“https://t.me/s/FreeVless”,
“https://t.me/s/freeNodes”,
“https://t.me/s/meli_proxi”,
“https://t.me/s/ShadowProxy66”,
“https://t.me/s/v2ray1_ng”,
“https://t.me/s/VmessProtocol”,
“https://t.me/s/DigiV2ray”,
“https://t.me/s/v2rayen”,
“https://t.me/s/v2ray_collector”,
“https://t.me/s/VlessConfig”,
“https://t.me/s/XrayFreeConfig”,
“https://t.me/s/DirectVPN”,
“https://t.me/s/freevlesskey”,
“https://t.me/s/v2ray_free_conf”,
“https://t.me/s/vmessconfig”,
“https://t.me/s/FreeV2ray4u”,
“https://t.me/s/V2ray4Iran”,
“https://t.me/s/ConfigsHub”,
“https://t.me/s/v2rayNGn”,
“https://t.me/s/vlessconfig”,
“https://t.me/s/v2ray_configs_pool”,
“https://t.me/s/VPN_Hell”,
“https://t.me/s/v2rayshop”,
“https://t.me/s/v2rayngvpn”,
“https://t.me/s/VpnSkyy”,
“https://t.me/s/V2RayOxygen”,
“https://t.me/s/GetConfig”,
“https://t.me/s/V2rayNG_Collector”,
“https://t.me/s/Freee_VPN”,
“https://t.me/s/v2ray_vpn_ir”,
“https://t.me/s/V2RayIranStable”,
“https://t.me/s/GozarVPN”,
“https://t.me/s/fast_v2ray”,
“https://t.me/s/freenode_v2ray”,
“https://t.me/s/Hiddify”,
“https://t.me/s/v2rayng_vpn”,
“https://t.me/s/IranProxies”,
“https://t.me/s/NetworkNinja”,
“https://t.me/s/free_shadowsocks_v2ray”,
“https://t.me/s/NightFox_VPN”,
“https://t.me/s/HiddifyNG”,
“https://t.me/s/Sing_Box_Config”,
“https://t.me/s/XrayConfig”,
“https://t.me/s/XrayFree”,
“https://t.me/s/ClashConfig”,
“https://t.me/s/V2rayCDN”,
“https://t.me/s/CloudflareV2ray”,
]

VPS_KEYWORDS = [
“oracle”,“google”,“amazon”,“aws”,“digitalocean”,“hetzner”,“ovh”,
“linode”,“vultr”,“azure”,“contabo”,“alibaba”,“tencent”,“rackspace”,
“leaseweb”,“choopa”,“quadranet”,“frantech”,“datacamp”,“incapsula”,
“cloudflare”,“fastly”,“akamai”,“cdn77”,“stackpath”,“clouvider”,
“hostwinds”,“liquidweb”,“vps”,“datacenter”,“hosting”,
]
CF_KEYWORDS = [
“cloudfront”,“cdn”,“worker”,“pages.dev”,“nodes.com”,
“cloudflare”,“cfcdn”,“cfip”,“104.”,“172.64.”,“172.65.”,
“172.66.”,“172.67.”,“162.158.”,“198.41.”,
]

CONFIG_RE  = re.compile(r”(?:vless|vmess)://[^\s#"'<>][]+”)
GITHUB_RAW = re.compile(r”https://raw.githubusercontent.com/[^\s"'<>][)]+.txt”)
GITHUB_SUB = re.compile(r”https://raw.githubusercontent.com/[^\s"'<>][)]+/(?:sub|v2ray|mix|vless|vmess|config)[^\s"'<>][)]*”)

# ─── SNI UTILS ──────────────────────────────────────────────────

_SNI_KEYS = (“sni”,“host”,“peer”,“servername”,“server-name”)

def _extract_vless_sni(raw: str) -> str:
for k in _SNI_KEYS:
m = re.search(rf”[?&]{k}=([^&\s#]+)”, raw, re.IGNORECASE)
if m:
return m.group(1)
return “”

def _extract_vmess_sni(raw: str) -> str:
try:
b64 = raw[len(“vmess://”):]
obj = json.loads(base64.b64decode(b64 + “==” * 3).decode(“utf-8”, errors=“ignore”))
for k in _SNI_KEYS:
if obj.get(k):
return str(obj[k])
except Exception:
pass
return “”

def extract_sni(raw: str) -> str:
return _extract_vmess_sni(raw) if raw.startswith(“vmess://”) else _extract_vless_sni(raw)

def has_empty_sni(raw: str) -> bool:
return extract_sni(raw) == “”

def inject_allow_insecure_vless(raw: str) -> str:
“”“Inject allowInsecure=1 and ensure SNI stays empty in vless config”””
if “allowInsecure=1” in raw or “allowinsecure=1” in raw.lower():
return raw
sep = “&” if “?” in raw else “?”
return raw + f”{sep}allowInsecure=1”

def inject_allow_insecure_vmess(raw: str) -> str:
“”“Inject allowInsecure=1 in vmess config”””
try:
b64 = raw[len(“vmess://”):]
obj = json.loads(base64.b64decode(b64 + “==” * 3).decode(“utf-8”, errors=“ignore”))
obj[“allowInsecure”] = True
obj[“skip-cert-verify”] = True
# Keep SNI empty
for k in _SNI_KEYS:
if k in obj:
obj[k] = “”
return “vmess://” + base64.b64encode(
json.dumps(obj, ensure_ascii=False).encode()
).decode()
except Exception:
return raw

def patch_config(raw: str) -> str:
“”“Patch config: empty SNI + allowInsecure enabled”””
if raw.startswith(“vmess://”):
return inject_allow_insecure_vmess(raw)
return inject_allow_insecure_vless(raw)

# ─── SELF-LEARNING SOURCE MANAGER ───────────────────────────────

class SourceManager:
def **init**(self):
self.stats   = self._load(STATS_FILE, {})
self.learned = self._load(SOURCES_FILE, [])

```
def _load(self, path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save(self):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)
        with open(SOURCES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.learned, f, indent=2)
        log.info(f"Saved stats for {len(self.stats)} sources, {len(self.learned)} learned")
    except Exception as e:
        log.warning(f"Could not save source data: {e}")

def record(self, url: str, count: int):
    if url not in self.stats:
        self.stats[url] = {"hits": 0, "fails": 0, "total": 0}
    if count > 0:
        self.stats[url]["hits"]  += 1
        self.stats[url]["total"] += count
    else:
        self.stats[url]["fails"] += 1

def add_discovered(self, urls: list):
    existing = set(BASE_SOURCES) | set(self.learned)
    new = [u for u in set(urls) if u not in existing and len(u) < 300]
    if new:
        log.info(f"Discovered {len(new)} new sources to try")
        self.learned.extend(new)
        self.learned = list(set(self.learned))

def prune_bad_sources(self):
    before = len(self.learned)
    self.learned = [
        u for u in self.learned
        if not (
            self.stats.get(u, {}).get("fails", 0) >= 5 and
            self.stats.get(u, {}).get("hits", 0) == 0
        )
    ]
    pruned = before - len(self.learned)
    if pruned:
        log.info(f"Pruned {pruned} dead learned sources")

def get_all_sources(self) -> list:
    def score(url):
        s = self.stats.get(url, {})
        hits  = s.get("hits", 0)
        fails = s.get("fails", 0)
        total_calls = hits + fails
        if total_calls == 0:
            return 0.5
        success_rate = hits / total_calls
        avg_yield    = s.get("total", 0) / max(hits, 1)
        return success_rate * 0.6 + min(avg_yield / 100, 1.0) * 0.4

    all_srcs = list(set(BASE_SOURCES + self.learned))
    all_srcs.sort(key=score, reverse=True)
    return all_srcs
```

# ─── DATA MODEL ─────────────────────────────────────────────────

@dataclass
class V2Config:
raw:          str
raw_patched:  str
host:         str
port:         int
ping_ms:      int
proto:        str
ssl_ok:       bool = False
ssl_cert_cn:  str  = “”
country_code: str  = “??”
country:      str  = “Unknown”
isp:          str  = “”
is_vps:       bool = False
is_cf:        bool = False

```
def score(self) -> int:
    s  = 600 if self.is_vps else 0
    s += 400 if self.is_cf  else 0
    s += 200 if self.ssl_ok else 0
    s += max(0, 600 - self.ping_ms)
    return s
```

# ─── FETCH + DISCOVER ───────────────────────────────────────────

def _fetch(url: str, sm: SourceManager) -> tuple:
discovered = []
try:
r = requests.get(url, timeout=FETCH_TIMEOUT, headers={“User-Agent”: “Mozilla/5.0”})
text = r.text

```
    # Discover new raw github URLs from page
    discovered += GITHUB_RAW.findall(text)
    discovered += GITHUB_SUB.findall(text)

    found = CONFIG_RE.findall(text)
    if not found:
        try:
            decoded = base64.b64decode(text.strip() + "==").decode("utf-8", errors="ignore")
            found   = CONFIG_RE.findall(decoded)
            discovered += GITHUB_RAW.findall(decoded)
        except Exception:
            pass

    # Filter: port 443 AND empty SNI only
    found = [c for c in found if ":443" in c and has_empty_sni(c)]

    sm.record(url, len(found))
    if found:
        log.info(f"OK {len(found):>4} empty-SNI <- {url[:65]}")
    return found, discovered
except Exception:
    sm.record(url, 0)
    return [], discovered
```

def collect_configs(sm: SourceManager) -> list:
sources = sm.get_all_sources()
log.info(f”Fetching from {len(sources)} sources [{FETCH_WORKERS} workers]…”)
all_raw:    list = []
discovered: list = []

```
with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
    future_map = {ex.submit(_fetch, u, sm): u for u in sources}
    for fut in as_completed(future_map):
        try:
            cfgs, disc = fut.result()
            all_raw.extend(cfgs)
            discovered.extend(disc)
        except Exception:
            pass

sm.add_discovered(discovered)
sm.prune_bad_sources()

unique = list(set(all_raw))
log.info(f"{len(unique)} unique empty-SNI port-443 configs")
return unique
```

# ─── TCP PING + SSL ─────────────────────────────────────────────

def tcp_ping(host: str, port: int) -> Optional[int]:
try:
t0 = time.perf_counter()
with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT):
return int((time.perf_counter() - t0) * 1000)
except Exception:
return None

def ssl_check(host: str, port: int) -> tuple:
“”“Check SSL without verifying cert (Allow Insecure mode)”””
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode    = ssl.CERT_NONE
try:
with ctx.wrap_socket(
socket.create_connection((host, port), timeout=SSL_TIMEOUT),
server_hostname=host,
do_handshake_on_connect=True
) as s:
der = s.getpeercert(binary_form=True) or b””
cn  = “”
if der:
try:
pem = ssl.DER_cert_to_PEM_cert(der)
m   = re.search(r”CN\s*=\s*([^\n,/]+)”, pem)
if m: cn = m.group(1).strip()
except Exception:
pass
return True, cn
except Exception:
return False, “”

def check_raw(raw: str) -> Optional[V2Config]:
# Must have empty SNI
if not has_empty_sni(raw):
return None
m = re.search(r”@([^:/\s]#]+):(\d+)”, raw)
if not m:
return None
host = m.group(1)
try:
port = int(m.group(2))
except ValueError:
return None
if port != TARGET_PORT:
return None

```
proto = "VLESS" if raw.startswith("vless://") else "VMESS"
ping  = tcp_ping(host, port)
if ping is None or ping > MAX_PING_MS:
    return None

# Patch: inject allowInsecure=1, keep SNI empty
patched = patch_config(raw)

# SSL check (insecure mode - no cert verification)
ssl_ok, ssl_cn = ssl_check(host, port)

return V2Config(
    raw=raw, raw_patched=patched,
    host=host, port=port, ping_ms=ping,
    proto=proto, ssl_ok=ssl_ok, ssl_cert_cn=ssl_cn
)
```

# ─── PARALLEL CHECK ─────────────────────────────────────────────

def run_checks(raws: list) -> list:
log.info(f”Checking {len(raws)} configs [{CHECK_WORKERS} workers]…”)
live: list = []
stop = threading.Event()
lock = threading.Lock()

```
def _worker(raw: str) -> Optional[V2Config]:
    if stop.is_set():
        return None
    try:
        return check_raw(raw)
    except Exception:
        return None

with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as ex:
    for f in as_completed({ex.submit(_worker, r): r for r in raws}):
        if stop.is_set():
            f.cancel()
            continue
        try:
            res = f.result()
        except Exception:
            res = None
        if res:
            with lock:
                live.append(res)
                if len(live) >= STOP_AFTER_FOUND:
                    stop.set()
                    log.info(f"Stop gate reached: {STOP_AFTER_FOUND}")

log.info(f"{len(live)} live empty-SNI configs found")
return live
```

# ─── GEO ────────────────────────────────────────────────────────

_geo:   dict = {}
_glock = threading.Lock()

def get_geo(ip: str) -> tuple:
with _glock:
if ip in _geo: return _geo[ip]
try:
r = requests.get(
f”http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp”,
timeout=5
).json()
result = (r.get(“countryCode”,”??”), r.get(“country”,“Unknown”), r.get(“isp”,””))   
if r.get(“status”) == “success” else (”??”,“Unknown”,””)
except Exception:
result = (”??”,“Unknown”,””)
with _glock:
_geo[ip] = result
return result

def enrich(cfg: V2Config) -> V2Config:
try:
ip = socket.gethostbyname(cfg.host)
cfg.country_code, cfg.country, cfg.isp = get_geo(ip)
except Exception:
pass
low        = (cfg.raw + cfg.host + cfg.isp).lower()
cfg.is_cf  = any(k in low for k in CF_KEYWORDS)
cfg.is_vps = any(k in low for k in VPS_KEYWORDS)
return cfg

# ─── MESSAGE BUILDER ────────────────────────────────────────────

def _ping_bar(ms: int) -> str:
if ms < 80:  return “Ultra Fast”
if ms < 150: return “Fast”
if ms < 300: return “Good”
if ms < 500: return “Moderate”
return “Slow”

def build_message(cfg: V2Config) -> str:
now = datetime.now(timezone.utc).strftime(”%Y-%m-%d %H:%M UTC”)

```
# Header: VPS = fire + Ultimate Ashaq, normal = Welcome to Ashaq
if cfg.is_vps:
    header = (
        "&#128293;&#128293;&#128293; "
        "<b>Ultimate Ashaq</b> "
        "&#128293;&#128293;&#128293;"
    )
else:
    header = "&#127881; <b>Welcome to Ashaq</b> &#127881;"

type_tag = "VPS &#128640;" if cfg.is_vps else "Shared &#128421;"
if cfg.is_cf:
    type_tag += " + CF &#9889;"

ssl_line = (
    "&#9989; SSL Active (Allow Insecure)"
    if cfg.ssl_ok else
    "&#9888;&#65039; No SSL (Allow Insecure)"
)
ssl_tag = " #SSL" if cfg.ssl_ok else ""

return (
    f"{header}\n"
    f"========================\n"
    f"&#127758; <b>Country:</b> {cfg.country_code} {cfg.country}\n"
    f"&#128311; <b>Protocol:</b> {cfg.proto}\n"
    f"&#128421; <b>Type:</b> {type_tag}\n"
    f"&#128274; <b>SSL/TLS:</b> {ssl_line}\n"
    f"&#128290; <b>SNI:</b> Empty &#10004;\n"
    f"&#128421; <b>Allow Insecure:</b> ON &#10004;\n"
    f"&#9889; <b>Ping:</b> {cfg.ping_ms}ms  {_ping_bar(cfg.ping_ms)}\n"
    f"&#127760; <b>ISP:</b> {cfg.isp or 'Unknown'}\n"
    f"&#128197; <b>Verified:</b> {now}\n"
    f"========================\n"
    f"<code>{cfg.raw_patched}</code>\n"
    f"========================\n"
    f"#Ashaq #V2Ray #Free443 #{cfg.proto} #EmptySNI #AllowInsecure{ssl_tag}\n"
    f"@V2rayashaq"
)
```

# ─── TELEGRAM ───────────────────────────────────────────────────

def send_to_telegram(cfg: V2Config) -> bool:
if not BOT_TOKEN:
log.error(“BOT_TOKEN not set”)
return False
payload = {
“chat_id”:                  CHAT_ID,
“text”:                     build_message(cfg),
“parse_mode”:               “HTML”,
“disable_web_page_preview”: True,
“reply_markup”: {“inline_keyboard”: [[
{“text”: “Channel”, “url”: “https://t.me/V2rayashaq”},
{“text”: “Admin”,   “url”: f”https://t.me/{ADMIN_USER.lstrip(’@’)}”},
]]}
}
for attempt in range(3):
try:
res = requests.post(
f”https://api.telegram.org/bot{BOT_TOKEN}/sendMessage”,
json=payload, timeout=12
)
if res.status_code == 429:
wait_s = res.json().get(“parameters”, {}).get(“retry_after”, 15)
log.warning(f”Rate limited - sleeping {wait_s}s”)
time.sleep(wait_s)
continue
if res.ok: return True
log.warning(f”Telegram {res.status_code}: {res.text[:80]}”)
return False
except requests.RequestException as e:
log.warning(f”Telegram attempt {attempt+1}/3: {e}”)
time.sleep(3)
return False

# ─── SUBSCRIPTION ───────────────────────────────────────────────

def save_subscription(configs: list) -> None:
top  = configs[:MAX_SUB_CONFIGS]
blob = “\n”.join(c.raw_patched for c in top)
try:
with open(SUB_FILE, “w”, encoding=“utf-8”) as f:
f.write(base64.b64encode(blob.encode()).decode())
log.info(f”Saved {len(top)} configs to {SUB_FILE}”)
except OSError as e:
log.error(f”Cannot write subscription: {e}”)

# ─── MAIN ───────────────────────────────────────────────────────

def main() -> None:
parser = argparse.ArgumentParser()
parser.add_argument(”–dry-run”, action=“store_true”)
args = parser.parse_args()

```
t_start = time.time()
log.info("=" * 55)
log.info("  V2Ray Ultimate Hunter v4 - Ashaq Team")
log.info("  Mode: Empty SNI + Allow Insecure | Self-Evolving")
log.info("=" * 55)

sm = SourceManager()
log.info(f"Sources: {len(sm.get_all_sources())} total "
         f"(base={len(BASE_SOURCES)} learned={len(sm.learned)})")

# 1. Collect empty-SNI configs
raws = collect_configs(sm)
if not raws:
    log.error("Nothing collected - exiting")
    sm.save()
    return

# 2. Pre-sort: CF/VPS hints first
raws.sort(key=lambda x: (
    not any(k in x.lower() for k in CF_KEYWORDS),
    not any(k in x.lower() for k in VPS_KEYWORDS),
))

# 3. Live check
live = run_checks(raws)
if not live:
    log.error("No live configs - exiting")
    sm.save()
    return

# 4. Geo enrich
log.info("Enriching geo data...")
with ThreadPoolExecutor(max_workers=30) as ex:
    live = list(ex.map(enrich, live))

# 5. Sort by score
live.sort(key=lambda c: c.score(), reverse=True)

# 6. Smart post selection:
#    Slot 1: Best SSL config (if any)
#    Slot 2: Best VPS config (non-SSL)
#    Slot 3-4: Top scored remaining
ssl_cfgs  = [c for c in live if c.ssl_ok]
vps_cfgs  = [c for c in live if c.is_vps and not c.ssl_ok]
rest_cfgs = [c for c in live if not c.ssl_ok and not c.is_vps]

posts = []
if ssl_cfgs:
    posts.append(ssl_cfgs[0])
if vps_cfgs and len(posts) < MAX_POSTS:
    posts.append(vps_cfgs[0])
for c in rest_cfgs + live:
    if len(posts) >= MAX_POSTS:
        break
    if c not in posts:
        posts.append(c)
posts = posts[:MAX_POSTS]

ssl_count = sum(1 for c in posts if c.ssl_ok)
vps_count = sum(1 for c in posts if c.is_vps)
log.info(f"Posting {len(posts)} configs | SSL={ssl_count} VPS={vps_count}")

posted = 0
for cfg in posts:
    if args.dry_run:
        log.info(f"[DRY] {cfg.host} ping={cfg.ping_ms}ms ssl={cfg.ssl_ok} vps={cfg.is_vps}")
        posted += 1
    else:
        if send_to_telegram(cfg):
            posted += 1
            log.info(f"Posted {posted}/{MAX_POSTS}: {cfg.host} "
                     f"ping={cfg.ping_ms}ms ssl={cfg.ssl_ok} vps={cfg.is_vps}")
            time.sleep(2)

# 7. Save
save_subscription(live)
sm.save()

elapsed = int(time.time() - t_start)
log.info(f"Done in {elapsed}s | live={len(live)} scanned={len(raws)} posted={posted}")
log.info(f"Learned sources total: {len(sm.learned)}")
```

if **name** == “**main**”:
main()
