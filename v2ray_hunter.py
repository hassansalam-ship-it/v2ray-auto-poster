"""
╔══════════════════════════════════════════════════════════════════╗
║       🚀 V2RAY ULTIMATE HUNTER v5 — ASHAQ TEAM EDITION         ║
║   2000+ Sources | Auto-Post | Custom SNI | VPS-First | SSL     ║
║   Anti-Bot Bypass | WS Path /ws | allowInsecure | Force TLS    ║
╚══════════════════════════════════════════════════════════════════╝

HOW TO USE:
  Normal run:           python v2ray_hunter.py
  Override SNI:         python v2ray_hunter.py --sni speedtest.net
  Skip posting:         python v2ray_hunter.py --dry-run

ENV VARS:
  BOT_TOKEN      — Telegram bot token (required for posting)
  CUSTOM_SNI     — SNI domain to inject into all configs
  ADMIN_TG       — Telegram admin username
"""

import os, re, ssl, sys, json, time, socket, base64
import logging, threading, argparse, requests, random, urllib.parse
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
log = logging.getLogger("V2Hunter")
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s │ %(levelname)-7s │ %(message)s", "%H:%M:%S")
_ch  = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt); _ch.setLevel(logging.INFO)
log.addHandler(_ch)
try:
    _fh = logging.FileHandler("v2ray_hunt.log", encoding="utf-8")
    _fh.setFormatter(_fmt); _fh.setLevel(logging.DEBUG)
    log.addHandler(_fh)
except Exception:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANTI-BOT: Rotating User-Agent pool + stealth headers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
]

_ACCEPT_LANGS = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.9,ar;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
]


def _stealth_headers() -> dict:
    """Returns randomized browser-like headers to bypass bot detection."""
    ua = random.choice(_USER_AGENTS)
    is_chrome = "Chrome" in ua and "Edg" not in ua
    is_firefox = "Firefox" in ua
    return {
        "User-Agent":      ua,
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
                           if is_firefox else
                           "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": random.choice(_ACCEPT_LANGS),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest":  "document",
        "Sec-Fetch-Mode":  "navigate",
        "Sec-Fetch-Site":  "none",
        "Sec-Fetch-User":  "?1",
        "Cache-Control":   random.choice(["max-age=0", "no-cache"]),
        **({"Sec-CH-UA": f'"Chromium";v="122", "Google Chrome";v="122", "Not:A-Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"'} if is_chrome else {}),
    }


def _make_session() -> requests.Session:
    """Creates a requests session with retry logic and connection pooling."""
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=200)
    s.mount("https://", adapter)
    s.mount("http://",  adapter)
    return s


# One shared session per thread (thread-local)
_tl = threading.local()

def _session() -> requests.Session:
    if not hasattr(_tl, "sess"):
        _tl.sess = _make_session()
    return _tl.sess


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
CHAT_ID    = "@V2rayashaq"
ADMIN_USER = os.environ.get("ADMIN_TG", "@genie_2000")
SUB_FILE   = "sub_link.txt"

# Set your custom SNI here OR pass --sni on command line
# Leave "" to use each config's built-in SNI
CUSTOM_SNI = os.environ.get("CUSTOM_SNI", "")

MAX_POSTS        = 5
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
#  TARGET BUG HOSTS — هوستات إلزامية لاختبار التوافق مع شبكات الموردين
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# كل سيرفر ناجح يُختبر مع هذه الهوستات عبر SSL Handshake حقيقي.
# السيرفرات التي تجتاز أكثر هوستات تحصل على أعلى تقييم.
TARGET_HOSTS: dict[str, list[str]] = {
    # ── Voxi Core (Vodafone UK) ───────────────────────────────────
    "voxi": [
        "downloads.vodafone.co.uk",
    ],
    # ── Oodi Matrix (سيرفرات تدعم CDN متعدد) ──────────────────────
    "oodi": [
        "m.tiktok.com",
        "www.snapchat.com",
        "m.instagram.com",
        "m.facebook.com",
        "m.youtube.com",
        "web.telegram.org",
        "web.whatsapp.com",
    ],
    # ── Zain Pulse (الاعتماد الكلي على TikTok) ────────────────────
    "zain": [
        "m.tiktok.com",
    ],
}

