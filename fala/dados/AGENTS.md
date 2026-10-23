# fa: instruções para agentes de IA

O `fa` (pacote `fala`) transforma um pedido em linguagem natural num comando de terminal:
`fa mostra os 5 maiores arquivos` põe `find . -type f ... | head -5` na linha do shell, e a
pessoa confere e dá Enter. Se te pediram para instalar ou configurar o fa, siga isto.
Estas instruções também saem com `fa --agente`.

## 1. Instalar: dois comandos

```sh
pipx install fala                  # ou: uv tool install fala · pip install --user fala
fa --instalar claude               # ou codex, agy, pi, anthropic, openrouter... (ver tabela)
```

`fa --instalar` põe `eval "$(fa --init bash)"` no `~/.bashrc` (ou o de zsh no `~/.zshrc`),
grava o provedor e faz um pedido de teste. Pode rodar de novo sem duplicar nada. Sem
provedor, ele escolhe pelo que achar na máquina (chave de API no ambiente, ou claude/codex/agy/pi
instalado). Termina com `ok: ...` quando funcionou; senão diz o que falta, por exemplo
`o claude falhou: Not logged in`: aí peça à pessoa para entrar no programa (`claude`, depois
`/login`) e rode de novo. Precisa de Python 3.11 ou mais novo. A integração só vale em
terminal aberto depois: avise a pessoa para abrir um novo (ou `source ~/.bashrc`).

Para que serve cada provedor, ou para ajustar depois, veja a seção 2.

## 2. Configurar: `fa --config chave=valor ...`

Não precisa editar arquivo. O comando grava `~/.config/fa/config.toml` e mostra como ficou.
Trocar de `provedor` apaga as chaves do provedor anterior, então passe o `modelo` junto.
`chave=` (vazio) apaga uma chave.

| chave | o que é |
|---|---|
| `provedor` | API: `anthropic`, `openai`, `openrouter`, `groq`, `ollama`, `compat`. Assinatura (programa oficial já logado, sem chave): `claude`, `codex`, `agy`, `pi` |
| `modelo` | nome do modelo no provedor (obrigatório nas APIs, exceto `anthropic`; nas assinaturas vale o padrão abaixo) |
| `url` | só `compat`: endereço da API no formato da OpenAI, ex. `http://localhost:8080/v1` |
| `chave_env` | nome da variável de ambiente com a chave, se não for a padrão |
| `pensamento` | nível de raciocínio do programa: `--thinking` do pi, `--effort` do claude e do agy, `model_reasoning_effort` do codex |
| `pi_provedor` | só `pi`: o `--provider` do pi |
| `tempo_limite` | segundos até desistir (padrão 30) |

Variável padrão da chave: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`,
`GROQ_API_KEY`. O `ollama` não usa chave.

**A chave nunca vai no config.toml.** Ela fica numa variável de ambiente. Se a pessoa ainda
não tem a variável, peça a ela para pôr no `~/.bashrc` (ou onde guarda segredos); não escreva
a chave você mesmo em arquivo nenhum sem ela pedir.

**Assinatura em vez de chave.** Se a pessoa já usa Claude Code, Codex ou Antigravity (`agy`)
logado, o fa chama esse programa uma vez por pedido, sem ferramentas e numa pasta neutra.
Confira o login antes (`claude -p oi`, `codex exec oi`, `agy -p=oi`). Padrões e tempo medido
num notebook comum: `claude` → haiku, ~3 s · `codex` → gpt-6-luna com `low`, ~5 s · `agy` →
gemini-3.8-flash-low, ~6 s · `pi` com `fa --servico` → ~2 s.

Exemplos:

```sh
fa --config provedor=anthropic modelo=claude-haiku-5-5
fa --config provedor=openrouter modelo=google/gemma-4-31b-it
fa --config provedor=ollama modelo=qwen2.5:7b tempo_limite=120
fa --config provedor=compat url=http://localhost:8080/v1 modelo=local chave_env=MINHA_CHAVE
fa --config provedor=claude                      # assinatura do Claude, modelo haiku
fa --config provedor=codex modelo=gpt-6-luna pensamento=low
fa --config provedor=pi pi_provedor=openai-codex modelo=gpt-6-luna pensamento=off
```

Para escolher: modelos pequenos e rápidos bastam (é só traduzir uma frase num comando). O que
importa é a latência: prefira um modelo sem raciocínio longo. Com `pi`, rode também
`fa --servico` (deixa o pi aberto como serviço do systemd e economiza ~3 s por pedido).
Modelo local precisa de máquina boa: o contexto tem alguns milhares de tokens.

## 3. Conferir: `fa --testar`

Mostra a configuração valendo e faz um pedido de verdade. Sai com código 0 e
`ok: ... → <comando>` se funcionou; senão sai com 1 e diz o que falta (chave vazia, chave
recusada, modelo faltando, sem resposta). Rode sempre depois de configurar.

## 4. Opcional

- `fa --reconhecer`: lê a máquina uma vez (distribuição, rede, ferramentas instaladas) para
  o contexto. Melhora bastante as respostas. **Manda hostname, IPs e a lista de serviços para
  o provedor a cada pedido**: avise a pessoa antes de rodar.
- Pacotes de exemplos: `~/.config/fa/pacotes/<nome>.txt`, linhas `pedido => comando`, com uma
  linha `# flag: x` para ativar com `fa -x <pedido>`. `fa -h` lista os que existem.

## O que não fazer

- Não execute os comandos que o fa sugere no lugar da pessoa: ele existe para ela conferir.
- Não ponha chave de API no config.toml, no histórico do shell ou em mensagem de commit.
