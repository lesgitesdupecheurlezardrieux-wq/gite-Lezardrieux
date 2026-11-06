#!/usr/bin/env python3
"""Fusionne vos calendriers iCal (Booking, Airbnb, Greengo...) en disponibilites.json.

Aucune dépendance : Python 3.8+ suffit.
Les liens iCal (avec leurs jetons) ne sont JAMAIS écrits dans ce fichier : ils sont
lus dans la variable d'environnement ICAL_URLS, un lien par ligne.

Utilisation :
    export ICAL_URLS="https://...
    https://...
    https://..."
    python3 sync_calendrier.py disponibilites.json
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta


def telecharger(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (sync-calendrier)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def lignes(texte):
    """Recolle les lignes pliées du format iCal (celles qui commencent par un espace)."""
    texte = texte.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n[ \t]", "", texte).split("\n")


def lire_date(valeur):
    """Renvoie (date, avait_une_heure). Gère 20260704 et 20260704T150000Z."""
    v = valeur.strip()
    d = datetime.strptime(v[:8], "%Y%m%d").date()
    return d, len(v) > 8


def periodes_ical(texte):
    resultat, event = [], None
    for ligne in lignes(texte):
        if ligne == "BEGIN:VEVENT":
            event = {}
        elif ligne == "END:VEVENT" and event is not None:
            if "DTSTART" in event:
                debut, _ = lire_date(event["DTSTART"])
                if "DTEND" in event:
                    fin, avec_heure = lire_date(event["DTEND"])
                    if avec_heure:
                        fin += timedelta(days=1)
                else:
                    fin = debut + timedelta(days=1)
                if fin <= debut:
                    fin = debut + timedelta(days=1)
                resultat.append((debut, fin))
            event = None
        elif event is not None and ":" in ligne:
            cle, valeur = ligne.split(":", 1)
            event[cle.split(";")[0].upper()] = valeur
    return resultat


def fusionner(periodes):
    """Fusionne uniquement les périodes qui se chevauchent (le jour de rotation reste visible)."""
    fusion = []
    for debut, fin in sorted(periodes):
        if fusion and debut < fusion[-1][1]:
            fusion[-1][1] = max(fusion[-1][1], fin)
        else:
            fusion.append([debut, fin])
    return fusion


def main():
    sortie = sys.argv[1] if len(sys.argv) > 1 else "disponibilites.json"
    urls = [u.strip() for u in os.environ.get("ICAL_URLS", "").splitlines() if u.strip()]
    if not urls:
        sys.exit("Variable ICAL_URLS vide : aucun calendrier à lire.")

    toutes, reussis = [], 0
    for i, url in enumerate(urls, 1):
        try:
            p = periodes_ical(telecharger(url))
            toutes += p
            reussis += 1
            print(f"Calendrier {i}/{len(urls)} : {len(p)} période(s)")
        except Exception as e:  # on n'affiche jamais l'URL (elle contient un jeton)
            print(f"Calendrier {i}/{len(urls)} : échec ({type(e).__name__})")

    # Si un calendrier est injoignable, on ne publie pas une liste incomplète.
    if reussis < len(urls):
        sys.exit("Au moins un calendrier est injoignable : fichier existant conservé.")

    aujourdhui = date.today()
    futures = [(d, f) for d, f in toutes if f > aujourdhui]
    donnees = [{"start": d.isoformat(), "end": f.isoformat()} for d, f in fusionner(futures)]

    with open(sortie, "w", encoding="utf-8") as fh:
        json.dump(donnees, fh, ensure_ascii=False, indent=1)
    print(f"{len(donnees)} période(s) écrite(s) dans {sortie}")


if __name__ == "__main__":
    main()
