#!/usr/bin/env bash
# Reconhece a máquina uma vez (na instalação) e grava ~/.config/fa/sistema.txt.
# O servidor junta esse arquivo ao prompt: o modelo começa sabendo que sistema é este.
# Rodar de novo se a máquina mudar (distribuição, rede, ferramentas instaladas).
set -u
saida="${XDG_CONFIG_HOME:-$HOME/.config}/fa/sistema.txt"
mkdir -p "$(dirname "$saida")"

# Cada comando aparece com a saída, do jeito que apareceria no terminal.
mostrar() {
    echo "\$ $*"
    timeout 5 bash -c "$*" 2>&1 | head -n 40
    echo
}

{
    echo "Estado desta máquina, lido na instalação do fa em $(date '+%d/%m/%Y %H:%M'):"
    echo
    mostrar 'cat /etc/os-release'
    mostrar 'uname -srm'
    mostrar 'hostname'
    mostrar 'id'
    mostrar 'echo $SHELL'
    mostrar 'nproc; free -h'
    mostrar 'lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS'
    mostrar 'df -h -x tmpfs -x devtmpfs -x efivarfs'
    mostrar 'ip -br addr'
    mostrar 'ip route'
    mostrar 'resolvectl dns 2>/dev/null || cat /etc/resolv.conf'
    mostrar 'nmcli -t -f NAME,TYPE,DEVICE connection show --active'
    mostrar 'systemctl list-units --type=service --state=running --no-legend --plain | cut -d" " -f1'
    mostrar 'for c in dnf apt pacman zypper flatpak snap firewall-cmd ufw iptables nft docker podman nmcli ss netstat ip ifconfig dig nslookup host traceroute tracepath nmap nc curl wget tcpdump python python3 node git; do command -v $c >/dev/null && printf "%s " $c; done; echo'
} > "$saida"

echo "fa: reconhecimento gravado em $saida ($(wc -l < "$saida") linhas)"

# Exemplos de rede desta máquina (pacote -r). Só cria se não existir: o arquivo é seu pra editar.
# Pra gerar de novo do zero: apague o arquivo e rode este script.
local_redes="$(dirname "$saida")/pacotes/redes.txt"
if [ ! -e "$local_redes" ]; then
    mkdir -p "$(dirname "$local_redes")"
    wifi=$(nmcli -t -f DEVICE,TYPE device 2>/dev/null | awk -F: '$2=="wifi"{print $1; exit}')
    cabo=$(nmcli -t -f DEVICE,TYPE device 2>/dev/null | awk -F: '$2=="ethernet"{print $1; exit}')
    instalar=$(for g in dnf apt zypper; do command -v $g >/dev/null && { echo "sudo $g install -y"; break; }; done)
    command -v pacman >/dev/null && instalar="sudo pacman -S --noconfirm"
    ativa=$(ip route show default 2>/dev/null | awk '{for(i=1;i<NF;i++) if($i=="dev"){print $(i+1); exit}}')
    {
        echo "# Exemplos de rede DESTA máquina, gerados na instalação em $(date '+%d/%m/%Y'). Edite à vontade."
        echo "# Formato: pedido => comando"
        [ -n "$ativa" ] && echo "interface ativa (a da rota padrão na instalação) => $ativa"
        [ -n "$wifi" ] && echo "captura no wifi => sudo tcpdump -i $wifi -c 20 -nn"
        [ -n "$cabo" ] && echo "captura no cabo => sudo tcpdump -i $cabo -c 20 -nn"
        [ -n "$wifi" ] && echo "meu ip no wifi => ip -br addr show $wifi"
        [ -n "$cabo" ] && echo "meu ip no cabo => ip -br addr show $cabo"
        [ -n "$cabo" ] && echo "liga o cabo => nmcli device connect $cabo"
        command -v tailscale >/dev/null && echo "status do tailscale => tailscale status"
        command -v tailscale >/dev/null && echo "meu ip no tailscale => tailscale ip -4"
        command -v firewall-cmd >/dev/null && echo "mostra o firewall => sudo firewall-cmd --list-all"
        command -v firewall-cmd >/dev/null && echo "libera uma porta no firewall => sudo firewall-cmd --permanent --add-port=3000/tcp && sudo firewall-cmd --reload"
        command -v nmap >/dev/null || echo "descobre os hosts ativos na rede => $instalar nmap && sudo nmap -sn <rede>/24"
        command -v mtr >/dev/null || echo "mede perda e latência no caminho => tracepath host   (mtr não instalado)"
    } > "$local_redes"
    echo "fa: exemplos de rede desta máquina em $local_redes (edite à vontade)"
fi
