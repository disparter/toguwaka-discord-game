# Story Mode System

Este diretório contém a implementação do sistema de modo história para o jogo Academia Tokugawa, seguindo os princípios SOLID de design de software.

## Estrutura do Diretório

```
story_mode/
├── interfaces.py     # Interfaces para os componentes do sistema
├── chapter.py        # Implementações de capítulos
├── event.py          # Implementações de eventos
├── npc.py            # Implementações de NPCs
├── progress.py       # Gerenciamento de progresso do jogador
└── story_mode.py     # Classe principal que coordena os componentes
```

## Arquivos de Dados

Os dados do modo história são armazenados em arquivos JSON nos seguintes diretórios:

```
data/story_mode/
├── chapters/         # Definições de capítulos
├── events/           # Definições de eventos
└── npcs/             # Definições de NPCs
```

## Componentes Principais

### Interfaces (interfaces.py)

Define as interfaces para os principais componentes do sistema:

- `Chapter`: Interface para capítulos da história
- `Event`: Interface para eventos
- `NPC`: Interface para personagens não-jogáveis
- `ChapterLoader`: Interface para carregar capítulos
- `EventManager`: Interface para gerenciar eventos
- `StoryProgressManager`: Interface para gerenciar o progresso do jogador

### Capítulos (chapter.py)

Implementações da interface `Chapter`:

- `BaseChapter`: Implementação base com funcionalidades comuns
- `StoryChapter`: Capítulo padrão da história
- `ChallengeChapter`: Capítulo de desafio com mecânicas especiais
- `BranchingChapter`: Capítulo com múltiplos caminhos baseados nas escolhas do jogador

### Eventos (event.py)

Implementações da interface `Event`:

- `BaseEvent`: Implementação base com funcionalidades comuns
- `ClimacticEvent`: Evento climático com grande impacto na história
- `RandomEvent`: Evento aleatório que pode ocorrer a qualquer momento
- `SeasonalEvent`: Evento sazonal que ocorre em períodos específicos do ano

Também inclui o `DefaultEventManager`, uma implementação da interface `EventManager`.

### NPCs (npc.py)

Implementações da interface `NPC`:

- `BaseNPC`: Implementação base com funcionalidades comuns
- `StudentNPC`: NPC estudante com atributos específicos
- `FacultyNPC`: NPC membro da faculdade com atributos específicos

Também inclui o `NPCManager`, uma classe para gerenciar NPCs.

### Progresso (progress.py)

Implementação da interface `StoryProgressManager`:

- `DefaultStoryProgressManager`: Gerencia o progresso do jogador na história

### Modo História (story_mode.py)

A classe principal que coordena todos os componentes:

- `FileChapterLoader`: Carrega capítulos de arquivos JSON
- `StoryMode`: Classe principal que gerencia o fluxo da história

## Como Usar

### Inicialização

```python
from story_mode.story_mode import StoryMode

# Inicializa o sistema de modo história
story_mode = StoryMode()
```

### Iniciar ou Continuar a História

```python
# Obtém os dados do jogador do banco de dados
player_data = get_player(user_id)

# Inicia ou continua a história
result = story_mode.start_story(player_data)

# Atualiza os dados do jogador no banco de dados
update_player(user_id, story_progress=json.dumps(result["player_data"]["story_progress"]))
```

### Processar Escolhas do Jogador

```python
# Obtém os dados do jogador do banco de dados
player_data = get_player(user_id)

# Processa a escolha do jogador
result = story_mode.process_choice(player_data, choice_index)

# Atualiza os dados do jogador no banco de dados
update_player(user_id, story_progress=json.dumps(result["player_data"]["story_progress"]))
```

### Disparar Eventos

```python
# Obtém os dados do jogador do banco de dados
player_data = get_player(user_id)

# Dispara um evento
result = story_mode.trigger_event(player_data, event_id)

# Atualiza os dados do jogador no banco de dados
update_player(user_id, story_progress=json.dumps(result["player_data"]["story_progress"]))
```

### Atualizar Afinidade com NPCs

```python
# Obtém os dados do jogador do banco de dados
player_data = get_player(user_id)

# Atualiza a afinidade com um NPC
result = story_mode.update_affinity(player_data, npc_name, change)

# Atualiza os dados do jogador no banco de dados
update_player(user_id, story_progress=json.dumps(result["player_data"]["story_progress"]))
```

### Obter Status da História

```python
# Obtém os dados do jogador do banco de dados
player_data = get_player(user_id)

# Obtém o status da história
status = story_mode.get_story_status(player_data)
```

## Extensão do Sistema

### Adicionando Novos Capítulos

1. Crie um arquivo JSON em `data/story_mode/chapters/` com a definição do capítulo.
2. Se necessário, crie uma nova classe que herde de `BaseChapter` para implementar comportamentos específicos.

### Adicionando Novos Eventos

1. Crie um arquivo JSON em `data/story_mode/events/` com a definição do evento.
2. Se necessário, crie uma nova classe que herde de `BaseEvent` para implementar comportamentos específicos.

### Adicionando Novos NPCs

1. Crie um arquivo JSON em `data/story_mode/npcs/` com a definição do NPC.
2. Se necessário, crie uma nova classe que herde de `BaseNPC` para implementar comportamentos específicos.

## Integração com o Discord

O sistema de modo história é integrado ao bot do Discord através do cog `StoryModeCog` em `cogs/story_mode.py`. Este cog implementa comandos slash para interagir com o sistema:

- `/historia`: Inicia ou continua o modo história
- `/status_historia`: Mostra o status atual do progresso na história
- `/relacionamento [personagem] [afinidade]`: Mostra ou altera relacionamentos com NPCs
- `/evento [evento_id]`: Participa de eventos disponíveis

## Documentação Adicional

Para uma documentação mais detalhada sobre o sistema de modo história, consulte o arquivo `STORY_MODE_DOCUMENTATION.md` na raiz do projeto.
