"""Deixa um pi aberto (modo rpc) e atende o fa por um socket unix (fa --servir).

Cada pedido começa uma sessão nova no pi, pra um pedido não ver o anterior.
"""
import json
import os
import queue
import socket
import subprocess
import sys
import threading
from pathlib import Path

from .config import CACHE

# em ~/.cache e não no XDG_RUNTIME_DIR: o lab do netlings cobre o /run, e lá dentro o socket sumia
SOCK = CACHE / "fa.sock"
LIMITE = 60  # segundos por pedido


def argumentos(cfg, sistema):
    """Opções do pi comuns ao modo rpc e ao pi -p: sem ferramentas, sem sessão, só o prompt do fa."""
    args = []
    if cfg.get("pi_provedor"):
        args += ["--provider", cfg["pi_provedor"]]
    if cfg.get("modelo"):
        args += ["--model", cfg["modelo"]]
    if cfg.get("pensamento"):
        args += ["--thinking", cfg["pensamento"]]
    return args + ["--no-tools", "--no-session", "--no-context-files", "--no-extensions",
                   "--no-skills", "--no-prompt-templates", "--offline", "--system-prompt", sistema]


class Pi:
    def __init__(self, cfg, sistema):
        self.args = ["pi", "--mode", "rpc", *argumentos(cfg, sistema)]
        self.proc = None
        self.eventos = queue.Queue()
        self.trava = threading.Lock()

    def abrir(self):
        self.proc = subprocess.Popen(self.args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, cwd=Path.home())
        self.eventos = queue.Queue()
        threading.Thread(target=self._ler, args=(self.proc, self.eventos), daemon=True).start()

    @staticmethod
    def _ler(proc, fila):
        # JSONL só com \n como separador (a doc do rpc avisa sobre leitores que quebram em U+2028)
        for linha in iter(proc.stdout.readline, b""):
            try:
                fila.put(json.loads(linha.decode()))
            except ValueError:
                pass
        fila.put(None)  # pi fechou

    def _enviar(self, cmd):
        self.proc.stdin.write((json.dumps(cmd) + "\n").encode())
        self.proc.stdin.flush()

    def _esperar(self, fim):
        while True:
            e = self.eventos.get(timeout=LIMITE)
            if e is None:
                raise RuntimeError("o pi fechou")
            if e.get("type") == "response" and not e.get("success", True):
                raise RuntimeError(e.get("error", "pi recusou o comando"))
            if fim(e):
                return e

    def pedir(self, texto):
        with self.trava:
            if self.proc is None or self.proc.poll() is not None:
                self.abrir()
            try:
                self._enviar({"type": "new_session"})
                self._esperar(lambda e: e.get("type") == "response" and e.get("command") == "new_session")
                self._enviar({"type": "prompt", "message": texto})
                partes = []

                def fim(e):
                    if e.get("type") == "message_update":
                        d = e.get("assistantMessageEvent", {})
                        if d.get("type") == "text_delta":
                            partes.append(d.get("delta", ""))
                    return e.get("type") == "agent_end"

                self._esperar(fim)
                return "".join(partes)
            except (RuntimeError, queue.Empty, BrokenPipeError):
                self.proc.kill()
                self.proc = None
                raise


def servir(cfg, sistema):
    pi = Pi(cfg, sistema)
    pi.abrir()
    SOCK.parent.mkdir(parents=True, exist_ok=True)
    SOCK.unlink(missing_ok=True)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(str(SOCK))
    os.chmod(SOCK, 0o600)
    srv.listen()

    def atender(con):
        with con:
            pedido = con.makefile("rb").readline().decode()
            try:
                resposta = pi.pedir(json.loads(pedido)["pedido"])
            except Exception as erro:
                resposta = ""
                print("erro:", erro, file=sys.stderr, flush=True)
            con.sendall(resposta.encode())

    while True:
        con, _ = srv.accept()
        threading.Thread(target=atender, args=(con,), daemon=True).start()


def pedir(texto):
    """Resposta do servidor, ou None se ele não está no ar."""
    try:
        con = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        con.connect(str(SOCK))
    except OSError:
        return None
    with con:
        con.sendall((json.dumps({"pedido": texto}) + "\n").encode())
        con.shutdown(socket.SHUT_WR)
        resposta = b""
        while dado := con.recv(65536):
            resposta += dado
    return resposta.decode() or None
