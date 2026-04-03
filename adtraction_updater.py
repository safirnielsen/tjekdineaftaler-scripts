#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.error
from datetime import date, timedelta

TOKEN = os.environ.get("ADTRACTION_TOKEN", "C9FF5AF00AC8F14025B0E8B78EAD9CADD5F3FA8A")
MARKET = 22
BASE = "https://api.adtraction.net"

CHANNELS = {
    "2056923302": "Mobilabonnement",
    "2057435403": "Kanal 2",
}

def api(path, params=None):
    url = f"{BASE}{path}?token={TOKEN}"
    if params:
        url += "".join(f"&{k}={v}" for k, v in params.items())
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"  HTTP {e.code}: {body}")
        return []
    except Exception as e:
        print(f"  Fejl: {e}")
        return []

def get_programs(channel_id):
    # Prøv v3 med marketId som query param
    data = api("/v3/partner/programs/", {"channelId": channel_id, "marketId": MARKET})
    if not data:
        # Prøv v2
        data = api("/v2/partner/programs/", {"channelId": channel_id, "marketId": MARKET})
    return [p for p in (data or []) if p.get("approvalStatus") == 1]

def get_stats(channel_id, from_dt, to_dt):
    data = api("/v3/partner/statistics/", {
        "channelId": channel_id, "fromDate": from_dt, "toDate": to_dt, "marketId": MARKET
    })
    if not data:
        data = api("/v2/partner/statistics/", {
            "channelId": channel_id, "fromDate": from_dt, "toDate": to_dt, "marketId": MARKET
        })
    return data or []

def run_channel(channel_id, label):
    print(f"\n{'='*60}")
    print(f"  {label}  (Channel ID: {channel_id})")
    print(f"{'='*60}")
    progs = get_programs(channel_id)
    if progs:
        print(f"  Aktive programmer ({len(progs)}):")
        for p in progs:
            print(f"    - {p.get('programName','?'):<30} ID: {p.get('programId','?')}")
    else:
        print("  Ingen aktive programmer")
    today = date.today()
    from_dt = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    to_dt = today.strftime("%Y-%m-%d")
    stats = get_stats(channel_id, from_dt, to_dt)
    print(f"\n  Statistik seneste 30 dage ({from_dt} til {to_dt}):")
    if not stats:
        print("  Ingen data")
        return
    print(f"  {'Program':<28} {'Klik':>8} {'Konv.':>8} {'Kommission':>14}")
    print(f"  {'-'*60}")
    totals = [0, 0, 0.0]
    for s in sorted(stats, key=lambda x: x.get("clicks", 0), reverse=True):
        name = s.get("programName", "?")[:26]
        clicks = s.get("clicks", 0)
        conv = s.get("approved", 0) + s.get("pending", 0)
        comm = s.get("approvedCommission", 0) + s.get("pendingCommission", 0)
        totals[0] += clicks; totals[1] += conv; totals[2] += comm
        print(f"  {name:<28} {clicks:>8} {conv:>8} {comm:>12.2f} kr")
    print(f"  {'-'*60}")
    print(f"  {'TOTAL':<28} {totals[0]:>8} {totals[1]:>8} {totals[2]:>12.2f} kr")
    if totals[0] > 0:
        print(f"\n  Konverteringsrate: {totals[1]/totals[0]*100:.1f}%")

if __name__ == "__main__":
    print(f"Adtraction rapport -- {date.today()}")
    for cid, label in CHANNELS.items():
        run_channel(cid, label)
    print(f"\nFaerdig.")
