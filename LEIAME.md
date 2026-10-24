# fa

*[Read in English](README.md)*

Diga o que você quer, do seu jeito. O `fa` põe o comando na linha do terminal, você confere
e dá Enter.

![demonstração do fa: juntar PDFs, converter documento e áudio, descompactar](https://raw.githubusercontent.com/canpse/fala/main/demo/fa-pt.gif)

```
$ fa quem está escutando na porta 8080
fa> sudo ss -ltnp 'sport = :8080'
```

```
$ fa mostra os 3 maiores arquivos daqui
fa> find . -type f -printf '%s %p\n' | sort -nr | head -3
```

O terminal deixa de ser um monte de ferramentas pra decorar e vira um lugar onde você escreve
o que quer. Nada roda antes do Enter: dá pra editar a linha, ou apagar pra cancelar. O pedido
e o comando vão pro histórico, então você aprende os comandos usando.

## Instalar

**O jeito recomendado: peça ao seu agente de IA.** Mande isto pro Claude Code, pro Codex ou
pro agente que você usa:

```
Instala isso pra mim: https://github.com/canpse/fala
```

Ele lê o [AGENTS.md](AGENTS.md), instala o fa, liga no seu shell, escolhe como modelo a
assinatura em que ele mesmo está rodando e confere se funciona. Depois é só abrir um terminal
novo.

**À mão** (Python 3.11+, bash ou zsh):

```sh
pipx install fala          # ou: uv tool install fala · pip install --user fala
fa --install claude        # ou codex, agy, pi, anthropic, openai, openrouter, groq, ollama
```

O `fa --install` põe uma linha no `~/.bashrc` (ou no `~/.zshrc`), grava qual modelo usar e
faz um pedido de teste. Abra um terminal novo e pronto.

## Qual modelo

Qualquer um destes. Um modelo pequeno e rápido basta: o trabalho é transformar uma frase num
comando.

| provedor | o que usa | chave |
|---|---|---|
| `claude` | sua assinatura do Claude, pelo programa oficial `claude` | já logado |
| `codex` | sua assinatura do ChatGPT, pelo programa oficial `codex` | já logado |
| `agy` | seu login do Antigravity, pelo programa oficial `agy` | já logado |
| `pi` | o que o [pi](https://github.com/badlogic/pi-mono) tiver logado | já logado |
| `anthropic` | API da Anthropic | `ANTHROPIC_API_KEY` |
| `openai`, `openrouter`, `groq` | as APIs deles | `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY` |
| `ollama`, `compat` | modelo local, ou qualquer API no formato da OpenAI (llama.cpp, vLLM, LM Studio) | opcional |

Tempo por pedido num notebook de 4 núcleos: `pi` com `fa --service` 1,6 s, `claude` (Haiku)
3,1 s, `codex` (GPT-6 Luna, low) 4,8 s, `agy` (Gemini 3.8 Flash Low) 6,3 s.

Pra trocar: `fa --config provider=codex model=gpt-6-luna`. Pra conferir: `fa --test`.
Chave de API fica em variável de ambiente, nunca no arquivo de configuração.

**Sobre as assinaturas:** `claude`, `codex` e `agy` rodam o programa oficial que você mesmo
instalou e logou, uma vez por pedido, sem nenhuma ferramenta ligada. É uso pessoal comum
desses programas, mas cada empresa tem os próprios termos (e já mudou mais de uma vez). Pra
equipe, servidor ou produto, use chave de API.

## O que vai pro modelo

Cada pedido manda: as instruções fixas, o caminho da pasta atual, os nomes dos arquivos dela
(dois níveis, até 80) e o pedido. O conteúdo dos arquivos nunca vai.

O `fa --scan` é opcional e melhora bastante as respostas: ele lê uma vez a distribuição,
as ferramentas, as interfaces de rede e os serviços rodando, grava em
`~/.config/fa/sistema.txt`, e esse arquivo vai junto com **todo** pedido. Inclui o hostname e
os IPs locais. Leia ou edite antes de usar um provedor em que você não confia.

## Packs de exemplos

`fa -n <pedido>` junta exemplos de rede ao pedido (`fa -h` lista os packs). Um pack é um
arquivo de texto com linhas `pedido => comando` e uma linha `# flag: x`. Os seus vão em
`~/.config/fa/packs/`: é ali que você ensina ao `fa` os servidores, as interfaces e os
costumes da sua máquina.

## Comandos

```
fa <pedido>               comando na linha, Enter executa
fa -n <pedido>            com o pack de redes
fa --install [provedor]   liga no shell, escolhe o provedor e testa
fa --config chave=valor   muda a configuração · fa --config mostra
fa --test                 mostra o que está valendo e faz um pedido de teste
fa --scan                 lê esta máquina uma vez, pra respostas melhores
fa --service              deixa o pi aberto como serviço do systemd (provedor pi)
fa --translate <pedido>   só imprime o comando
fa --agent                instruções pra agentes de IA
```

## Estado

Começo (0.2.0). Testado no Fedora com bash; o zsh está escrito mas ainda não foi testado. Os
testes estão em [testes/](testes/). Pedidos em qualquer idioma; as mensagens saem em português
quando o sistema está em português. Os nomes da 0.1 (`--instalar`, `provedor=`...) continuam
valendo.

## Licença

MIT
