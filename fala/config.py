"""Configuração em ~/.config/fa/config.toml. Sem o arquivo, adivinha pelo que existe na máquina."""
import json
import os
import shutil
import tomllib
from pathlib import Path

from .idioma import t

PASTA = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "fa"
ARQUIVO = PASTA / "config.toml"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "fa"

# Provedores com API no formato da OpenAI: (url, variável de ambiente com a chave, modelo padrão)
COMPAT = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", None),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", None),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", None),
    "ollama": ("http://localhost:11434/v1", None, None),
}
ANTHROPIC = ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY", "claude-haiku-5-5")
# Assinaturas: o fa chama o CLI oficial já logado (claude, codex, agy), sem chave de API
ASSINATURAS = ("claude", "codex", "agy")
PROVEDORES = ("anthropic", *COMPAT, "compat", "pi", *ASSINATURAS)

MODELO = """\
# fa (package fala): which model turns your request into a command.
# provider: anthropic | openai | openrouter | groq | ollama | compat | pi | claude | codex | agy
provider = "{provider}"
{model}
# compat = any OpenAI-compatible API (llama.cpp, vLLM, LM Studio...):
# url = "http://localhost:8080/v1"
# key_env = "MY_KEY"    # name of the environment variable holding the key (the key never goes here)

# pi = uses pi (https://github.com/badlogic/pi-mono) with the login it already has.
# Without pi_provider/model, pi's own defaults apply. Faster with: fa --service
# pi_provider = "openai-codex"
# thinking = "off"

# claude, codex, agy = use your subscription through the official CLI, already logged in (no API key).
# model and thinking are the program's own (claude: haiku · codex: gpt-6-luna, low · agy: gemini-3.8-flash-low)

# seconds before giving up on an answer
# timeout = 30
"""


class Erro(Exception):
    """Erro com mensagem pronta pra mostrar a quem usa."""


def adivinhar():
    """Primeiro provedor que dá pra usar sem perguntar nada, ou None."""
    for nome, var in (("anthropic", ANTHROPIC[1]), ("openai", "OPENAI_API_KEY"),
                      ("openrouter", "OPENROUTER_API_KEY"), ("groq", "GROQ_API_KEY")):
        if os.environ.get(var):
            cfg = {"provider": nome}
            if nome == "openrouter" and os.environ.get("OPENROUTER_MODEL"):
                cfg["model"] = os.environ["OPENROUTER_MODEL"]
            return cfg
    for cli in ("pi", *ASSINATURAS):  # do mais rápido pro mais lento
        if shutil.which(cli):
            return {"provider": cli}
    return None


CHAVES = {"provider": str, "model": str, "url": str, "key_env": str,
          "pi_provider": str, "thinking": str, "timeout": int}
# nomes da 0.1.x, em português: continuam valendo e viram os novos na próxima gravação
ANTIGAS = {"provedor": "provider", "modelo": "model", "chave_env": "key_env",
           "pi_provedor": "pi_provider", "pensamento": "thinking", "tempo_limite": "timeout"}


def _novas(cfg):
    return {ANTIGAS.get(k, k): v for k, v in cfg.items()}


def _conferir(cfg):
    if cfg.get("provider") not in PROVEDORES:
        raise Erro(t(f"provider {cfg.get('provider')!r} does not exist (use one of: {', '.join(PROVEDORES)})",
                     f"provedor {cfg.get('provider')!r} não existe (use um de: {', '.join(PROVEDORES)})"))


def carregar():
    if ARQUIVO.exists():
        try:
            cfg = _novas(tomllib.loads(ARQUIVO.read_text()))
        except tomllib.TOMLDecodeError as e:
            raise Erro(t(f"error in {ARQUIVO}: {e}", f"{ARQUIVO} com erro: {e}"))
    else:
        cfg = adivinhar()
        if cfg is None:
            raise Erro(t("no model configured. Run: fa --install", "nenhum modelo configurado. Rode: fa --install"))
    _conferir(cfg)
    cfg.setdefault("timeout", 30)
    return cfg


def escrever(cfg):
    linhas = ["# fa (package fala). Options: fa --agent. Change with: fa --config key=value"]
    for chave in CHAVES:
        if chave in cfg:
            v = cfg[chave]
            # json.dumps escapa aspas e barras do jeito que o TOML aceita
            linhas.append(f"{chave} = {v if isinstance(v, int) else json.dumps(v, ensure_ascii=False)}")
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text("\n".join(linhas) + "\n")


def ajustar(pares):
    """fa --config chave=valor ...: muda só essas chaves. Trocar de provedor apaga as do provedor antigo."""
    atual = _novas(tomllib.loads(ARQUIVO.read_text())) if ARQUIVO.exists() else {}
    novo = {}
    for par in pares:
        chave, sep, valor = par.partition("=")
        chave = ANTIGAS.get(chave, chave)
        if not sep or chave not in CHAVES:
            raise Erro(t(f"{par!r}: use key=value, with key one of: {', '.join(CHAVES)}",
                         f"{par!r}: use chave=valor, com chave entre: {', '.join(CHAVES)}"))
        if CHAVES[chave] is int:
            try:
                valor = int(valor)
            except ValueError:
                raise Erro(t(f"{chave} must be a number", f"{chave} precisa ser um número"))
        novo[chave] = valor
    if "provider" in novo and novo["provider"] != atual.get("provider"):
        atual = {}
    cfg = {k: v for k, v in {**atual, **novo}.items() if v != ""}  # chave= (vazio) apaga
    _conferir(cfg)
    escrever(cfg)


def criar():
    """Escreve o config.toml com o palpite desta máquina. Devolve o texto escrito."""
    cfg = adivinhar() or {"provider": "anthropic"}
    p = cfg["provider"]
    if cfg.get("model"):
        modelo = f'model = "{cfg["model"]}"'
    elif p == "anthropic":
        modelo = f'model = "{ANTHROPIC[2]}"'
    elif p in ("pi", *ASSINATURAS):
        modelo = '# model = ""    # empty = the program\'s default'
    else:
        modelo = 'model = ""    # required: the model name at this provider'
    texto = MODELO.format(provider=p, model=modelo)
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(texto)
    return texto
