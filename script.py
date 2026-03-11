“””
╔══════════════════════════════════════════════════════════════════╗
║        V2RAY ULTIMATE HUNTER v4 — ASHAQ TEAM EDITION           ║
║   2000+ Sources | Auto-Post | Custom SNI | VPS-First | SSL      ║
╚══════════════════════════════════════════════════════════════════╝
HOW TO USE:
Normal run:     python v2ray_hunter.py
Override SNI:   python v2ray_hunter.py –sni speedtest.net
Skip posting:   python v2ray_hunter.py –dry-run
ENV VARS:
BOT_TOKEN  — Telegram bot token (required for posting)
CUSTOM_SNI — SNI domain to inject into all configs
ADMIN_TG   — Telegram admin username
“””
import os, re, ssl, sys, json, time, socket, base64
import logging, threading, argparse, requests
from datetime import datetime, timezone
from dataclasses import dataclass, field   # BUG FIX 1: field was missing
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# LOGGING

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log = logging.getLogger(“V2Hunter”)
log.setLevel(logging.DEBUG)
_fmt = logging.Formatter(”%(asctime)s │ %(levelname)-7s │ %(message)s”, “%H:%M:%S”)
_ch  = logging.StreamHandler(sys.stdout)
_ch.setFormatter(_fmt); _ch.setLevel(logging.INFO)
log.addHandler(_ch)
try:
_fh = logging.FileHandler(“v2ray_hunt.log”, encoding=“utf-8”)
_fh.setFormatter(_fmt); _fh.setLevel(logging.DEBUG)
log.addHandler(_fh)
except Exception:
pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ★ USER SETTINGS

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOT_TOKEN        = os.environ.get(“BOT_TOKEN”, “”)
CHAT_ID          = “@V2rayashaq”
ADMIN_USER       = os.environ.get(“ADMIN_TG”, “@genie_2000”)
SUB_FILE         = “sub_link.txt”
CUSTOM_SNI       = os.environ.get(“CUSTOM_SNI”, “”)
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

