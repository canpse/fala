# Testes

`pedidos.txt`: 64 pedidos comuns de Linux e rede, em português. Foram rodados numa pasta com
`README.md`, `main.py`, `utils.py`, `dados.csv`, `notas.txt`, `config.yaml`, `logs/app.log`,
`src/servidor.js` e `backup/antigo.tar.gz`, **sem executar** os comandos, e cada resposta foi
conferida à mão. Modelo: GPT-6 Luna sem raciocínio (provedor `pi`), Fedora 44.

| Rodada | Mudança | Certos de 64 |
|---|---|---|
| 1 | só a lista de arquivos da pasta | 50 (6 meio certos, 8 errados: `apt` no Fedora, arquivo em subpasta, gateway procurado no config.yaml) |
| 2 | sistema + 2 níveis de arquivos + regras no prompt | 63 |
| 4 | reconhecimento da máquina (`fa --reconhecer`) e regra de caminho relativo | 62 (1 meio certo, 1 errado) |
| 5 | os 28 pedidos de rede com `-r` (pacote de exemplos de redes) | 28 de 28 |

Tempo médio: 1,8 s por pedido.
