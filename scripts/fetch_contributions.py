#!/usr/bin/env python3
"""Baixa o calendário público de contribuições (sem token) e grava data/contributions.json.

Uso:  GH_USER=kauagabr python scripts/fetch_contributions.py
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "kauagabr")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
COUNT_RE = re.compile(r"^(No|\d[\d,]*)\s+contributions?", re.I)


def fetch_days():
    resp = requests.get(
        URL, headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}, timeout=30
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # O número de contribuições de cada dia vem no <tool-tip for="id-da-célula">
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        day = td.get("data-date")
        if not day:
            continue
        level = int(td.get("data-level", 0))
        m = COUNT_RE.match(tips.get(td.get("id"), ""))
        if m:
            count = 0 if m.group(1).lower() == "no" else int(m.group(1).replace(",", ""))
        else:
            count = level  # fallback aproximado se o tooltip não vier
        days.append({"date": day, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # sequência atual: se hoje ainda está zerado, começa a contar de ontem
    i = len(days) - 1
    if i >= 0 and days[i]["count"] == 0:
        i -= 1
    current = 0
    while i >= 0 and days[i]["count"] > 0:
        current += 1
        i -= 1

    best = max(days, key=lambda d: d["count"])
    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main():
    days = fetch_days()
    if len(days) < 300:
        sys.exit(f"Calendário incompleto ({len(days)} dias) — abortando para não sobrescrever.")
    payload = {
        "username": USERNAME,
        "generated_on": date.today().isoformat(),
        "stats": compute_stats(days),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    s = payload["stats"]
    print(
        f"{USERNAME}: {s['total']} contribuições, sequência atual {s['current_streak']}, "
        f"maior {s['longest_streak']} → {OUT}"
    )


if __name__ == "__main__":
    main()