# 2000+ SOURCES

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCES: list = [
# BLOCK A — GitHub collectors
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
“https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity_base64.txt”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/mix”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed”,
“https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_Sub.txt”,
“https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_base64_Sub.txt”,
“https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub”,
“https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt”,
“https://raw.githubusercontent.com/freefq/free/master/v2”,
“https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2”,
“https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/All.txt”,
“https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/Vmess.txt”,
“https://raw.githubusercontent.com/Rokate/Proxy-Sub/main/Base64/Vless.txt”,
“https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray”,
“https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/combine/sub.txt”,
“https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free”,
“https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/v2ray/v2raysub”,
“https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription1”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription2”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription3”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription4”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription5”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription6”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription7”,
“https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription8”,
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
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server2.txt”,
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server3.txt”,
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server4.txt”,
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server5.txt”,
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server6.txt”,
“https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server7.txt”,
“https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt”,
“https://raw.githubusercontent.com/IranianCypherpunks/sub/main/config”,
“https://raw.githubusercontent.com/IranianCypherpunks/sub/main/configB64”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/1/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/2/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/3/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/4/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/5/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/6/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/7/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/8/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/9/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/10/config”,
“https://raw.githubusercontent.com/vxiaov/free_proxies/main/v2ray/v2ray.share.txt”,
“https://raw.githubusercontent.com/vxiaov/free_proxies/main/vmess/vmess.share.txt”,
“https://raw.githubusercontent.com/vxiaov/free_proxies/main/vless/vless.share.txt”,
“https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/all_configs.txt”,
“https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/vless_configs.txt”,
“https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/vmess_configs.txt”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/G-Core.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/openai.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/cloudflare.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/NiREvil.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/CF-IPs.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/DigiCloud.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Proton.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/GlobalVPN.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/TurboVPN.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/SkyVPN.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/SVR.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Sentry.md”,
“https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt”,
“https://raw.githubusercontent.com/Surfboardv2ray/v2ray-cf/main/sub”,
“https://raw.githubusercontent.com/Surfboardv2ray/Proxy/main/Raw”,
“https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vless”,
“https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/vmess”,
“https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/subs/v2ray”,
“https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Mix/mix.txt”,
“https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Vmess/vmess.txt”,
“https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/main/sub/Vless/vless.txt”,
“https://raw.githubusercontent.com/snakem982/proxypool/main/vmess.txt”,
“https://raw.githubusercontent.com/snakem982/proxypool/main/vless.txt”,
“https://raw.githubusercontent.com/snakem982/proxypool/main/mix.txt”,
“https://raw.githubusercontent.com/mheidari98/.proxy/main/all”,
“https://raw.githubusercontent.com/mheidari98/.proxy/main/vmess”,
“https://raw.githubusercontent.com/mheidari98/.proxy/main/vless”,
“https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/proxy.txt”,
“https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/mix.txt”,
“https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/vless.txt”,
“https://raw.githubusercontent.com/GFW-knocker/gfw_resist/main/protocols/vmess.txt”,
“https://raw.githubusercontent.com/resasanian/Mirza/main/sub”,
“https://raw.githubusercontent.com/resasanian/Mirza/main/best”,
“https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt”,
“https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_outside_iran.txt”,
“https://raw.githubusercontent.com/ermaozi01/free_clash_vpn/main/subscribe/v2ray.txt”,
“https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/node.txt”,
“https://raw.githubusercontent.com/AliAnonymous/v2configs/main/All/config.txt”,
“https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/merged.txt”,
“https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/vless.txt”,
“https://raw.githubusercontent.com/snail-fly/v2ray-aggregated/main/sub/vmess.txt”,
“https://raw.githubusercontent.com/dimzon/scaling-robot/main/all”,
“https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/mix_base64”,
“https://raw.githubusercontent.com/Ashkan0322/ConfigCollect/main/sub/mix”,
“https://raw.githubusercontent.com/hermansh-id/belajar-script-proxy/main/sub/vmess”,
“https://raw.githubusercontent.com/hermansh-id/belajar-script-proxy/main/sub/vless”,
“https://raw.githubusercontent.com/GalaxyCom2023/v2ray/main/sub”,
“https://raw.githubusercontent.com/GalaxyCom2023/Xray-sub/main/sub”,
“https://raw.githubusercontent.com/free18/v2ray/main/v2ray.txt”,
“https://raw.githubusercontent.com/mganotas/outbound/main/raw.txt”,
“https://raw.githubusercontent.com/mganotas/outbound/main/raw_b64.txt”,
“https://raw.githubusercontent.com/Moli-X/Resources/main/Subscription/Collect.txt”,
“https://raw.githubusercontent.com/FreeVpnSubscriber/FreeVpn/main/v2ray.txt”,
“https://raw.githubusercontent.com/V2Hub/V2Hub.github.io/main/subs/v2ray”,
“https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/default.txt”,
“https://raw.githubusercontent.com/ndsphonemy/proxy-sub/main/speed.txt”,
“https://raw.githubusercontent.com/proxypool404/v2ray/main/all.txt”,
“https://raw.githubusercontent.com/Airscker/V2Ray-Config-Pool/main/all.txt”,
“https://raw.githubusercontent.com/MrHedgehogArmenian/proxy/main/all.txt”,
“https://raw.githubusercontent.com/vpn0/v2ray/main/v2ray.txt”,
“https://raw.githubusercontent.com/VPN-Speed/V2ray-Config/main/sub.txt”,
“https://raw.githubusercontent.com/jason5ng32/MyIP/main/public/v2ray.txt”,
# BLOCK B — Extended sources
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/vless”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/channels/vmess”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/mix”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/vless”,
“https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/vmess”,
“https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/mix”,
“https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/vless”,
“https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/base64/vmess”,
“https://raw.githubusercontent.com/yebekhe/V2Hub/main/sub/normal/mix”,
“https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/mix”,
“https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/vmess”,
“https://raw.githubusercontent.com/yebekhe/configtohub/main/sub/base64/vless”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vmess.txt”,
“https://raw.githubusercontent.com/barry-far/V2ray-Config/main/sub.txt”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Atlas.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Thunder.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Mullvad.md”,
“https://raw.githubusercontent.com/NiREvil/vless/main/sub/Windscribe.md”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/11/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/12/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/13/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/14/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/15/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/20/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/25/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/30/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/40/config”,
“https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/api/50/config”,
“https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Raw”,
“https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Vless”,
“https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Vmess”,
“https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/mixed”,
“https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/vmess”,
“https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/update/vless”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/all2”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vmess”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/type/vless”,
“https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/type/trojan”,
“https://raw.githubusercontent.com/adiwzx/freenode/main/adispeed.txt”,
“https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub2”,
“https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub3”,
“https://raw.githubusercontent.com/free18/v2ray/main/vmess.txt”,
“https://raw.githubusercontent.com/free18/v2ray/main/vless.txt”,
“https://raw.githubusercontent.com/mfuu/v2ray/master/vmess”,
“https://raw.githubusercontent.com/mfuu/v2ray/master/vless”,
“https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/clash.yml”,
“https://raw.githubusercontent.com/vveg26/chromego_merge/main/sub/base64.txt”,
“https://raw.githubusercontent.com/Misaka-blog/chromego_merge/main/sub/base64.txt”,
“https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml”,
“https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/v2ray.txt”,
“https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/vmess.txt”,
“https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o/vless.txt”,
“https://raw.githubusercontent.com/dimzon/scaling-robot/main/vmess”,
“https://raw.githubusercontent.com/dimzon/scaling-robot/main/vless”,
“https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/vmess_Sub.txt”,
“https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/vless_Sub.txt”,
# BLOCK C — Telegram channels
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
“https://t.me/s/v2ray_outlinekey”,
“https://t.me/s/FreeVless”,
“https://t.me/s/freeNodes”,
“https://t.me/s/meli_proxi”,
“https://t.me/s/ShadowProxy66”,
“https://t.me/s/v2ray1_ng”,
“https://t.me/s/VmessProtocol”,
“https://t.me/s/DigiV2ray”,
“https://t.me/s/V2RayTz”,
“https://t.me/s/v2rayen”,
“https://t.me/s/v2ray_collector”,
“https://t.me/s/VlessConfig”,
“https://t.me/s/XrayFreeConfig”,
“https://t.me/s/XrayTunnel”,
“https://t.me/s/DirectVPN”,
“https://t.me/s/freevlesskey”,
“https://t.me/s/frev2rayng”,
“https://t.me/s/v2ray_free_conf”,
“https://t.me/s/vmessconfig”,
“https://t.me/s/freeconfigv2”,
“https://t.me/s/FreeV2ray4u”,
“https://t.me/s/V2ray4Iran”,
“https://t.me/s/iP_CF”,
“https://t.me/s/ConfigsHub”,
“https://t.me/s/v2rayNGn”,
“https://t.me/s/VPN_NAT”,
“https://t.me/s/vlessconfig”,
“https://t.me/s/v2ray_configs_pool”,
“https://t.me/s/VPN_Hell”,
“https://t.me/s/proxy_wars”,
“https://t.me/s/v2rayshop”,
“https://t.me/s/mahsaproxi”,
“https://t.me/s/v2rayngvpn”,
“https://t.me/s/VpnSkyy”,
“https://t.me/s/servervpniran”,
“https://t.me/s/V2RayOxygen”,
“https://t.me/s/v2rayprotocols”,
“https://t.me/s/GetConfig”,
“https://t.me/s/vpnfail_v2ray”,
“https://t.me/s/V2rayNG_Collector”,
“https://t.me/s/Freee_VPN”,
“https://t.me/s/prrooxy”,
“https://t.me/s/v2ray_vpn_ir”,
“https://t.me/s/VpnFail”,
“https://t.me/s/V2RayIranStable”,
“https://t.me/s/GozarVPN”,
“https://t.me/s/v2_configs”,
“https://t.me/s/YANEY_VPN”,
“https://t.me/s/fast_v2ray”,
“https://t.me/s/freenode_v2ray”,
“https://t.me/s/freeconfig4all”,
“https://t.me/s/Hiddify”,
“https://t.me/s/v2rayng_vpn”,
“https://t.me/s/AllProxies”,
“https://t.me/s/IranProxies”,
“https://t.me/s/VPN_Proxy_Free”,
“https://t.me/s/NetworkNinja”,
“https://t.me/s/vpnhat”,
“https://t.me/s/OutlineVpnOfficial”,
“https://t.me/s/v2ray_rules”,
“https://t.me/s/free_shadowsocks_v2ray”,
“https://t.me/s/freev2rayssr”,
“https://t.me/s/v2rayng_v”,
“https://t.me/s/v2rayng_config”,
“https://t.me/s/vmess_vless_free”,
“https://t.me/s/FreeVpnVless”,
“https://t.me/s/freevpnvmess”,
“https://t.me/s/V2rayFreeProxy”,
“https://t.me/s/NightFox_VPN”,
“https://t.me/s/HiddifyNG”,
“https://t.me/s/Hiddify_Configs”,
“https://t.me/s/Sing_Box_Config”,
“https://t.me/s/XrayConfig”,
“https://t.me/s/XrayFree”,
“https://t.me/s/ClashConfig”,
“https://t.me/s/HiddifyConfig”,
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

CONFIG_RE = re.compile(r”(?:vless|vmess)://[^\s#"'<>][]+”)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# DATA MODEL

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class V2Config:
raw:          str
raw_patched:  str
host:         str
port:         int
ping_ms:      int
proto:        str
original_sni: str
active_sni:   str
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# SNI — extract + inject

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

def _inject_vless_sni(raw: str, sni: str) -> str:
replaced, result = False, raw
for k in _SNI_KEYS:
if re.search(rf”[?&]{k}=”, result, re.IGNORECASE):
result = re.sub(rf”([?&]{k}=)[^&\s#]*”, rf”\g<1>{sni}”, result, flags=re.IGNORECASE)
replaced = True
if not replaced:
sep = “&” if “?” in result else “?”
result += f”{sep}sni={sni}&host={sni}”
return result

def _inject_vmess_sni(raw: str, sni: str) -> str:
try:
b64 = raw[len(“vmess://”):]
obj = json.loads(base64.b64decode(b64 + “==” * 3).decode(“utf-8”, errors=“ignore”))
for k in _SNI_KEYS:
if k in obj:
obj[k] = sni
obj[“sni”]  = sni
obj[“host”] = sni
return “vmess://” + base64.b64encode(json.dumps(obj, ensure_ascii=False).encode()).decode()
except Exception:
return raw

def apply_sni(raw: str, custom_sni: str) -> tuple:
orig = extract_sni(raw)
if not custom_sni:
return orig, raw
if raw.startswith(“vmess://”):
return orig, _inject_vmess_sni(raw, custom_sni)
return orig, _inject_vless_sni(raw, custom_sni)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# COLLECT

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _fetch(url: str) -> list:
try:
r = requests.get(url, timeout=FETCH_TIMEOUT, headers={“User-Agent”: “Mozilla/5.0”})
text  = r.text
found = CONFIG_RE.findall(text)
if not found:
try:
decoded = base64.b64decode(text.strip() + “==”).decode(“utf-8”, errors=“ignore”)
found   = CONFIG_RE.findall(decoded)
except Exception:
pass
found = [c for c in found if “:443” in c]
if found:
log.info(f”✓ {len(found):>4} ← {url[:68]}”)
return found
except Exception:
return []

def collect_configs() -> list:
log.info(f”🌐 Fetching from {len(SOURCES)} sources [{FETCH_WORKERS} workers] …”)
all_raw: list = []
with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
for fut in as_completed({ex.submit(_fetch, u): u for u in SOURCES}):
try:
all_raw.extend(fut.result())
except Exception:
pass
unique = list(set(all_raw))
log.info(f”📦 {len(unique)} unique port-443 configs collected”)
return unique

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# TCP PING + SSL

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tcp_ping(host: str, port: int) -> Optional[int]:
try:
t0 = time.perf_counter()
with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT):
return int((time.perf_counter() - t0) * 1000)
except Exception:
return None

def ssl_handshake(host: str, port: int, sni: str) -> tuple:
name = sni or host
ctx  = ssl.create_default_context()
ctx.check_hostname = True
ctx.verify_mode    = ssl.CERT_REQUIRED
try:
with ctx.wrap_socket(
socket.create_connection((host, port), timeout=SSL_TIMEOUT),
server_hostname=name, do_handshake_on_connect=True
) as s:
cert = s.getpeercert() or {}
cn   = next((v for f in cert.get(“subject”, []) for k, v in f if k == “commonName”), “”)
return True, cn
except ssl.SSLCertVerificationError:
pass
except Exception:
return False, “”

```
ctx2 = ssl.create_default_context()
ctx2.check_hostname = False
ctx2.verify_mode    = ssl.CERT_NONE
try:
    with ctx2.wrap_socket(
        socket.create_connection((host, port), timeout=SSL_TIMEOUT),
        server_hostname=name, do_handshake_on_connect=True
    ) as s:
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
```

def check_raw(raw: str) -> Optional[V2Config]:
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
proto = “VLESS” if raw.startswith(“vless://”) else “VMESS”
ping  = tcp_ping(host, port)
if ping is None or ping > MAX_PING_MS:
return None
orig_sni, patched = apply_sni(raw, CUSTOM_SNI)
active_sni        = CUSTOM_SNI if CUSTOM_SNI else (orig_sni or host)
ssl_ok, ssl_cn    = ssl_handshake(host, port, active_sni)
return V2Config(
raw=raw, raw_patched=patched, host=host, port=port,
ping_ms=ping, proto=proto, original_sni=orig_sni,
active_sni=active_sni, ssl_ok=ssl_ok, ssl_cert_cn=ssl_cn
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PARALLEL CHECK + STOP GATE

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_checks(raws: list) -> list:
log.info(f”⚡ Checking {len(raws)} configs [{CHECK_WORKERS} workers | stop at {STOP_AFTER_FOUND}] …”)
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
                    log.info(f"🛑 Stop gate: {STOP_AFTER_FOUND} live configs reached")
log.info(f"✅ {len(live)} live configs")
return live
```

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# GEO ENRICHMENT

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MESSAGE BUILDER

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _ping_bar(ms: int) -> str:
if ms < 80:  return “🟢 Ultra Fast”
if ms < 150: return “🟢 Fast”
if ms < 300: return “🟡 Good”
if ms < 500: return “🟠 Moderate”
return               “🔴 Slow”

def _stars(cfg: V2Config) -> str:
if cfg.is_vps and cfg.ssl_ok and cfg.ping_ms < 150: return “⭐⭐⭐⭐⭐ Elite”
if cfg.is_vps or cfg.ssl_ok:                        return “⭐⭐⭐⭐ Stable”
return                                                      “⭐⭐⭐ Good”

def build_message(cfg: V2Config) -> str:
type_label = (“VPS 🚀” if cfg.is_vps else “Shared”) + (” + CF ⚡” if cfg.is_cf else “”)
ssl_label  = f”✅ Verified (CN: {cfg.ssl_cert_cn})” if cfg.ssl_ok else “⚠️ Self-Signed”
sni_src    = “🔧 Custom” if (CUSTOM_SNI and cfg.active_sni == CUSTOM_SNI) else “📌 Built-in”
sni_line   = f”🔑 <b>SNI:</b> <code>{cfg.active_sni}</code> [{sni_src}]” if cfg.active_sni else “”
return (
f”✨ <b>Ashaq Team — Free V2Ray</b> ✨\n”
f”━━━━━━━━━━━━━━━━━━━━━━\n”
f”🌍 <b>Country:</b> {cfg.country_code} {cfg.country}\n”
f”🔷 <b>Protocol:</b> {cfg.proto}\n”
f”🖥 <b>Type:</b> {type_label}\n”
f”🔒 <b>SSL/TLS:</b> {ssl_label}\n”
f”⚡ <b>Ping:</b> {cfg.ping_ms}ms — {_ping_bar(cfg.ping_ms)}\n”
f”🌐 <b>ISP:</b> {cfg.isp or ‘Unknown’}\n”
f”{sni_line}\n”
f”⭐ <b>Rating:</b> {_stars(cfg)}\n”
f”🔌 <b>Port:</b> 443\n”
f”🕐 <b>Verified:</b> {datetime.now(timezone.utc).strftime(’%Y-%m-%d %H:%M’)} UTC\n”
f”🏷 <b>Tags:</b> #Ashaq_Team #V2Ray #Free443 #{cfg.proto}\n”
f”━━━━━━━━━━━━━━━━━━━━━━\n”
f”<code>{cfg.raw_patched}</code>\n”
f”━━━━━━━━━━━━━━━━━━━━━━\n”
f”👥 @V2rayashaq”
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# TELEGRAM SENDER

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_to_telegram(cfg: V2Config) -> bool:
if not BOT_TOKEN:
log.error(“BOT_TOKEN not set — cannot post”)
return False
payload = {
“chat_id”:                  CHAT_ID,
“text”:                     build_message(cfg),
“parse_mode”:               “HTML”,
“disable_web_page_preview”: True,
“reply_markup”: {“inline_keyboard”: [[
{“text”: “📢 Channel”, “url”: “https://t.me/V2rayashaq”},
{“text”: “👤 Admin”,   “url”: f”https://t.me/{ADMIN_USER.lstrip(’@’)}”},
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
log.warning(f”Rate limited — sleeping {wait_s}s”)
time.sleep(wait_s)
continue
if res.ok: return True
log.warning(f”Telegram {res.status_code}: {res.text[:80]}”)
return False
except requests.RequestException as e:
log.warning(f”Telegram attempt {attempt+1}/3: {e}”)
time.sleep(3)
return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# SUBSCRIPTION FILE

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def save_subscription(configs: list) -> None:
top  = configs[:MAX_SUB_CONFIGS]
blob = “\n”.join(c.raw_patched for c in top)
try:
with open(SUB_FILE, “w”, encoding=“utf-8”) as f:
f.write(base64.b64encode(blob.encode()).decode())
log.info(f”💾 Saved {len(top)} configs → {SUB_FILE}”)
except OSError as e:
log.error(f”Cannot write subscription: {e}”)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAIN

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
parser = argparse.ArgumentParser(description=“V2Ray Ultimate Hunter v4”)
parser.add_argument(”–dry-run”, action=“store_true”, help=“Skip actual Telegram posting”)
parser.add_argument(”–sni”,     default=””,          help=“Set / override CUSTOM_SNI”)
args = parser.parse_args()

```
global CUSTOM_SNI
if args.sni:
    CUSTOM_SNI = args.sni.strip()

t_start = time.time()
log.info("╔══════════════════════════════════════════════════╗")
log.info("║     V2Ray Ultimate Hunter v4 — Ashaq Team        ║")
log.info(f"║  Sources: {len(SOURCES):<6} | Auto-Post | SSL+SNI      ║")
log.info("╚══════════════════════════════════════════════════╝")
log.info(f"🔑 SNI: {CUSTOM_SNI or '(per-config built-in)'}")
if args.dry_run:
    log.info("🚫 Dry-run: Telegram disabled")

# 1. Collect
raws = collect_configs()
if not raws:
    log.error("Nothing collected — exiting"); return

# 2. Pre-sort: CF/VPS hints checked first
raws.sort(key=lambda x: (
    not any(k in x.lower() for k in CF_KEYWORDS),
    not any(k in x.lower() for k in VPS_KEYWORDS),
))

# 3. Check
live = run_checks(raws)
if not live:
    log.error("No live configs — exiting"); return

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
    log.info(f"  {i:>2}. {flags} [{c.ping_ms:>4}ms] {c.country_code} {c.proto} sni={c.active_sni}")

# 7. Auto-post
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
```

if **name** == “**main**”:
main()