# قائمة مسطّحة لجميع الهوستات الفريدة (لتجنب التكرار في الاختبار)
ALL_TARGET_HOSTS: list[str] = list(dict.fromkeys(
    h for hosts in TARGET_HOSTS.values() for h in hosts
))

# عدد الهوستات المطلوبة كحد أدنى لاعتبار السيرفر "متوافقاً"
MIN_COMPAT_HOSTS = 1   # ← غيّر لـ 2 أو 3 لتصفية أشد


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

VPS_KEYWORDS = [
    "oracle", "google", "amazon", "aws", "digitalocean", "hetzner", "ovh",
    "linode", "vultr", "azure", "contabo", "alibaba", "tencent", "rackspace",
    "leaseweb", "choopa", "quadranet", "frantech", "datacamp", "incapsula",
    "cloudflare", "fastly", "akamai", "cdn77", "stackpath", "clouvider",
    "hostwinds", "liquidweb", "vps", "datacenter", "hosting",
]
CF_KEYWORDS = [
    "cloudfront", "cdn", "worker", "pages.dev", "nodes.com",
    "cloudflare", "cfcdn", "cfip", "104.", "172.64.", "172.65.",
    "172.66.", "172.67.", "162.158.", "198.41.",
]

CONFIG_RE = re.compile(r"(?:vless|vmess)://[^\s#\"\'<>\]\[]+")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dataclass
class V2Config:
    raw:              str
    raw_patched:      str
    host:             str
    port:             int
    ping_ms:          int
    proto:            str
    original_sni:     str
    active_sni:       str
    ssl_ok:           bool       = False
    ssl_cert_cn:      str        = ""
    country_code:     str        = "??"
    country:          str        = "Unknown"
    isp:              str        = ""
    is_vps:           bool       = False
    is_cf:            bool       = False
    compatible_hosts: list       = None   # الهوستات التي اجتازت SSL معها

    def __post_init__(self):
        if self.compatible_hosts is None:
            self.compatible_hosts = []

    def score(self) -> int:
        s  = 600 if self.is_vps else 0
        s += 400 if self.is_cf  else 0
        s += 200 if self.ssl_ok else 0

        # ── مكافأة الهوستات المتوافقة (الأهم في النظام الجديد) ────
        # كل هوست Oodi/Zain ناجح = +800 نقطة
        oodi_zain = set(TARGET_HOSTS["oodi"]) | set(TARGET_HOSTS["zain"])
        compat_set = set(self.compatible_hosts)
        oodi_hits  = len(compat_set & oodi_zain)
        voxi_hits  = len(compat_set & set(TARGET_HOSTS["voxi"]))
        s += oodi_hits  * 800   # كل هوست Oodi/Zain يجتاز = +800
        s += voxi_hits  * 600   # كل هوست Voxi يجتاز     = +600

        # ── مكافأة السرعة العدوانية ────────────────────────────────
        # تحت 150ms = +800، تحت 300ms = +400، وإلا تناقص تدريجي
        if   self.ping_ms < 80:   s += 800
        elif self.ping_ms < 150:  s += 600
        elif self.ping_ms < 300:  s += 400
        elif self.ping_ms < 450:  s += 200
        else:                     s += max(0, 600 - self.ping_ms)

        return s


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SNI — extract + inject
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_SNI_KEYS = ("sni", "host", "peer", "servername", "server-name")


