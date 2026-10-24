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
from .idioma import t


def _chave(var):
    if var is None:
        return None
    chave = os.environ.get(var)
    if not chave:
        raise Erro(t(f"missing key: the variable {var} is empty", f"falta a chave: a variável {var} está vazia"))
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
            raise Erro(t(f"the provider rejected the key ({e.code}): {detalhe}",
                         f"o provedor recusou a chave ({e.code}): {detalhe}"))
        raise Erro(t(f"the provider answered {e.code}: {detalhe}", f"o provedor respondeu {e.code}: {detalhe}"))
    except (urllib.error.URLError, TimeoutError) as e:
        motivo = getattr(e, "reason", e)
        raise Erro(t(f"no answer from {url} ({motivo})", f"sem resposta de {url} ({motivo})"))


def compat(cfg, sistema, texto):
    url, var, modelo = COMPAT.get(cfg["provider"], (None, None, None))
    url = cfg.get("url", url)
    modelo = cfg.get("model", modelo)
    if not url:
        raise Erro(t("provider compat needs a url: fa --config url=http://...",
                     "provedor compat precisa de url: fa --config url=http://..."))
    if not modelo:
        raise Erro(t(f"provider {cfg['provider']} needs a model: fa --config model=...",
                     f"falta o modelo do provedor {cfg['provider']}: fa --config model=..."))
    chave = _chave(cfg.get("key_env", var))
    r = _post(url.rstrip("/") + "/chat/completions",
              {"Authorization": f"Bearer {chave}"} if chave else {},
              {"model": modelo, "messages": [{"role": "system", "content": sistema},
                                             {"role": "user", "content": texto}]},
              cfg["timeout"])
    try:
        return r["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise Erro(t(f"unexpected answer from the provider: {str(r)[:300]}",
                     f"resposta estranha do provedor: {str(r)[:300]}"))


def anthropic(cfg, sistema, texto):
    url, var, modelo = ANTHROPIC
    r = _post(cfg.get("url", url),
              {"x-api-key": _chave(cfg.get("key_env", var)), "anthropic-version": "2023-06-01"},
              {"model": cfg.get("model", modelo), "max_tokens": 400, "system": sistema,
               "messages": [{"role": "user", "content": texto}]},
              cfg["timeout"])
    return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")


def pi(cfg, sistema, texto):
    # Com o serviço no ar (fa --servico), o pi já está aberto: ~1 s a menos por pedido.
    resposta = pi_servidor.pedir(texto)
    if resposta is not None:
        return resposta
    if not shutil.which("pi"):
        raise Erro(t("provider is pi, but the pi command is not installed",
                     "provedor pi, mas o comando pi não está instalado"))
    try:
        r = subprocess.run(["pi", "-p", *pi_servidor.argumentos(cfg, sistema), texto],
                           capture_output=True, text=True, timeout=cfg["timeout"])
    except subprocess.TimeoutExpired:
        s = cfg["timeout"]
        raise Erro(t(f"pi did not answer in {s} s (no internet? login expired? try: pi -p hi)",
                     f"o pi não respondeu em {s} s (sem internet? login vencido? teste: pi -p oi)"))
    if r.returncode != 0 or not r.stdout.strip():
        detalhe = (r.stderr or t("no answer", "sem resposta")).strip()[:300]
        raise Erro(t(f"pi failed: {detalhe}", f"o pi falhou: {detalhe}"))
    return r.stdout


def _rodar(cfg, args, nome):
    """Chama o CLI oficial de uma assinatura (claude, codex, agy) uma vez, sem ferramentas nem memória.
    Roda numa pasta neutra pra não carregar o CLAUDE.md/AGENTS.md do projeto onde a pessoa está."""
    if not shutil.which(args[0]):
        raise Erro(t(f"provider is {nome}, but the {args[0]} command is not installed",
                     f"provedor {nome}, mas o comando {args[0]} não está instalado"))
    CACHE.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=CACHE,
                           stdin=subprocess.DEVNULL, timeout=cfg["timeout"])
    except subprocess.TimeoutExpired:
        s = cfg["timeout"]
        raise Erro(t(f"{args[0]} did not answer in {s} s (no internet? login expired?)",
                     f"o {args[0]} não respondeu em {s} s (sem internet? login vencido?)"))
    if r.returncode != 0:
        detalhe = (r.stderr or r.stdout).strip()[-300:]
        raise Erro(t(f"{args[0]} failed: {detalhe}", f"o {args[0]} falhou: {detalhe}"))
    return r.stdout


def claude(cfg, sistema, texto):
    args = ["claude", "-p", "--model", cfg.get("model", "haiku"), "--tools", "",
            "--no-session-persistence", "--strict-mcp-config", "--setting-sources", "",
            "--system-prompt", sistema]
    if cfg.get("thinking"):
        args += ["--effort", cfg["thinking"]]
    return _rodar(cfg, args + [texto], "claude")


def codex(cfg, sistema, texto):
    with tempfile.TemporaryDirectory() as pasta:
        saida = os.path.join(pasta, "resposta.txt")  # a resposta limpa, sem o log do codex
        _rodar(cfg, ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config",
                     "--ignore-rules", "-s", "read-only", "-c", "mcp_servers={}",
                     "-m", cfg.get("model", "gpt-6-luna"),
                     "-c", f"model_reasoning_effort={cfg.get('thinking', 'low')}",
                     "-c", f"developer_instructions={sistema}", "-o", saida, texto], "codex")
        with open(saida) as f:
            return f.read()


def agy(cfg, sistema, texto):
    # o agy não tem opção de prompt de sistema: as regras vão junto com o pedido
    args = ["agy", "--disable-slash-commands", "--model", cfg.get("model", "gemini-3.8-flash-low")]
    if cfg.get("thinking"):
        args += ["--effort", cfg["thinking"]]
    return _rodar(cfg, args + [f"-p={sistema}\n\n{texto}"], "agy")


ASSINATURAS = {"claude": claude, "codex": codex, "agy": agy}


def chamar(cfg, sistema, texto):
    p = cfg["provider"]
    if p == "anthropic":
        return anthropic(cfg, sistema, texto)
    if p == "pi":
        return pi(cfg, sistema, texto)
    if p in ASSINATURAS:
        return ASSINATURAS[p](cfg, sistema, texto)
    return compat(cfg, sistema, texto)
