"""Cada provedor recebe (cfg, sistema, texto) e devolve a resposta crua do modelo."""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request

from . import pi as pi_servidor
from .config import ANTHROPIC, CACHE, COMPAT, Erro


def _chave(var):
    if var is None:
        return None
    chave = os.environ.get(var)
    if not chave:
        raise Erro(f"falta a chave: a variável {var} está vazia")
    return chave


def _post(url, cabecalhos, corpo, limite):
    req = urllib.request.Request(url, json.dumps(corpo).encode(),
                                 {"Content-Type": "application/json", **cabecalhos})
    try:
        with urllib.request.urlopen(req, timeout=limite) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode(errors="replace")[:300]
        if e.code in (401, 403):
            raise Erro(f"o provedor recusou a chave ({e.code}): {detalhe}")
        raise Erro(f"o provedor respondeu {e.code}: {detalhe}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise Erro(f"sem resposta de {url} ({getattr(e, 'reason', e)})")


def compat(cfg, sistema, texto):
    url, var, modelo = COMPAT.get(cfg["provedor"], (None, None, None))
    url = cfg.get("url", url)
    modelo = cfg.get("modelo", modelo)
    if not url:
        raise Erro("provedor compat precisa de url no config.toml")
    if not modelo:
        raise Erro(f"falta o modelo do provedor {cfg['provedor']} no config.toml (fa --config)")
    chave = _chave(cfg.get("chave_env", var))
    r = _post(url.rstrip("/") + "/chat/completions",
              {"Authorization": f"Bearer {chave}"} if chave else {},
              {"model": modelo, "messages": [{"role": "system", "content": sistema},
                                             {"role": "user", "content": texto}]},
              cfg["tempo_limite"])
    try:
        return r["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise Erro(f"resposta estranha do provedor: {str(r)[:300]}")


def anthropic(cfg, sistema, texto):
    url, var, modelo = ANTHROPIC
    r = _post(cfg.get("url", url),
              {"x-api-key": _chave(cfg.get("chave_env", var)), "anthropic-version": "2023-06-01"},
              {"model": cfg.get("modelo", modelo), "max_tokens": 400, "system": sistema,
               "messages": [{"role": "user", "content": texto}]},
              cfg["tempo_limite"])
    return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")


def pi(cfg, sistema, texto):
    # Com o serviço no ar (fa --servico), o pi já está aberto: ~1 s a menos por pedido.
    resposta = pi_servidor.pedir(texto)
    if resposta is not None:
        return resposta
    if not shutil.which("pi"):
        raise Erro("provedor pi, mas o comando pi não está instalado")
    try:
        r = subprocess.run(["pi", "-p", *pi_servidor.argumentos(cfg, sistema), texto],
                           capture_output=True, text=True, timeout=cfg["tempo_limite"])
    except subprocess.TimeoutExpired:
        raise Erro(f"o pi não respondeu em {cfg['tempo_limite']} s (sem internet? login vencido? teste: pi -p oi)")
    if r.returncode != 0 or not r.stdout.strip():
        raise Erro(f"o pi falhou: {(r.stderr or 'sem resposta').strip()[:300]}")
    return r.stdout


def _rodar(cfg, args, nome):
    """Chama o CLI oficial de uma assinatura (claude, codex, agy) uma vez, sem ferramentas nem memória.
    Roda numa pasta neutra pra não carregar o CLAUDE.md/AGENTS.md do projeto onde a pessoa está."""
    if not shutil.which(args[0]):
        raise Erro(f"provedor {nome}, mas o comando {args[0]} não está instalado")
    CACHE.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=CACHE,
                           stdin=subprocess.DEVNULL, timeout=cfg["tempo_limite"])
    except subprocess.TimeoutExpired:
        raise Erro(f"o {args[0]} não respondeu em {cfg['tempo_limite']} s (sem internet? login vencido?)")
    if r.returncode != 0:
        raise Erro(f"o {args[0]} falhou: {(r.stderr or r.stdout).strip()[-300:]}")
    return r.stdout


def claude(cfg, sistema, texto):
    args = ["claude", "-p", "--model", cfg.get("modelo", "haiku"), "--tools", "",
            "--no-session-persistence", "--strict-mcp-config", "--setting-sources", "",
            "--system-prompt", sistema]
    if cfg.get("pensamento"):
        args += ["--effort", cfg["pensamento"]]
    return _rodar(cfg, args + [texto], "claude")


def codex(cfg, sistema, texto):
    with tempfile.TemporaryDirectory() as pasta:
        saida = os.path.join(pasta, "resposta.txt")  # a resposta limpa, sem o log do codex
        _rodar(cfg, ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config",
                     "--ignore-rules", "-s", "read-only", "-c", "mcp_servers={}",
                     "-m", cfg.get("modelo", "gpt-6-luna"),
                     "-c", f"model_reasoning_effort={cfg.get('pensamento', 'low')}",
                     "-c", f"developer_instructions={sistema}", "-o", saida, texto], "codex")
        with open(saida) as f:
            return f.read()


def agy(cfg, sistema, texto):
    # o agy não tem opção de prompt de sistema: as regras vão junto com o pedido
    args = ["agy", "--disable-slash-commands", "--model", cfg.get("modelo", "gemini-3.8-flash-low")]
    if cfg.get("pensamento"):
        args += ["--effort", cfg["pensamento"]]
    return _rodar(cfg, args + [f"-p={sistema}\n\n{texto}"], "agy")


ASSINATURAS = {"claude": claude, "codex": codex, "agy": agy}


def chamar(cfg, sistema, texto):
    p = cfg["provedor"]
    if p == "anthropic":
        return anthropic(cfg, sistema, texto)
    if p == "pi":
        return pi(cfg, sistema, texto)
    if p in ASSINATURAS:
        return ASSINATURAS[p](cfg, sistema, texto)
    return compat(cfg, sistema, texto)