def _extract_vless_sni(raw: str) -> str:
    for k in _SNI_KEYS:
        m = re.search(rf"[?&]{k}=([^&\s#]+)", raw, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _extract_vmess_sni(raw: str) -> str:
    try:
        b64 = raw[len("vmess://"):]
        obj = json.loads(base64.b64decode(b64 + "==" * 3).decode("utf-8", errors="ignore"))
        for k in _SNI_KEYS:
            if obj.get(k):
                return str(obj[k])
    except Exception:
        pass
    return ""


def extract_sni(raw: str) -> str:
    return _extract_vmess_sni(raw) if raw.startswith("vmess://") else _extract_vless_sni(raw)


def _inject_vless_sni(raw: str, sni: str) -> str:
    """
    VLESS patching — الهدف النهائي للرابط الخارج:
      • sni=, peer=, servername=, server-name= → تُفرَّغ إن وُجدت، لا تُضاف إن لم تكن موجودة
      • host= → تُفرَّغ إن وُجدت، لا تُضاف إن لم تكن موجودة
      • path=%2Fws  → مُرمَّز URL (يحل مشكلة "0 Configs Imported" على التطبيقات)
      • type=ws     → WebSocket إلزامي
      • allowInsecure=1 → لتجاوز فحص الشهادة
    المستخدم يضع SNI يدوياً في التطبيق بعد الاستيراد.
    """
    result = raw

    # ── تفريغ حقول SNI (فقط إن وُجدت — لا تُضاف حقول جديدة) ────
    for k in ("sni", "peer", "servername", "server-name"):
        if re.search(rf"[?&]{k}=", result, re.IGNORECASE):
            result = re.sub(
                rf"([?&]{k}=)[^&\s#]*",
                r"\g<1>",   # تفريغ تام
                result,
                flags=re.IGNORECASE,
            )

    # host — تفريغ فقط إن وُجد
    if re.search(r"[?&]host=", result, re.IGNORECASE):
        result = re.sub(
            r"([?&]host=)[^&\s#]*",
            r"\g<1>",   # تفريغ تام
            result,
            flags=re.IGNORECASE,
        )

    # ── path=%2Fws (URL-encoded — يحل مشكلة "0 Configs Imported") ─
    if re.search(r"[?&]path=", result, re.IGNORECASE):
        result = re.sub(r"([?&]path=)[^&\s#]*", r"\g<1>%2Fws", result, flags=re.IGNORECASE)
    else:
        result += "&path=%2Fws"

    # ── type=ws ───────────────────────────────────────────────────
    if re.search(r"[?&]type=", result, re.IGNORECASE):
        result = re.sub(r"([?&]type=)[^&\s#]*", r"\g<1>ws", result, flags=re.IGNORECASE)
    else:
        result += "&type=ws"

    # ── allowInsecure=1 ───────────────────────────────────────────
    if re.search(r"[?&]allowInsecure=", result, re.IGNORECASE):
        result = re.sub(r"([?&]allowInsecure=)[^&\s#]*", r"\g<1>1", result, flags=re.IGNORECASE)
    else:
        result += "&allowInsecure=1"

    return result

    return result


def _inject_vmess_sni(raw: str, sni: str) -> str:
    """
    VMESS patching — 5 fixes applied inside the JSON:
      Fix 1:   Robust base64 decode (tries 4 padding variants).
      Fix 2:   CLEARS sni="" and host="" — no built-in SNI leaks.
               User sets their own SNI in the app after import.
      Fix 3:   Forces net=ws and path=/ws (WebSocket transport).
      Fix 4:   Forces tls=tls (enable TLS encryption).
      Fix 5:   Forces allowInsecure=True + skip-cert-verify=True
               so custom SNI works with any certificate.
      All other original fields (uuid, address, port…) are preserved.
    """
    try:
        b64 = raw[len("vmess://"):]

        # ── Fix 1: Robust base64 decode (4 padding variants) ──────
        obj = None
        for pad in ("", "=", "==", "==="):
            try:
                decoded = base64.b64decode(b64 + pad).decode("utf-8", errors="ignore")
                obj = json.loads(decoded)
                break
            except Exception:
                continue
        if obj is None:
            return raw  # cannot decode — return unchanged

        # ── Fix 2: Clear SNI and Host completely ──────────────────
        obj["sni"]  = ""   # empty → app uses user's own SNI setting
        obj["host"] = ""   # empty CDN host header — no leaks

        # Also clear any other sni-related fields that may exist
        for k in ("peer", "servername", "server-name"):
            if k in obj:
                obj[k] = ""

        # ── Fix 3: Force WebSocket transport ──────────────────────
        obj["net"]  = "ws"
        obj["path"] = "/ws"

        # ── Fix 4: Force TLS ──────────────────────────────────────
        obj["tls"]  = "tls"

        # ── Fix 5: Allow insecure / skip cert verification ────────
        obj["allowInsecure"]    = True   # v2rayNG / Hiddify / NekoBox
        obj["skip-cert-verify"] = True   # Clash / Mihomo / Stash

        # ── Re-encode: compact JSON → base64 ──────────────────────
        new_json = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        new_b64  = base64.b64encode(new_json.encode()).decode()
        return f"vmess://{new_b64}"

    except Exception:
        return raw   # if anything fails, return original unchanged


def apply_sni(raw: str, custom_sni: str) -> tuple[str, str]:
    """
    تُطبَّق التعديلات دائماً بغض النظر عن وجود CUSTOM_SNI أم لا:
      - دائماً تُمرَّر "" للدالتين → تفريغ SNI/host تماماً
      - path=%2Fws و type=ws و allowInsecure تُطبَّق دائماً
      - المستخدم يضع SNI يدوياً في التطبيق بعد الاستيراد
    """
    orig = extract_sni(raw)
    # دائماً نمرر "" لتفريغ الحقول — apply fixes regardless of CUSTOM_SNI
    if raw.startswith("vmess://"):
        return orig, _inject_vmess_sni(raw, "")
    return orig, _inject_vless_sni(raw, "")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _fetch(url: str) -> list[str]:
    """
    Fetch configs from a single source with full anti-bot bypass:
    - Rotating User-Agent + browser headers
    - Persistent session with retry
    - Handles base64, plain text, YAML/clash format
    - Special handling for t.me Telegram pages (scrapes code blocks)
    - Respects Cloudflare rate-limit headers
    - Random delay jitter to avoid fingerprinting
    """
    try:
        # Small random jitter to stagger parallel requests
        time.sleep(random.uniform(0.05, 0.35))

        sess = _session()
        headers = _stealth_headers()

        # Telegram needs special referrer to avoid redirect
        if "t.me/s/" in url:
            headers["Referer"] = "https://t.me/"
            headers["X-Requested-With"] = "XMLHttpRequest"

        r = sess.get(url, timeout=FETCH_TIMEOUT, headers=headers,
                     allow_redirects=True, stream=False)

        # Cloudflare / rate-limit — back off and retry once
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 5))
            time.sleep(min(wait, 10))
            r = sess.get(url, timeout=FETCH_TIMEOUT, headers=_stealth_headers(),
                         allow_redirects=True)

        if r.status_code not in (200, 206):
            return []

        text = r.text

        # ── Try plain regex first ──────────────────────────────────
        found = CONFIG_RE.findall(text)

        # ── Try base64 decode if no configs found ──────────────────
        if not found:
            try:
                # Strip whitespace and try multiple paddings
                b64_clean = re.sub(r"\s+", "", text)
                for pad in ("", "=", "=="):
                    try:
                        decoded = base64.b64decode(b64_clean + pad).decode("utf-8", errors="ignore")
                        found = CONFIG_RE.findall(decoded)
                        if found:
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        # ── Try line-by-line base64 (subscription format) ─────────
        if not found:
            for line in text.splitlines():
                line = line.strip()
                if len(line) > 20 and not line.startswith(("vless://", "vmess://")):
                    try:
                        dec = base64.b64decode(line + "==").decode("utf-8", errors="ignore")
                        found.extend(CONFIG_RE.findall(dec))
                    except Exception:
                        pass

        # ── Telegram: extract from <code> blocks and message text ──
        if not found and "t.me" in url:
            # Remove HTML tags and decode HTML entities
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = clean.replace("&amp;", "&").replace("&#43;", "+").replace(
                "&#61;", "=").replace("%3A", ":").replace("%2F", "/")
            found = CONFIG_RE.findall(clean)

        # ── Filter: only port 443 ──────────────────────────────────
        found = [c for c in found if ":443" in c]

        # Deduplicate within this source
        found = list(dict.fromkeys(found))

        if found:
            log.info(f"✓ {len(found):>4}  ←  {url[:68]}")
        return found

    except requests.exceptions.SSLError:
        # Retry without SSL verification for self-signed sources
        try:
            r2 = requests.get(url, timeout=FETCH_TIMEOUT,
                              headers=_stealth_headers(), verify=False)
            found = CONFIG_RE.findall(r2.text)
            found = [c for c in found if ":443" in c]
            return list(dict.fromkeys(found))
        except Exception:
            return []
    except Exception:
        return []


