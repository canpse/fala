"""O que vai pro modelo: prompt fixo + sistema lido na instalação, e por pedido a pasta e os pacotes."""
import os
import re
import shutil
import unicodedata
from pathlib import Path

from .config import PASTA

DADOS = Path(__file__).parent / "dados"
SISTEMA = PASTA / "sistema.txt"


def sistema():
    texto = (DADOS / "prompt.txt").read_text()
    if SISTEMA.exists():
        texto += "\n" + SISTEMA.read_text()
    return texto


# Pastas de packs: os que vêm com o fa e os da pessoa. "pacotes" e "redes" são os nomes da 0.1.x.
PASTAS_PACKS = (DADOS / "packs", PASTA / "packs", PASTA / "pacotes")
ANTIGOS = {"redes": "network"}


def pacotes():
    """{letra: nome}. Um pack é um .txt com a linha '# flag: x' (ou '# flag: x y', a 1ª é a que aparece na ajuda)."""
    achados = {}
    for pasta in PASTAS_PACKS:
        for f in sorted(pasta.glob("*.txt")):
            for linha in f.read_text().splitlines():
                if linha.startswith("# flag: "):
                    for letra in linha[8:].split():
                        achados.setdefault(letra, ANTIGOS.get(f.stem, f.stem))
    return achados


def _linhas(f):
    return [l for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")]


def exemplos(nome):
    texto = ""
    antigo = next((a for a, n in ANTIGOS.items() if n == nome), None)
    comum = DADOS / "packs" / f"{nome}.txt"
    local = next((f for f in (PASTA / "packs" / f"{nome}.txt", PASTA / "pacotes" / f"{nome}.txt",
                              PASTA / "pacotes" / f"{antigo}.txt") if f.exists()), None)
    if comum.exists():
        texto += (f"Common examples from the {nome} pack (request => command; adapt them, don't copy one that doesn't fit):\n"
                  + "\n".join(_linhas(comum)) + "\n\n")
    if local:
        texto += (f"Examples from the {nome} pack for THIS machine (when they contradict the common ones, these win):\n"
                  + "\n".join(_linhas(local)) + "\n\n")
    return texto


def arquivos(limite=80):
    """Até 2 níveis da pasta atual, sem entrar no .git."""
    achados = []
    try:
        for e in sorted(os.scandir("."), key=lambda e: e.name):
            achados.append(e.name)
            if e.is_dir(follow_symlinks=False) and e.name != ".git":
                try:
                    achados += [f"{e.name}/{s}" for s in sorted(os.listdir(e.path))]
                except OSError:
                    pass
            if len(achados) >= limite:
                break
    except OSError:
        pass
    return achados[:limite]


# Programas do dia a dia que o modelo costuma achar que faltam. Conferir leva milissegundos,
# então vai ao vivo a cada pedido (o reconhecimento da instalação pode estar velho ou nem existir).
COMUNS = """
pdfunite pdfseparate pdftotext pdftoppm qpdf pdftk gs ocrmypdf
soffice libreoffice pandoc
ffmpeg ffprobe sox lame flac opusenc yt-dlp
magick convert identify exiftool cwebp
unzip zip 7z 7za unrar tar gzip xz zstd bzip2
rsync rclone trash-put fd rg fzf jq yq bat tree ncdu
git gh docker podman flatpak snap
apt dnf pacman zypper brew
curl wget aria2c nc nmap dig ss ip mtr traceroute
python3 node npm pip pipx uv go cargo java
xdg-open notify-send wl-copy xclip
""".split()


def instalados():
    return [p for p in COMUNS if shutil.which(p)]


def pedido(texto, nomes_pacotes=()):
    return ("".join(exemplos(n) for n in nomes_pacotes)
            + f"Current folder: {os.getcwd()}\n"
            + f"Installed programs (of the common ones): {' '.join(instalados())}\n"
            + f"Files (up to 2 levels): {' '.join(arquivos())}\n\n"
            + f"Request: {texto}")


def limpar(resposta):
    """O comando que veio entre <cmd></cmd>: sem pensamento, o modelo às vezes raciocina em voz alta
    antes. Sem as marcas, tira crases e linhas vazias. Tira também caracteres que não existem
    (visto: U+4E180 colado no fim de um cp)."""
    resposta = "".join(c for c in resposta
                       if unicodedata.category(c) not in ("Cn", "Co", "Cs") or c == "\n")
    marcados = re.findall(r"<cmd>(.*?)</cmd>", resposta, re.S)
    if marcados:
        return marcados[-1].strip()
    linhas = [l for l in resposta.splitlines() if l.strip() and not l.startswith("```")]
    return "\n".join(linhas).strip()
