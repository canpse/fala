# fa for zsh: the command goes on your next prompt line to check; Enter runs it, Ctrl+C cancels.
# Load with: eval "$(fa --init zsh)"
unalias fa 2>/dev/null
fa() {
    case "${1:-}" in
        ""|-h|--*) command fa "$@"; return ;;
    esac
    local cmd
    printf '\e[2m@THINKING@\e[0m' >&2
    cmd=$(command fa --translate "$@") || return
    printf '\r\e[K' >&2
    print -s -- "fa $*"
    print -z -- "$cmd"
}
# without this zsh tries to expand the ? and * in the request ("what's my ip?") and complains
alias fa='noglob fa'
