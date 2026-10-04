#!/usr/bin/env python3
"""
Descarga los datos públicos de fcf.cat (partidos, clasificación y actas de
la Pirinaica, F.C. A) y los guarda en archivos separados dentro de data/,
cada uno con la misma forma que el endpoint original de fcf.cat.
"""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

GRUP_ID = "58161858"
TEAM_ID = "33048"
BASE = "https://www.fcf.cat/api/competition"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; fcf-sync-bot/1.0)",
    "Accept": "application/json",
}
DATA_DIR = "data"


def get_json(url, retries=3, delay=2):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(delay)
    raise RuntimeError(f"No se pudo descargar {url}: {last_err}")


def write_json(name, data):
    path = os.path.join(DATA_DIR, name)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def main():
    partidos = get_json(f"{BASE}/partidos?grupId={GRUP_ID}")
    classificacio = get_json(f"{BASE}/classificacio?grupId={GRUP_ID}")

    actas = {}
    for _jornada, partidos_jornada in partidos.items():
        if not isinstance(partidos_jornada, list):
            continue
        for p in partidos_jornada:
            casa = str(p.get("CODEQUIPO_CASA", ""))
            fuera = str(p.get("CODEQUIPO_FUERA", ""))
            cerrada = str(p.get("CERRADA", ""))
            codacta = p.get("CODACTA")
            if cerrada == "1" and codacta and (casa == TEAM_ID or fuera == TEAM_ID):
                try:
                    actas[str(codacta)] = get_json(f"{BASE}/acta?codacta={codacta}")
                except RuntimeError as e:
                    print(f"Aviso: no se pudo descargar el acta {codacta}: {e}")

    write_json("partidos.json", partidos)
    write_json("classificacio.json", classificacio)
    write_json("actas.json", actas)
    write_json("meta.json", {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "grupId": GRUP_ID,
        "teamId": TEAM_ID,
    })

    n_partidos = sum(len(v) for v in partidos.values() if isinstance(v, list))
    n_equipos = len(classificacio.get("data", []))
    print(
        f"OK: {n_partidos} partidos, {n_equipos} equipos en clasificación, "
        f"{len(actas)} actas descargadas."
    )


if __name__ == "__main__":
    main()
