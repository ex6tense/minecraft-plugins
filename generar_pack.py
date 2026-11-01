#!/usr/bin/env python3
"""Genera el modpack (.mrpack) de los jugadores: Fabric + mods de cliente + el servidor ya añadido."""
import argparse
import io
import json
import os
import struct
import time
import urllib.parse
import zipfile

from actualizar import get

MODS = ["fabric-api", "simple-voice-chat", "sodium"]
SERVIDOR = ("Servidor ex6tense", "mc.ex6tenseiscool.co.in")


def loader_fabric(mc):
    d = json.loads(get(f"https://meta.fabricmc.net/v2/versions/loader/{mc}"))
    return next(x["loader"]["version"] for x in d if x["loader"]["stable"])


def archivo_mod(slug, mc):
    q = urllib.parse.urlencode({"loaders": '["fabric"]', "game_versions": json.dumps([mc])})
    vs = json.loads(get(f"https://api.modrinth.com/v2/project/{slug}/version?{q}"))
    if not vs:
        raise SystemExit(f"{slug} no tiene versión Fabric para {mc}")
    f = next((f for f in vs[0]["files"] if f["primary"]), vs[0]["files"][0])
    return vs[0]["version_number"], {
        "path": "mods/" + f["filename"],
        "hashes": {"sha1": f["hashes"]["sha1"], "sha512": f["hashes"]["sha512"]},
        "env": {"client": "required", "server": "unsupported"},
        "downloads": [f["url"]],
        "fileSize": f["size"],
    }


def servers_dat(nombre, ip):
    """servers.dat (NBT sin comprimir) con un servidor y su paquete de recursos aceptado (acceptTextures=1)."""
    s = lambda t: struct.pack(">H", len(t.encode())) + t.encode()
    servidor = b"\x08" + s("name") + s(nombre) + b"\x08" + s("ip") + s(ip) + b"\x01" + s("acceptTextures") + b"\x01" + b"\x00"
    return b"\x0a" + s("") + b"\x09" + s("servers") + b"\x0a" + struct.pack(">i", 1) + servidor + b"\x00"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mc", default="26.3", help="versión de Minecraft")
    ap.add_argument("--salida", help="archivo .mrpack (por defecto dist/ex6tense-<mc>.mrpack)")
    args = ap.parse_args()
    salida = args.salida or os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", f"ex6tense-{args.mc}.mrpack")

    loader = loader_fabric(args.mc)
    print(f"Minecraft {args.mc} · Fabric Loader {loader}")
    archivos = []
    for slug in MODS:
        version, archivo = archivo_mod(slug, args.mc)
        print(f"  {slug} {version}")
        archivos.append(archivo)

    indice = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": time.strftime("%Y.%m.%d"),
        "name": f"Servidor ex6tense {args.mc}",
        "summary": "Fabric con chat de voz (Simple Voice Chat) y Sodium; el servidor ya viene en la lista.",
        "files": archivos,
        "dependencies": {"minecraft": args.mc, "fabric-loader": loader},
    }
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("modrinth.index.json", json.dumps(indice, indent=2, ensure_ascii=False))
        z.writestr("overrides/servers.dat", servers_dat(*SERVIDOR))
    print(f"Pack: {salida}")


if __name__ == "__main__":
    main()
