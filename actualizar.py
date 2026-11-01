#!/usr/bin/env python3
"""Actualiza los plugins del servidor desde Modrinth según plugins.txt."""
import argparse
import fnmatch
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.abspath(__file__))
UA = "ex6tense/minecraft-plugins (github.com/ex6tense/minecraft-plugins)"
LOADERS = ["paper", "spigot", "bukkit", "purpur"]
DIR_DEFECTO = "/home/amp/.ampdata/instances/Minecraft201/Minecraft/plugins"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def sha512(path):
    h = hashlib.sha512()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def version_mc(server_dir):
    # Paper antiguo: "... (MC: 1.21.4)"; Paper 26.x: "26.3-235-main@bb10cf0 (...)"
    try:
        with open(os.path.join(server_dir, "version_history.json")) as f:
            actual = json.load(f)["currentVersion"]
        m = re.search(r"MC: ([\d.]+)", actual) or re.match(r"(\d+\.\d+(?:\.\d+)?)-", actual)
        if m:
            return m.group(1)
    except (OSError, KeyError, ValueError):
        pass
    # Paperclip deja el servidor en versions/<mc>/paper-<mc>.jar; la más reciente es la que corre
    jars = glob.glob(os.path.join(server_dir, "versions", "*", "paper-*.jar"))
    return os.path.basename(os.path.dirname(max(jars, key=os.path.getmtime))) if jars else None


def elegir(versiones, mc):
    """La versión más nueva para mc; si no hay, la más nueva de la misma serie (26.x)."""
    exacta = next((v for v in versiones if mc in v["game_versions"]), None)
    if exacta:
        return exacta, True
    serie = mc.split(".")[0] + "."
    return next((v for v in versiones if any(g.startswith(serie) for g in v["game_versions"])), None), False


def leer_lista(path):
    with open(path, encoding="utf-8") as f:
        for linea in f:
            partes = linea.split("#", 1)[0].split()
            if partes:
                yield partes[0], [p.lower() for p in partes[1:]]


def actualizar_repo(args):
    if args.sin_pull or not os.path.isdir(os.path.join(REPO, ".git")):
        return
    head = lambda: subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout
    antes = head()
    subprocess.run(["git", "-C", REPO, "pull", "--ff-only", "-q"])
    if head() != antes:  # el script pudo cambiar: vuelve a ejecutar la versión nueva
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), "--sin-pull", *sys.argv[1:]])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=DIR_DEFECTO, help="carpeta plugins del servidor")
    ap.add_argument("--mc", help="versión de Minecraft (por defecto se detecta)")
    ap.add_argument("-n", "--simular", action="store_true", help="solo muestra qué cambiaría")
    ap.add_argument("--sin-pull", action="store_true", help="no hace git pull antes")
    args = ap.parse_args()
    sys.stdout.reconfigure(errors="replace")  # consolas sin UTF-8 no deben romper la salida
    actualizar_repo(args)

    plugins = args.dir.rstrip("/")
    if not os.path.isdir(plugins):
        sys.exit(f"No existe {plugins}")
    server_dir = os.path.dirname(plugins)
    mc = args.mc or version_mc(server_dir)
    if not mc:
        sys.exit("No pude detectar la versión de Minecraft; usa --mc 26.3")
    st = os.stat(plugins)
    respaldo = os.path.join(server_dir, "plugins-respaldo", time.strftime("%Y-%m-%d_%H%M%S"))
    actuales = [j for j in os.listdir(plugins) if j.lower().endswith(".jar")]
    cambios = errores = 0
    print(f"Minecraft {mc} · {plugins}" + ("  (simulación)" if args.simular else ""))

    for slug, patrones in leer_lista(os.path.join(REPO, "plugins.txt")):
        try:
            v, exacta = None, False
            for loaders in (["paper"], LOADERS):  # la variante Paper primero; si no hay para mc, cualquiera
                q = urllib.parse.urlencode({"loaders": json.dumps(loaders)})
                cand, cand_exacta = elegir(json.loads(get(f"https://api.modrinth.com/v2/project/{slug}/version?{q}")), mc)
                if cand and (cand_exacta or not v):
                    v, exacta = cand, cand_exacta
                if exacta:
                    break
            if not v:
                raise RuntimeError(f"no hay versión para {mc.split('.')[0]}.x")
            f = next((f for f in v["files"] if f["primary"]), v["files"][0])
            viejos = [j for j in actuales if any(fnmatch.fnmatch(j.lower(), p) for p in patrones)]
            if any(sha512(os.path.join(plugins, j)) == f["hashes"]["sha512"] for j in viejos):
                print(f"  = {slug} {v['version_number']} al día")
                continue
            aviso = "" if exacta else f"  (aviso: solo declara hasta {v['game_versions'][-1]})"
            print(f"  + {slug}: {', '.join(viejos) or '(nuevo)'} → {f['filename']}{aviso}")
            cambios += 1
            if args.simular:
                continue
            datos = get(f["url"])
            if hashlib.sha512(datos).hexdigest() != f["hashes"]["sha512"]:
                raise RuntimeError("la descarga no coincide con el hash de Modrinth; no se instala")
            if viejos:
                os.makedirs(respaldo, exist_ok=True)
            for j in viejos:
                shutil.move(os.path.join(plugins, j), os.path.join(respaldo, j))
            destino = os.path.join(plugins, f["filename"])
            with open(destino + ".tmp", "wb") as out:
                out.write(datos)
            os.replace(destino + ".tmp", destino)
            if hasattr(os, "chown"):
                os.chown(destino, st.st_uid, st.st_gid)
        except Exception as e:
            errores += 1
            print(f"  ! {slug}: {e}")

    print(f"\n{cambios} cambio(s), {errores} error(es).")
    if cambios and not args.simular:
        if os.path.isdir(respaldo):
            print(f"Los .jar viejos están en {respaldo}")
        print("Reinicia el servidor en AMP para cargar los plugins nuevos.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
