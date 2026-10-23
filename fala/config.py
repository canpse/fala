"""Configuração em ~/.config/fa/config.toml. Sem o arquivo, adivinha pelo que existe na máquina."""
import json
import os
import shutil
import tomllib
from pathlib import Path

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
# fa (pacote fala): qual modelo traduz o pedido em comando.
# provedor: anthropic | openai | openrouter | groq | ollama | compat | pi | claude | codex | agy
provedor = "{provedor}"
{modelo}
# compat = qualquer API no formato da OpenAI (llama.cpp, vLLM, LM Studio...):
# url = "http://localhost:8080/v1"
# chave_env = "MINHA_CHAVE"    # nome da variável de ambiente com a chave (a chave não fica aqui)

# pi = usa o pi (https://github.com/badlogic/pi-mono) com o login que ele já tem.
# Sem pi_provedor/modelo, vale o padrão do próprio pi. Mais rápido com: fa --servico
# pi_provedor = "openai-codex"
# pensamento = "off"

# claude, codex, agy = usa a assinatura pelo programa oficial já logado (sem chave de API).
# modelo e pensamento são os do próprio programa (claude: haiku · codex: gpt-6-luna, low · agy: gemini-3.8-flash-low)

# segundos até desistir de uma resposta
# tempo_limite = 30
"""


class Erro(Exception):
    """Erro com mensagem pronta pra mostrar a quem usa."""


def adivinhar():
    """Primeiro provedor que dá pra usar sem perguntar nada, ou None."""
    for nome, var in (("anthropic", ANTHROPIC[1]), ("openai", "OPENAI_API_KEY"),
                      ("openrouter", "OPENROUTER_API_KEY"), ("groq", "GROQ_API_KEY")):
        if os.environ.get(var):
            cfg = {"provedor": nome}
            if nome == "openrouter" and os.environ.get("OPENROUTER_MODEL"):
                cfg["modelo"] = os.environ["OPENROUTER_MODEL"]
            return cfg
    for cli in ("pi", *ASSINATURAS):  # do mais rápido pro mais lento
        if shutil.which(cli):
            return {"provedor": cli}
    return None


def carregar():
    if ARQUIVO.exists():
        try:
            cfg = tomllib.loads(ARQUIVO.read_text())
        except tomllib.TOMLDecodeError as e:
            raise Erro(f"{ARQUIVO} com erro: {e}")
    else:
        cfg = adivinhar()
        if cfg is None:
            raise Erro("nenhum modelo configurado. Rode: fa --config")
    if cfg.get("provedor") not in PROVEDORES:
        raise Erro(f"provedor {cfg.get('provedor')!r} não existe (use um de: {', '.join(PROVEDORES)})")
    cfg.setdefault("tempo_limite", 30)
    return cfg


CHAVES = {"provedor": str, "modelo": str, "url": str, "chave_env": str,
          "pi_provedor": str, "pensamento": str, "tempo_limite": int}


def escrever(cfg):
    linhas = ["# fa (pacote fala). Opções: fa --agente. Mude com: fa --config chave=valor"]
    for chave in CHAVES:
        if chave in cfg:
            v = cfg[chave]
            # json.dumps escapa aspas e barras do jeito que o TOML aceita
            linhas.append(f"{chave} = {v if isinstance(v, int) else json.dumps(v, ensure_ascii=False)}")
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text("\n".join(linhas) + "\n")


def ajustar(pares):
    """fa --config chave=valor ...: muda só essas chaves. Trocar de provedor apaga as do provedor antigo."""
    atual = tomllib.loads(ARQUIVO.read_text()) if ARQUIVO.exists() else {}
    novo = {}
    for par in pares:
        chave, sep, valor = par.partition("=")
        if not sep or chave not in CHAVES:
            raise Erro(f"{par!r}: use chave=valor, com chave entre: {', '.join(CHAVES)}")
        if CHAVES[chave] is int:
            try:
                valor = int(valor)
            except ValueError:
                raise Erro(f"{chave} precisa ser um número")
        novo[chave] = valor
    if "provedor" in novo and novo["provedor"] != atual.get("provedor"):
        atual = {}
    cfg = {k: v for k, v in {**atual, **novo}.items() if v != ""}  # chave= (vazio) apaga
    if cfg.get("provedor") not in PROVEDORES:
        raise Erro(f"provedor {cfg.get('provedor')!r} não existe (use um de: {', '.join(PROVEDORES)})")
    escrever(cfg)


def criar():
    """Escreve o config.toml com o palpite desta máquina. Devolve o texto escrito."""
    cfg = adivinhar() or {"provedor": "anthropic"}
    p = cfg["provedor"]
    if cfg.get("modelo"):
        modelo = f'modelo = "{cfg["modelo"]}"'
    elif p == "anthropic":
        modelo = f'modelo = "{ANTHROPIC[2]}"'
    elif p in ("pi", *ASSINATURAS):
        modelo = '# modelo = ""    # vazio = o padrão do programa'
    else:
        modelo = 'modelo = ""    # obrigatório: o nome do modelo nesse provedor'
    texto = MODELO.format(provedor=p, modelo=modelo)
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(texto)
    return texto
