# fa for bash: the command shows up on your prompt to check; Enter runs it, erasing the line (or Ctrl+C) cancels.
# Load with: eval "$(fa --init bash)"
fa() {
    case "${1:-}" in
        ""|-h|--*) command fa "$@"; return ;;
    esac
    local cmd linha
    printf '\e[2m@THINKING@\e[0m' >&2
    cmd=$(command fa --translate "$@") || return
    printf '\r\e[K' >&2
    read -e -r -i "$cmd" -p $'\e[33mfa>\e[0m ' linha || { echo; return 130; }
    [ -z "$linha" ] && return 0
    history -s "fa $*"
    history -s "$linha"
    eval "$linha"
}
