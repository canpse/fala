"""Mensagens em inglês por padrão; em português quando o sistema está em português."""
import os


def _portugues():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        valor = os.environ.get(var)
        if valor:
            return valor.startswith("pt")
    return False


PT = _portugues()


def t(en, pt):
    return pt if PT else en
