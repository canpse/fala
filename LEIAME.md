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

Precisa de Python 3.11 ou mais novo e de bash ou zsh.

```sh
pipx install fala          # ou: uv tool install fala · pip install --user fala
fa --instalar claude       # ou codex, agy, pi, anthropic, openai, openrouter, groq, ollama
```

O `fa --instalar` põe uma linha no `~/.bashrc` (ou no `~/.zshrc`), grava qual modelo usar e
faz um pedido de teste. Abra um terminal novo e pronto.

**Ou peça ao seu agente:** "instala o fa (github.com/canpse/fala) usando minha assinatura do
Claude". As instruções que ele precisa estão no [AGENTS.md](AGENTS.md) e em `fa --agente`.

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

Tempo por pedido num notebook de 4 núcleos: `pi` com `fa --servico` 1,6 s, `claude` (Haiku)
3,1 s, `codex` (GPT-6 Luna, low) 4,8 s, `agy` (Gemini 3.8 Flash Low) 6,3 s.

Pra trocar: `fa --config provedor=codex modelo=gpt-6-luna`. Pra conferir: `fa --testar`.
Chave de API fica em variável de ambiente, nunca no arquivo de configuração.

**Sobre as assinaturas:** `claude`, `codex` e `agy` rodam o programa oficial que você mesmo
instalou e logou, uma vez por pedido, sem nenhuma ferramenta ligada. É uso pessoal comum
desses programas, mas cada empresa tem os próprios termos (e já mudou mais de uma vez). Pra
equipe, servidor ou produto, use chave de API.

## O que vai pro modelo

Cada pedido manda: as instruções fixas, o caminho da pasta atual, os nomes dos arquivos dela
(dois níveis, até 80) e o pedido. O conteúdo dos arquivos nunca vai.

O `fa --reconhecer` é opcional e melhora bastante as respostas: ele lê uma vez a distribuição,
as ferramentas, as interfaces de rede e os serviços rodando, grava em
`~/.config/fa/sistema.txt`, e esse arquivo vai junto com **todo** pedido. Inclui o hostname e
os IPs locais. Leia ou edite antes de usar um provedor em que você não confia.

## Pacotes de exemplos

`fa -r <pedido>` junta exemplos de rede ao pedido (`fa -h` lista os pacotes). Um pacote é um
arquivo de texto com linhas `pedido => comando` e uma linha `# flag: x`. Os seus vão em
`~/.config/fa/pacotes/`: é ali que você ensina ao `fa` os servidores, as interfaces e os
costumes da sua máquina.

## Comandos

```
fa <pedido>               comando na linha, Enter executa
fa -r <pedido>            com o pacote de redes
fa --instalar [provedor]  liga no shell, escolhe o provedor e testa
fa --config chave=valor   muda a configuração · fa --config mostra
fa --testar               mostra o que está valendo e faz um pedido de teste
fa --reconhecer           lê esta máquina uma vez, pra respostas melhores
fa --servico              deixa o pi aberto como serviço do systemd (provedor pi)
fa --traduzir <pedido>    só imprime o comando
fa --agente               instruções pra agentes de IA
```

## Estado

Começo (0.1.1). Testado no Fedora com bash; o zsh está escrito mas ainda não foi testado. Os
testes estão em [testes/](testes/).

## Licença

MIT
