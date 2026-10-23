"""fa: pedido em linguagem natural vira comando de terminal. Você confere, edita se quiser, e dá Enter."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import __version__, config, contexto, pi, provedores
from .config import Erro

USO = """\
uso: fa [-flags] <pedido>        ex.: fa ler readme.md · fa -r captura pacotes no wifi

  --instalar [provedor]      liga o fa no shell, escolhe o modelo e testa (ex.: fa --instalar claude)

  --init bash|zsh   integração com o shell; ponha no ~/.bashrc:  eval "$(fa --init bash)"
  --config          cria ou mostra ~/.config/fa/config.toml (qual modelo usar)
  --config chave=valor ...   muda a configuração sem editar o arquivo
  --testar          mostra o que está valendo e faz um pedido de teste
  --agente          instruções pra um agente de IA configurar o fa
  --reconhecer      lê esta máquina uma vez pro contexto (~/.config/fa/sistema.txt)
  --servico         deixa o pi sempre aberto, como serviço do systemd (provedor pi)
  --traduzir ...    só imprime o comando, sem pôr na linha
  --versao
"""


def ajuda():
    texto = USO
    pac = contexto.pacotes()
    if pac:
        texto += "\npacotes de exemplos (flags):\n" + "".join(
            f"  -{letra}  {nome}\n" for letra, nome in sorted(pac.items()))
    return texto


def traduzir(args):
    pac, nomes = contexto.pacotes(), []
    while args and args[0].startswith("-") and len(args[0]) > 1:
        for letra in args.pop(0)[1:]:
            if letra not in pac:
                raise Erro(f"flag -{letra} não existe\n\n{ajuda()}")
            nomes.append(pac[letra])
    if not args:
        raise Erro(ajuda())
    cfg = config.carregar()
    resposta = provedores.chamar(cfg, contexto.sistema(), contexto.pedido(" ".join(args), nomes))
    cmd = contexto.limpar(resposta)
    if not cmd:
        raise Erro("o modelo não devolveu comando")
    return cmd


def mostrar_config():
    if not config.ARQUIVO.exists():
        config.criar()
        print(f"criei {config.ARQUIVO} com o palpite desta máquina:\n")
    else:
        print(f"{config.ARQUIVO}:\n")
    print(config.ARQUIVO.read_text())
    if not contexto.SISTEMA.exists():
        print("dica: fa --reconhecer lê esta máquina (distribuição, rede, ferramentas) e melhora as respostas")


def testar():
    """Diz o que está valendo e faz um pedido de verdade. Sai com erro se não funcionar."""
    cfg = config.carregar()
    print(f"config: {config.ARQUIVO if config.ARQUIVO.exists() else 'nenhum arquivo, palpite pelas chaves no ambiente'}")
    print(f"provedor: {cfg['provedor']} · modelo: {cfg.get('modelo') or 'padrão do provedor'}")
    if cfg["provedor"] == "pi":
        print("serviço do pi: " + ("no ar" if pi.SOCK.exists() else "desligado (fa --servico deixa ~3 s mais rápido)"))
    print(f"reconhecimento da máquina: {'sim' if contexto.SISTEMA.exists() else 'não (fa --reconhecer melhora as respostas)'}")
    inicio = time.monotonic()
    cmd = traduzir(["lista", "os", "arquivos", "daqui"])
    print(f"ok: 'lista os arquivos daqui' → {cmd}  ({(time.monotonic() - inicio) * 1000:.0f} ms)")


def instalar(args):
    """fa --instalar [provedor]: liga o fa no shell, escolhe o provedor e testa. Pode rodar de novo."""
    shell = Path(os.environ.get("SHELL", "bash")).name
    if shell not in ("bash", "zsh"):
        raise Erro(f"shell {shell} ainda não tem integração (tem: bash, zsh)")
    linha = f'eval "$(fa --init {shell})"'
    rc = Path.home() / (".zshrc" if shell == "zsh" else ".bashrc")
    lidos = [rc, *sorted((Path.home() / ".bashrc.d").glob("*"))] if shell == "bash" else [rc]
    if any(f.is_file() and "fa --init" in f.read_text(errors="ignore") for f in lidos):
        print(f"shell: o fa já carrega no {shell}")
    else:
        with rc.open("a") as f:
            f.write(f"\n# fa: pedido em linguagem natural vira comando\n{linha}\n")
        print(f"shell: acrescentei ao {rc}: {linha}")

    if args:
        config.ajustar([f"provedor={args[0]}", *args[1:]])
    elif not config.ARQUIVO.exists():
        palpite = config.adivinhar()
        if palpite is None:
            raise Erro("não achei chave de API nem claude/codex/agy/pi instalado. Diga qual usar: fa --instalar claude")
        config.ajustar([f"{k}={v}" for k, v in palpite.items()])
    print(f"provedor: {config.carregar()['provedor']} (troque com: fa --instalar <provedor>)")

    pasta_bin = str(Path(shutil.which("fa") or sys.argv[0]).resolve().parent)
    if pasta_bin not in os.environ.get("PATH", "").split(":"):
        print(f"atenção: {pasta_bin} não está no PATH; o shell não vai achar o fa")
    print()
    testar()
    print("\npronto. Abra um terminal novo e peça, por exemplo: fa mostra os 5 maiores arquivos daqui")


def reconhecer():
    subprocess.run(["bash", str(contexto.DADOS / "reconhecer.sh")], check=False)


def servico():
    if not shutil.which("systemctl"):
        raise Erro("sem systemd aqui; rode fa --servir num terminal à parte")
    fa = shutil.which("fa") or str(Path(sys.argv[0]).resolve())
    unidade = Path.home() / ".config/systemd/user/fa.service"
    unidade.parent.mkdir(parents=True, exist_ok=True)
    unidade.unlink(missing_ok=True)  # versões antigas do fa deixavam um link aqui
    unidade.write_text(f"""\
[Unit]
Description=fa: pi sempre aberto pra traduzir pedidos em comandos

[Service]
ExecStart={fa} --servir
Environment=PATH={os.environ.get("PATH", "/usr/bin:/bin")}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
""")
    for cmd in (["daemon-reload"], ["enable", "fa.service"], ["restart", "fa.service"]):
        subprocess.run(["systemctl", "--user", *cmd], check=True)
    print(f"serviço fa ligado ({unidade})")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            print(ajuda(), file=sys.stderr)
            return 1
        op = args[0]
        if op in ("-h", "--help", "--ajuda"):
            print(ajuda())
        elif op in ("--versao", "--version"):
            print(f"fa (fala) {__version__}")
        elif op == "--init":
            shell = args[1] if len(args) > 1 else Path(os.environ.get("SHELL", "bash")).name
            arq = contexto.DADOS / f"fa.{shell}"
            if not arq.exists():
                raise Erro(f"shell {shell} ainda não tem integração (tem: bash, zsh)")
            print(arq.read_text())
        elif op == "--config" and len(args) > 1:
            config.ajustar(args[1:])
            print(config.ARQUIVO.read_text(), end="")
        elif op == "--config":
            mostrar_config()
        elif op == "--instalar":
            instalar(args[1:])
        elif op == "--testar":
            testar()
        elif op == "--agente":
            print((contexto.DADOS / "AGENTS.md").read_text())
        elif op == "--reconhecer":
            reconhecer()
        elif op == "--servir":
            pi.servir(config.carregar(), contexto.sistema())
        elif op == "--servico":
            servico()
        elif op == "--traduzir":
            print(traduzir(args[1:]))
        elif op.startswith("--"):
            raise Erro(f"opção {op} não existe\n\n{ajuda()}")
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
