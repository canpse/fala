"""fa: pedido em linguagem natural vira comando de terminal. Você confere, edita se quiser, e dá Enter."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import __version__, config, contexto, pi, provedores
from .config import Erro
from .idioma import PT, t

USO = t("""\
usage: fa [-flags] <request>     e.g.: fa read readme.md · fa -n capture packets on wifi

  --install [provider]   hook fa into your shell, pick the model and test it (e.g.: fa --install claude)

  --init bash|zsh   shell integration; put in ~/.bashrc:  eval "$(fa --init bash)"
  --config          create or show ~/.config/fa/config.toml (which model to use)
  --config key=value ...   change settings without editing the file
  --test            show what's in use and send a test request
  --agent           instructions for an AI agent to set fa up
  --scan            read this machine once, for context (~/.config/fa/sistema.txt)
  --service         keep pi open as a systemd user service (provider pi)
  --translate ...   only print the command, don't put it on the prompt
  --version
""", """\
uso: fa [-flags] <pedido>        ex.: fa ler readme.md · fa -n captura pacotes no wifi

  --install [provedor]   liga o fa no shell, escolhe o modelo e testa (ex.: fa --install claude)

  --init bash|zsh   integração com o shell; ponha no ~/.bashrc:  eval "$(fa --init bash)"
  --config          cria ou mostra ~/.config/fa/config.toml (qual modelo usar)
  --config chave=valor ...   muda a configuração sem editar o arquivo
  --test            mostra o que está valendo e faz um pedido de teste
  --agent           instruções pra um agente de IA configurar o fa
  --scan            lê esta máquina uma vez pro contexto (~/.config/fa/sistema.txt)
  --service         deixa o pi sempre aberto, como serviço do systemd (provedor pi)
  --translate ...   só imprime o comando, sem pôr na linha
  --version
""")

# nomes da 0.1.x, em português: continuam valendo
ANTIGAS = {"--instalar": "--install", "--testar": "--test", "--agente": "--agent",
           "--reconhecer": "--scan", "--servico": "--service", "--servir": "--serve",
           "--traduzir": "--translate", "--versao": "--version", "--ajuda": "--help"}


def ajuda():
    texto = USO
    pac = contexto.pacotes()
    if pac:
        letras = {}  # nome: [letras], a primeira é a principal
        for letra, nome in pac.items():
            letras.setdefault(nome, []).append(letra)
        texto += t("\nexample packs (flags):\n", "\npacks de exemplos (flags):\n") + "".join(
            f"  -{ls[0]}  {nome}\n" for nome, ls in sorted(letras.items(), key=lambda x: x[1][0]))
    return texto


def traduzir(args):
    pac, nomes = contexto.pacotes(), []
    while args and args[0].startswith("-") and len(args[0]) > 1:
        for letra in args.pop(0)[1:]:
            if letra not in pac:
                raise Erro(t(f"flag -{letra} does not exist", f"flag -{letra} não existe") + f"\n\n{ajuda()}")
            if pac[letra] not in nomes:
                nomes.append(pac[letra])
    if not args:
        raise Erro(ajuda())
    cfg = config.carregar()
    resposta = provedores.chamar(cfg, contexto.sistema(), contexto.pedido(" ".join(args), nomes))
    cmd = contexto.limpar(resposta)
    if not cmd:
        raise Erro(t("the model returned no command", "o modelo não devolveu comando"))
    return cmd


def mostrar_config():
    if not config.ARQUIVO.exists():
        config.criar()
        print(t(f"created {config.ARQUIVO} with this machine's best guess:\n",
                f"criei {config.ARQUIVO} com o palpite desta máquina:\n"))
    else:
        print(f"{config.ARQUIVO}:\n")
    print(config.ARQUIVO.read_text())
    if not contexto.SISTEMA.exists():
        print(t("tip: fa --scan reads this machine (distribution, network, tools) and improves the answers",
                "dica: fa --scan lê esta máquina (distribuição, rede, ferramentas) e melhora as respostas"))


def testar():
    """Diz o que está valendo e faz um pedido de verdade. Sai com erro se não funcionar."""
    cfg = config.carregar()
    origem = config.ARQUIVO if config.ARQUIVO.exists() else t(
        "no file, guessed from the keys in the environment", "nenhum arquivo, palpite pelas chaves no ambiente")
    print(f"config: {origem}")
    modelo = cfg.get("model") or t("provider's default", "padrão do provedor")
    print(t(f"provider: {cfg['provider']} · model: {modelo}", f"provedor: {cfg['provider']} · modelo: {modelo}"))
    if cfg["provider"] == "pi":
        print(t("pi service: " + ("running" if pi.SOCK.exists() else "off (fa --service makes it ~3 s faster)"),
                "serviço do pi: " + ("no ar" if pi.SOCK.exists() else "desligado (fa --service deixa ~3 s mais rápido)")))
    print(t(f"machine scan: {'yes' if contexto.SISTEMA.exists() else 'no (fa --scan improves the answers)'}",
            f"reconhecimento da máquina: {'sim' if contexto.SISTEMA.exists() else 'não (fa --scan melhora as respostas)'}"))
    pedido = t("list the files here", "lista os arquivos daqui")
    inicio = time.monotonic()
    cmd = traduzir(pedido.split())
    print(f"ok: '{pedido}' → {cmd}  ({(time.monotonic() - inicio) * 1000:.0f} ms)")


def _sem_integracao(shell):
    return Erro(t(f"shell {shell} has no integration yet (there is: bash, zsh)",
                  f"shell {shell} ainda não tem integração (tem: bash, zsh)"))


def instalar(args):
    """fa --install [provedor]: liga o fa no shell, escolhe o provedor e testa. Pode rodar de novo."""
    shell = Path(os.environ.get("SHELL", "bash")).name
    if shell not in ("bash", "zsh"):
        raise _sem_integracao(shell)
    linha = f'eval "$(fa --init {shell})"'
    rc = Path.home() / (".zshrc" if shell == "zsh" else ".bashrc")
    lidos = [rc, *sorted((Path.home() / ".bashrc.d").glob("*"))] if shell == "bash" else [rc]
    if any(f.is_file() and "fa --init" in f.read_text(errors="ignore") for f in lidos):
        print(t(f"shell: fa already loads in {shell}", f"shell: o fa já carrega no {shell}"))
    else:
        with rc.open("a") as f:
            f.write(f"\n# fa: plain language in, shell command out\n{linha}\n")
        print(t(f"shell: added to {rc}: {linha}", f"shell: acrescentei ao {rc}: {linha}"))

    if args:
        config.ajustar([f"provider={args[0]}", *args[1:]])
    elif not config.ARQUIVO.exists():
        palpite = config.adivinhar()
        if palpite is None:
            raise Erro(t("found no API key and no claude/codex/agy/pi installed. Say which one to use: fa --install claude",
                         "não achei chave de API nem claude/codex/agy/pi instalado. Diga qual usar: fa --install claude"))
        config.ajustar([f"{k}={v}" for k, v in palpite.items()])
    p = config.carregar()["provider"]
    print(t(f"provider: {p} (change it with: fa --install <provider>)",
            f"provedor: {p} (troque com: fa --install <provedor>)"))

    pasta_bin = str(Path(shutil.which("fa") or sys.argv[0]).resolve().parent)
    if pasta_bin not in os.environ.get("PATH", "").split(":"):
        print(t(f"warning: {pasta_bin} is not in PATH; the shell won't find fa",
                f"atenção: {pasta_bin} não está no PATH; o shell não vai achar o fa"))
    print()
    testar()
    print(t("\ndone. Open a new terminal and ask, for example: fa show the 5 biggest files here",
            "\npronto. Abra um terminal novo e peça, por exemplo: fa mostra os 5 maiores arquivos daqui"))


def reconhecer():
    subprocess.run(["bash", str(contexto.DADOS / "reconhecer.sh")], check=False)


def servico():
    if not shutil.which("systemctl"):
        raise Erro(t("no systemd here; run fa --serve in a separate terminal",
                     "sem systemd aqui; rode fa --serve num terminal à parte"))
    fa = shutil.which("fa") or str(Path(sys.argv[0]).resolve())
    unidade = Path.home() / ".config/systemd/user/fa.service"
    unidade.parent.mkdir(parents=True, exist_ok=True)
    unidade.unlink(missing_ok=True)  # versões antigas do fa deixavam um link aqui
    unidade.write_text(f"""\