def collect_configs() -> list[str]:
    log.info(f"🌐 Fetching from {len(SOURCES)} sources [{FETCH_WORKERS} workers] …")
    # Shuffle so if we hit limits, different sources get priority each run
    shuffled = SOURCES[:]
    random.shuffle(shuffled)
    all_raw: list[str] = []
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        for fut in as_completed({ex.submit(_fetch, u): u for u in shuffled}):
            try:
                all_raw.extend(fut.result())
            except Exception:
                pass
    unique = list(dict.fromkeys(all_raw))  # dict.fromkeys preserves order + dedupes faster
    log.info(f"📦 {len(unique)} unique port-443 configs collected (from {len(all_raw)} total)")
    return unique


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TCP PING + SSL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def tcp_ping(host: str, port: int) -> Optional[int]:
    try:
        t0 = time.perf_counter()
        with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT):
            return int((time.perf_counter() - t0) * 1000)
    except Exception:
        return None


def ssl_handshake(host: str, port: int, sni: str) -> tuple[bool, str]:
    name = sni or host
    ctx  = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode    = ssl.CERT_REQUIRED
    try:
        with ctx.wrap_socket(socket.create_connection((host, port), timeout=SSL_TIMEOUT),
                             server_hostname=name, do_handshake_on_connect=True) as s:
            cert = s.getpeercert() or {}
            cn   = next((v for f in cert.get("subject", []) for k, v in f if k == "commonName"), "")
            return True, cn
    except ssl.SSLCertVerificationError:
        pass
    except Exception:
        return False, ""
    ctx2 = ssl.create_default_context()
    ctx2.check_hostname = False
    ctx2.verify_mode    = ssl.CERT_NONE
    try:
        with ctx2.wrap_socket(socket.create_connection((host, port), timeout=SSL_TIMEOUT),
                              server_hostname=name, do_handshake_on_connect=True) as s:
            der = s.getpeercert(binary_form=True) or b""
            cn  = ""
            if der:
                try:
                    m = re.search(r"CN\s*=\s*([^\n,/]+)", ssl.DER_cert_to_PEM_cert(der))
                    if m: cn = m.group(1).strip()
                except Exception:
                    pass
            return False, cn
    except Exception:
        return False, ""


