#!/usr/bin/env python3
"""Crea i pacchetti scaricabili di MG4 Voce (1.0) e il catalogo.

  python3 tools/packs/make_packs.py [--tag v1]

Uscita in dist/packs/: lang-<lingua>.zip, voice-<lingua>-<nome>.zip, voice-<lingua>-<nome>.ogg (anteprima)
e catalog.json. Da caricare cosi':
  - gli zip e le anteprime .ogg  → Release "packs-v1" del repository mg4-voice (allegati; togliere "Set as the latest release")
  - catalog.json                 → nella radice del repository mg4-voice (ramo main)
"""
import argparse, hashlib, json, os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "packs-src")
OUT = os.path.join(ROOT, "dist", "packs")
REPO = "ernestomicco2026-cell/mg4-voice"

# lingue pronte: {codice: (cartella modello Vosk, cartella voce Piper di riserva, voci registrate)}
LANGS = {
    "it": ("model-it", "tts-it", [("sara", "Sara", "f"), ("nicola", "Nicola", "m")]),
}
SAMPLE_KEY = {"it": "ciao sono il tuo assistente mg mi senti bene"}


def zipdir(zpath, parts):
    """parts: [(cartella sorgente, prefisso nello zip)]"""
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for src, prefix in parts:
            for base, _, files in os.walk(src):
                for f in sorted(files):
                    full = os.path.join(base, f)
                    rel = os.path.relpath(full, src)
                    # gli .ogg sono gia' compressi
                    z.write(full, os.path.join(prefix, rel), compress_type=zipfile.ZIP_STORED if f.endswith(".ogg") else zipfile.ZIP_DEFLATED)


def info(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest(), os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="packs-v1")
    ap.add_argument("--version", default="1")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    base = f"https://github.com/{REPO}/releases/download/{a.tag}/"
    packs = []
    for lang, (model, tts, voices) in LANGS.items():
        z = os.path.join(OUT, f"lang-{lang}.zip")
        zipdir(z, [(os.path.join(SRC, model), "model"), (os.path.join(SRC, tts), "tts")])
        sha, size = info(z)
        packs.append({"id": f"lang-{lang}", "type": "lang", "lang": lang, "name": lang, "version": a.version,
                      "size": size, "sha256": sha, "url": base + os.path.basename(z)})
        print(f"lang-{lang}: {size / 1e6:.1f} MB")
        for vid, vname, gender in voices:
            vdir = os.path.join(SRC, "voce", vid)
            pid = f"voice-{lang}-{vid}"
            z = os.path.join(OUT, pid + ".zip")
            zipdir(z, [(vdir, "")])
            sha, size = info(z)
            prev = ""
            k = SAMPLE_KEY.get(lang)
            for line in open(os.path.join(vdir, "index.txt"), encoding="utf-8"):
                key, _, f = line.rstrip("\n").partition("\t")
                if key == k:
                    with open(os.path.join(vdir, f), "rb") as i, open(os.path.join(OUT, pid + ".ogg"), "wb") as o:
                        o.write(i.read())
                    prev = base + pid + ".ogg"
            packs.append({"id": pid, "type": "voice", "lang": lang, "name": vname, "gender": gender,
                          "version": a.version, "size": size, "sha256": sha, "url": base + os.path.basename(z),
                          "preview": prev})
            print(f"{pid}: {size / 1e6:.1f} MB")
    cat = {"version": 1, "packs": packs}
    with open(os.path.join(OUT, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)
    print("catalogo:", os.path.join(OUT, "catalog.json"))


if __name__ == "__main__":
    main()