[Unit]
Description=fa: keeps pi open to turn requests into commands

[Service]
ExecStart={fa} --serve
Environment=PATH={os.environ.get("PATH", "/usr/bin:/bin")}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
""")
    for cmd in (["daemon-reload"], ["enable", "fa.service"], ["restart", "fa.service"]):
        subprocess.run(["systemctl", "--user", *cmd], check=True)
    print(t(f"fa service on ({unidade})", f"serviço fa ligado ({unidade})"))


def init(shell):
    arq = contexto.DADOS / f"fa.{shell}"
    if not arq.exists():
        raise _sem_integracao(shell)
    return arq.read_text().replace("@THINKING@", t("thinking…", "pensando…"))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            print(ajuda(), file=sys.stderr)
            return 1
        op = ANTIGAS.get(args[0], args[0])
        if op in ("-h", "--help"):
            print(ajuda())
        elif op == "--version":
            print(f"fa (fala) {__version__}")
        elif op == "--init":
            print(init(args[1] if len(args) > 1 else Path(os.environ.get("SHELL", "bash")).name))
        elif op == "--config" and len(args) > 1:
            config.ajustar(args[1:])
            print(config.ARQUIVO.read_text(), end="")
        elif op == "--config":
            mostrar_config()
        elif op == "--install":
            instalar(args[1:])
        elif op == "--test":
            testar()
        elif op == "--agent":
            print((contexto.DADOS / ("AGENTES.md" if PT else "AGENTS.md")).read_text())
        elif op == "--scan":
            reconhecer()
        elif op == "--serve":
            pi.servir(config.carregar(), contexto.sistema())
        elif op == "--service":
            servico()
        elif op == "--translate":
            print(traduzir(args[1:]))
        elif op.startswith("--"):
            raise Erro(t(f"option {op} does not exist", f"opção {op} não existe") + f"\n\n{ajuda()}")
        else:
            print(traduzir(args))
    except Erro as e:
        sys.stdout.flush()
        # apaga o "pensando…" que o shell deixou na linha
        print(("\r\033[K" if sys.stderr.isatty() else "") + f"fa: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0
