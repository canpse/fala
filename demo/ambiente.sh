# Carregado escondido no começo da gravação: prompt limpo, fa no shell, pasta da demo.
# Uso: source demo/ambiente.sh /tmp/projeto
PS1="\[\e[1;36m\]$(basename "$1")\[\e[0m\] \$ "
eval "$(fa --init bash)"
cd "$1"
clear
