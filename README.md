# Caça-Números

Protótipo 2D dividido em fases: colete 10 números na Fase 1; a meta cresce em 2 a cada fase. Cada número perde valor durante a queda e pode ficar negativo.

## Executar

No PowerShell, dentro desta pasta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Use **A/D** ou as **setas** para mover. **W**, **seta para cima** ou **Espaço** pula — há dois pulos antes de tocar o chão. Ao concluir uma fase, use **Enter** ou **Espaço** para avançar. Pressione **Esc** para sair; após Game Over, use **R**, **Enter** ou **Espaço** para reiniciar.

## Estrutura

- `main.py`: ponto de entrada.
- `game.py`: loop, eventos, atualização e desenho.
- `player.py`: movimento, gravidade e pulo único.
- `falling_number.py`: queda e redução individual dos números.
- `settings.py`: constantes visuais e de jogabilidade.
- `high_scores.py`: placar local persistente (os 10 melhores resultados).

## Placar

No *Game Over*, se o resultado entrar no **Top 10**, digite três letras para
registrá-lo. O placar mostra pontos, fase e iniciais, e é ordenado por: mais
pontos, maior fase e, persistindo o empate, resultado mais recente. Ele fica em
`data/high_scores.json`, criada automaticamente ao primeiro registro.

## Publicar para jogadores

Para este jogo em Pygame, a opção mais direta é gerar uma versão portátil para
Windows e publicar o arquivo `.zip` no [itch.io](https://itch.io). O site dá
uma página para o jogo, screenshots, instruções e downloads, sem exigir que o
jogador instale Python.

Na máquina de desenvolvimento, instale o empacotador e crie a versão de
distribuição:

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name SpaceMiner main.py
```

Envie o conteúdo de `dist/SpaceMiner/` compactado em `.zip`. Teste esse `.zip`
em outra pasta antes de publicar. O ranking atual é local a cada instalação; um
ranking mundial exige um servidor/API para guardar e validar os resultados.

## Versão online com ranking global

Este repositório já contém a configuração para **Pygbag + Supabase + GitHub
Pages**. A versão desktop continua igual: execute `python main.py`. No navegador,
o mesmo `main.py` usa o loop assíncrono exigido pelo Pygbag e envia o placar à
Edge Function do Supabase.

### 1. Criar e configurar o Supabase

1. Crie um projeto no [Supabase](https://supabase.com/dashboard).
2. No SQL Editor, execute o conteúdo de
   `supabase/migrations/20260930_create_leaderboard.sql`.
3. Instale a [Supabase CLI](https://supabase.com/docs/guides/cli), entre na sua
   conta e vincule a pasta ao projeto criado.
4. Publique a API com `supabase functions deploy leaderboard`.
5. Em `web_config.py`, preencha `SUPABASE_FUNCTION_URL` com
   `https://SEU-PROJETO.supabase.co/functions/v1/leaderboard` e
   `SUPABASE_PUBLISHABLE_KEY` com a chave **publishable** mostrada em Settings →
   API Keys. Essa chave é pública; jamais coloque uma chave secret ou
   `service_role` nesse arquivo.

A tabela não dá acesso direto ao navegador: apenas a Edge Function pode ler e
gravar os resultados. Ela devolve e mantém somente as dez primeiras posições,
usando pontos, fase e data como critérios de ordenação.

### 2. Publicar no GitHub Pages

1. Crie um repositório no GitHub e envie este projeto para ele (a branch atual é
   `master`).
2. No repositório, abra **Settings → Pages** e selecione **GitHub Actions** como
   fonte de publicação.
3. Faça push para `master`. O workflow
   `.github/workflows/deploy-pages.yml` instala Pygbag, gera `build/web` e o
   publica. A aba **Actions** mostrará a URL final.

Para testar antes do push, instale Pygbag e gere a versão web:

```powershell
python -m pip install pygbag
python tools/build_web_source.py
python -m pygbag --ume_block=0 .web-source
```

Abra o endereço local informado pelo Pygbag no navegador. O diretório `build/`
é gerado dentro de `.web-source/` e não deve ser versionado.

### Proteção contra fraude

O servidor impede acesso direto ao banco e valida formato, limites e ordenação,
mas um navegador ainda pode ser alterado por alguém experiente para enviar uma
pontuação falsa. Para um placar competitivo, a evolução correta é enviar o seed
e as ações da partida para a API, que reproduz e valida a partida no servidor.

Para evoluir, crie módulos como `enemies.py`, `level.py` e `ui.py`; mantenha o ciclo `handle_events → update → draw` em `game.py`.
