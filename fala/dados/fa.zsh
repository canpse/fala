# fa no zsh: o comando vai pra próxima linha do prompt pra conferir; Enter executa, Ctrl+C cancela.
# Carregue com: eval "$(fa --init zsh)"
unalias fa 2>/dev/null
fa() {
    case "${1:-}" in
        ""|-h|--*) command fa "$@"; return ;;
    esac
    local cmd
    printf '\e[2mpensando…\e[0m' >&2
    cmd=$(command fa --traduzir "$@") || return
    printf '\r\e[K' >&2
    print -s -- "fa $*"
    print -z -- "$cmd"
}
# sem isso o zsh tenta expandir o ? e o * do pedido ("qual meu ip?") e reclama
alias fa='noglob fa'
