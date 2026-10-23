# fa no bash: o comando aparece na linha pra conferir; Enter executa, apagar a linha (ou Ctrl+C) cancela.
# Carregue com: eval "$(fa --init bash)"
fa() {
    case "${1:-}" in
        ""|-h|--*) command fa "$@"; return ;;
    esac
    local cmd linha
    printf '\e[2mpensando…\e[0m' >&2
    cmd=$(command fa --traduzir "$@") || return
    printf '\r\e[K' >&2
    read -e -r -i "$cmd" -p $'\e[33mfa>\e[0m ' linha || { echo; return 130; }
    [ -z "$linha" ] && return 0
    history -s "fa $*"
    history -s "$linha"
    eval "$linha"
}