def multi_sni_check(host: str, port: int) -> list[str]:
    """
    يختبر السيرفر مع كل هوست من TARGET_HOSTS عبر SSL Handshake حقيقي.
    يعيد قائمة الهوستات التي نجح معها الاتصال.

    هذا هو قلب نظام "Zero-Data Filtering":
      - السيرفر الذي يقبل SNI = m.tiktok.com → يعمل مع Zain/Oodi ✅
      - السيرفر الذي يرفضها كلها → Downlink = 0B في التطبيق ❌

    ملاحظة: نستخدم CERT_NONE دائماً لأن الهوست المحقون (m.tiktok.com)
    لن يطابق شهادة السيرفر الأصلية — هذا متوقع ومقبول.
    """
    passed: list[str] = []
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE

    for bug_host in ALL_TARGET_HOSTS:
        try:
            conn = socket.create_connection((host, port), timeout=SSL_TIMEOUT)
            with ctx.wrap_socket(conn, server_hostname=bug_host,
                                 do_handshake_on_connect=True):
                passed.append(bug_host)
                log.debug(f"  ✅ {host} ← SNI={bug_host}")
        except Exception as e:
            log.debug(f"  ❌ {host} ← SNI={bug_host}: {type(e).__name__}")

    return passed


def check_raw(raw: str) -> Optional[V2Config]:
    m = re.search(r"@([^:/\s\]#]+):(\d+)", raw)
    if not m:
        return None
    host = m.group(1)
    try:
        port = int(m.group(2))
    except ValueError:
        return None
    if port != TARGET_PORT:
        return None

    proto = "VLESS" if raw.startswith("vless://") else "VMESS"

    # ── 1. TCP Ping (بوابة سريعة) ──────────────────────────────────
    ping = tcp_ping(host, port)
    if ping is None or ping > MAX_PING_MS:
        return None

    # ── 2. SNI patching ────────────────────────────────────────────
    orig_sni, patched = apply_sni(raw, CUSTOM_SNI)
    active_sni        = CUSTOM_SNI if CUSTOM_SNI else (orig_sni or host)

    # ── 3. SSL Handshake مع الهوست الأصلي ──────────────────────────
    ssl_ok, ssl_cn = ssl_handshake(host, port, active_sni)

    # ── 4. Zero-Data Filtering: اختبار الهوستات الإلزامية ──────────
    # هذا هو الفارق الحقيقي بين "CONNECTED 0B" و"CONNECTED 3.3KB+":
    # نختبر SSL مع كل هوست من قائمة Oodi/Zain/Voxi —
    # السيرفر الذي يقبل SNI مثل m.tiktok.com سيمر ترافيك فعلي.
    compat_hosts = multi_sni_check(host, port)

    # ── 5. تصفية Zero-Data: يجب اجتياز حد أدنى من الهوستات ─────────
    if len(compat_hosts) < MIN_COMPAT_HOSTS:
        log.debug(f"⛔ Zero-Data filter: {host} passed {len(compat_hosts)}/{len(ALL_TARGET_HOSTS)} hosts")
        return None

    log.debug(f"✅ {host} | ping={ping}ms | compat={compat_hosts}")

    return V2Config(
        raw=raw, raw_patched=patched, host=host, port=port,
        ping_ms=ping, proto=proto, original_sni=orig_sni,
        active_sni=active_sni, ssl_ok=ssl_ok, ssl_cert_cn=ssl_cn,
        compatible_hosts=compat_hosts,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PARALLEL CHECK + STOP GATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def run_checks(raws: list[str]) -> list[V2Config]:
    log.info(f"⚡ Checking {len(raws)} configs [{CHECK_WORKERS} workers | stop at {STOP_AFTER_FOUND}] …")
    live: list[V2Config] = []
    stop = threading.Event()
    lock = threading.Lock()

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
                        log.info(f"🛑 Stop gate: {STOP_AFTER_FOUND} live configs reached")
    log.info(f"✅ {len(live)} live configs")
    return live


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GEO ENRICHMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_geo: dict[str, tuple] = {}
_glock = threading.Lock()


def get_geo(ip: str) -> tuple[str, str, str]:
    with _glock:
        if ip in _geo: return _geo[ip]
    # Try primary then backup geo API
    for geo_url in [
        f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp",
        f"https://ipapi.co/{ip}/json/",
    ]:
        try:
            r = _session().get(geo_url, timeout=3, headers=_stealth_headers()).json()
            if r.get("status") == "success" or r.get("country_code"):
                result = (
                    r.get("countryCode") or r.get("country_code", "??"),
                    r.get("country", "Unknown"),
                    r.get("isp") or r.get("org", ""),
                )
                with _glock:
                    _geo[ip] = result
                return result
        except Exception:
            continue
    result = ("??", "Unknown", "")
    with _glock:
        _geo[ip] = result
    return result


def enrich(cfg: V2Config) -> V2Config:
    try:
        ip = socket.gethostbyname(cfg.host)
        cfg.country_code, cfg.country, cfg.isp = get_geo(ip)
    except Exception:
        pass
    low = (cfg.raw + cfg.host + cfg.isp).lower()
    cfg.is_cf  = any(k in low for k in CF_KEYWORDS)
    cfg.is_vps = any(k in low for k in VPS_KEYWORDS)
    return cfg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MESSAGE BUILDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _ping_bar(ms: int) -> str:
    if ms < 80:   return "🟢 Ultra Fast"
    if ms < 150:  return "🟢 Fast"
    if ms < 300:  return "🟡 Good"
    if ms < 500:  return "🟠 Moderate"
    return              "🔴 Slow"

def _stars(cfg: V2Config) -> str:
    oodi_zain = set(TARGET_HOSTS["oodi"]) | set(TARGET_HOSTS["zain"])
    compat_set = set(cfg.compatible_hosts)
    oodi_count = len(compat_set & oodi_zain)
    voxi_count = len(compat_set & set(TARGET_HOSTS["voxi"]))
    total = oodi_count + voxi_count

    if total >= 5 and cfg.ping_ms < 150: return "⭐⭐⭐⭐⭐ Elite"
    if total >= 3 or (cfg.is_vps and cfg.ssl_ok): return "⭐⭐⭐⭐ Stable"
    if total >= 1: return "⭐⭐⭐ Compatible"
    return "⭐⭐ Basic"

def _compat_line(cfg: V2Config) -> str:
    """يبني سطر الهوستات المتوافقة مع أيقونات الشبكات."""
    if not cfg.compatible_hosts:
        return "🔌 <b>Compatible:</b> —"

    voxi_set = set(TARGET_HOSTS["voxi"])
    oodi_set = set(TARGET_HOSTS["oodi"])
    zain_set = set(TARGET_HOSTS["zain"])
    compat   = set(cfg.compatible_hosts)

    tags = []
    if compat & voxi_set:  tags.append("📶 Voxi")
    if compat & zain_set:  tags.append("📶 Zain")
    if compat & oodi_set:  tags.append("📶 Oodi")

    # عرض الهوستات الناجحة (مختصر)
    hosts_short = " · ".join(
        h.replace("m.", "").replace("www.", "").replace("web.", "").split(".")[0]
        for h in cfg.compatible_hosts[:5]
    )
    suffix = f" (+{len(cfg.compatible_hosts)-5})" if len(cfg.compatible_hosts) > 5 else ""

    ops = "  ".join(tags) if tags else "—"
    return (
        f"📡 <b>Networks:</b> {ops}\n"
        f"🌐 <b>Bug Hosts:</b> <code>{hosts_short}{suffix}</code>"
    )

def build_message(cfg: V2Config) -> str:
    type_label = ("VPS 🚀" if cfg.is_vps else "Shared") + (" + CF ⚡" if cfg.is_cf else "")
    ssl_label  = f"✅ Verified (CN: {cfg.ssl_cert_cn})" if cfg.ssl_ok else "⚠️ Self-Signed / Insecure"
    sni_src    = "✏️ Custom" if (CUSTOM_SNI and cfg.active_sni == CUSTOM_SNI) else "📄 Built-in"
    sni_line   = f"🔑 <b>SNI:</b> <code>{cfg.active_sni}</code>  [{sni_src}]" if cfg.active_sni else "🔑 <b>SNI:</b> — (set manually)"
    return (
        f"✨ <b>Ashaq Team — Free V2Ray</b> ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 <b>Country:</b> {cfg.country_code}  {cfg.country}\n"
        f"🔹 <b>Protocol:</b> {cfg.proto}\n"
        f"🏢 <b>Type:</b> {type_label}\n"
        f"🔒 <b>SSL/TLS:</b> {ssl_label}\n"
        f"⚡ <b>Ping:</b> {cfg.ping_ms}ms — {_ping_bar(cfg.ping_ms)}\n"
        f"🌐 <b>ISP:</b> {cfg.isp or 'Unknown'}\n"
        f"{sni_line}\n"
        f"{_compat_line(cfg)}\n"
        f"⭐ <b>Rating:</b> {_stars(cfg)}\n"
        f"🔌 <b>Port:</b> 443  |  🛤 <b>Path:</b> /ws\n"
        f"🕒 <b>Verified:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"🏷 <b>Tags:</b> #Ashaq_Team #V2Ray #Free443 #{cfg.proto}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>{cfg.raw_patched}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 @V2rayashaq"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TELEGRAM SENDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def send_to_telegram(cfg: V2Config) -> bool:
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set — cannot post")
        return False
    payload = {
        "chat_id":                  CHAT_ID,
        "text":                     build_message(cfg),
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
        "reply_markup": {"inline_keyboard": [[
            {"text": "📢 Channel", "url": "https://t.me/V2rayashaq"},
            {"text": "👤 Admin",   "url": f"https://t.me/{ADMIN_USER.lstrip('@')}"},
        ]]}
    }
    for attempt in range(3):
        try:
            res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                json=payload, timeout=12)
            if res.status_code == 429:
                wait_s = res.json().get("parameters", {}).get("retry_after", 15)
                log.warning(f"Rate limited — sleeping {wait_s}s")
                time.sleep(wait_s)
                continue
            if res.ok: return True
            log.warning(f"Telegram {res.status_code}: {res.text[:80]}")
            return False
        except requests.RequestException as e:
            log.warning(f"Telegram attempt {attempt+1}/3: {e}")
            time.sleep(3)
    return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SUBSCRIPTION FILE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def save_subscription(configs: list[V2Config]) -> None:
    top  = configs[:MAX_SUB_CONFIGS]
    blob = "\n".join(c.raw_patched for c in top)
    try:
        with open(SUB_FILE, "w", encoding="utf-8") as f:
            f.write(base64.b64encode(blob.encode()).decode())
        log.info(f"💾 Saved {len(top)} configs → {SUB_FILE}")
    except OSError as e:
        log.error(f"Cannot write subscription: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main() -> None:
    parser = argparse.ArgumentParser(description="V2Ray Ultimate Hunter v5")
    parser.add_argument("--dry-run",  action="store_true", help="Skip actual Telegram posting")
    parser.add_argument("--sni",      default="", help="Set / override CUSTOM_SNI")
    args = parser.parse_args()

    global CUSTOM_SNI

    if args.sni:
        CUSTOM_SNI = args.sni.strip()

    t_start = time.time()
    log.info("╔══════════════════════════════════════════════════╗")
    log.info("║  🚀 V2Ray Ultimate Hunter v5 — Ashaq Team        ║")
    log.info(f"║  📡 Sources: {len(SOURCES):<6} | Auto-Post | SSL+WS        ║")
    log.info("╚══════════════════════════════════════════════════╝")
    log.info(f"🔑 CUSTOM_SNI : {CUSTOM_SNI or '(not set — SNI fields cleared)'}")
    if args.dry_run:
        log.info("🔇 Dry-run: Telegram disabled")

    # 1. Collect
    raws = collect_configs()
    if not raws:
        log.error("Nothing collected — exiting")
        return

    # 2. Pre-sort: CF/VPS hints checked first
    raws.sort(key=lambda x: (
        not any(k in x.lower() for k in CF_KEYWORDS),
        not any(k in x.lower() for k in VPS_KEYWORDS),
    ))

    # 3. Check
    live = run_checks(raws)
    if not live:
        log.error("No live configs — exiting")
        return

    # 4. Geo enrich
    log.info("🔍 Enriching …")
    with ThreadPoolExecutor(max_workers=30) as ex:
        live = list(ex.map(enrich, live))

    # 5. Sort by score
    live.sort(key=lambda c: c.score(), reverse=True)

    # 6. Top-10 summary
    log.info("\n📊 Top 10:")
    for i, c in enumerate(live[:10], 1):
        flags = ("🚀" if c.is_vps else "  ") + ("⚡" if c.is_cf else "  ") + ("🔒" if c.ssl_ok else "  ")
        compat_str = f"hosts={len(c.compatible_hosts)}/{len(ALL_TARGET_HOSTS)}"
        log.info(f"  {i:>2}. {flags} [{c.ping_ms:>4}ms] {c.country_code} {c.proto} {compat_str} {c.host[:30]}")

    # 7. Auto-post (no preview)
    posted = 0
    for cfg in live:
        if posted >= MAX_POSTS:
            break
        if args.dry_run:
            log.info(f"[DRY-RUN] {cfg.host} ({cfg.ping_ms}ms) sni={cfg.active_sni}")
            posted += 1
        else:
            if send_to_telegram(cfg):
                posted += 1
                log.info(f"📨 Posted {posted}/{MAX_POSTS}: {cfg.host} ({cfg.ping_ms}ms)")
                time.sleep(2)

    # 8. Save subscription
    save_subscription(live)

    elapsed = int(time.time() - t_start)
    log.info(f"\n🏁 Done in {elapsed}s — {len(live)} live / {len(raws)} scanned / {posted} posted")


if __name__ == "__main__":
    main()
