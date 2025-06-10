# Story Mode System

Este diretório contém a implementação do sistema de modo história para o jogo Academia Tokugawa, seguindo os princípios SOLID de design de software.

## Estrutura do Diretório

```
story_mode/
├── interfaces.py          # Interfaces para os componentes do sistema
├── chapter.py             # Implementações de capítulos
├── chapter_validator.py   # Validação básica de estrutura de capítulos
├── club_system.py         # Sistema expandido de clubes
├── consequences.py        # Sistema de consequências dinâmicas
├── decision_dashboard.py  # Dashboard de comparação de decisões
├── event.py               # Implementações de eventos
├── narrative_validator.py # Validação de caminhos narrativos
├── npc.py                 # Implementações de NPCs
├── progress.py            # Gerenciamento de progresso do jogador
├── validation.py          # Validação em tempo de execução
└── story_mode.py          # Classe principal que coordena os componentes
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

## Novas Funcionalidades

### 1. Sistema de Validação Automatizada de Caminhos Narrativos

O sistema de validação automatizada verifica a integridade e correção dos caminhos narrativos no modo história.

#### Funcionalidades

- **Verificação de Integridade de Caminhos**: Garante que todos os caminhos narrativos levem a destinos válidos.
- **Detecção de Referências Quebradas**: Identifica referências a capítulos inexistentes.
- **Validação de Uso de Variáveis**: Verifica se as variáveis usadas em condições são definidas corretamente.
- **Relatórios de Cobertura**: Gera estatísticas sobre a cobertura dos caminhos narrativos.

#### Como Usar

```python
from story_mode.narrative_validator import NarrativePathValidator

# Inicializar o validador com o diretório de capítulos
validator = NarrativePathValidator("data/story_mode/chapters")

# Carregar os capítulos
validator.load_chapters()

# Validar os caminhos narrativos
result = validator.validate_narrative_paths()

# Simular cobertura de caminhos
validator.simulate_path_coverage()

# Gerar relatório de cobertura
report = validator.generate_coverage_report()
print(f"Total de capítulos: {report['total_chapters']}")
print(f"Total de caminhos: {report['total_paths']}")
print(f"Caminhos cobertos: {report['covered_paths']}")
print(f"Porcentagem de cobertura: {report['coverage_percentage']:.2f}%")
```

#### Linha de Comando

Você também pode executar o validador pela linha de comando:

```bash
python -m story_mode.narrative_validator data/story_mode/chapters
```

### 2. Sistema de Clubes Expandido

O sistema de clubes expandido adiciona rivalidades, alianças, competições e progressão de rank aos clubes.

#### Funcionalidades

- **Rivalidades e Alianças**: Os clubes podem formar alianças ou declarar rivalidades com outros clubes.
- **Competições entre Clubes**: Os clubes podem organizar e participar de competições.
- **Progressão de Rank**: Os jogadores podem subir de rank dentro de seus clubes.
- **Missões Específicas de Clubes**: Cada clube tem missões específicas para seus membros.

#### Como Usar

```python
from story_mode.club_rivalry_system import get_club_system
from story_mode.story_consequences import DynamicConsequencesSystem

# Obter o sistema de consequências (opcional)
consequences_system = DynamicConsequencesSystem()

# Obter o sistema de clubes
club_system = get_club_system(consequences_system)

# Inicializar dados de clube para um jogador
club_system.initialize_player_club_data(player_data)

# Entrar em um clube
club_system.join_club(player_data, club_id=1)  # 1 = Clube das Chamas

# Obter informações do clube
club_info = club_system.get_club_info(player_data)
print(f"Clube: {club_info['name']}")
print(f"Rank: {club_info['rank_name']}")

# Adicionar experiência e subir de rank
result = club_system.add_club_experience(player_data, 100)
if result.get("rank_up"):
    print(f"Parabéns! Você subiu para o rank {result['rank_name']}!")

# Completar uma missão
mission_id = player_data["club"]["pending_missions"][0]["id"]
result = club_system.complete_mission(player_data, mission_id)
print(f"Missão completada: {result['mission_completed']['title']}")
print(f"Nova missão: {result['new_mission']['title']}")

# Criar uma competição (requer rank 3+)
if player_data["club"]["rank"] >= 3:
    competition = club_system.create_club_competition(player_data, opponent_club_id=2)
    print(f"Competição criada: {competition['title']}")

    # Resolver a competição
    result = club_system.resolve_competition(player_data, competition["id"])
    print(result["message"])

# Formar uma aliança (requer rank 4+)
if player_data["club"]["rank"] >= 4:
    alliance = club_system.form_alliance(player_data, ally_club_id=4)
    print(alliance["message"])

# Declarar uma rivalidade (requer rank 4+)
if player_data["club"]["rank"] >= 4:
    rivalry = club_system.declare_rivalry(player_data, rival_club_id=2)
    print(rivalry["message"])
```

### 3. Dashboard de Comparação de Decisões

O dashboard de comparação de decisões permite aos jogadores comparar suas escolhas com as da comunidade e refletir sobre as implicações éticas de suas decisões.

#### Funcionalidades

- **Rastreamento de Escolhas**: Registra as escolhas dos jogadores e agrega estatísticas da comunidade.
- **Comparação com a Comunidade**: Permite aos jogadores comparar suas escolhas com as da comunidade.
- **Reflexões Éticas**: Oferece prompts de reflexão ética baseados nas escolhas do jogador.
- **Caminhos Alternativos**: Mostra caminhos alternativos que o jogador poderia ter seguido.
- **Análise de Padrões**: Analisa os padrões de escolha do jogador para identificar traços de personalidade.

#### Como Usar

```python
from story_mode.decision_dashboard import get_decision_tracker

# Obter o rastreador de decisões
decision_tracker = get_decision_tracker()

# Registrar uma escolha do jogador
decision_tracker.record_player_choice(
    player_data,
    chapter_id="1_1",
    choice_key="choice_1",
    choice_text="Eu quero aprender mais sobre esse poder."
)

# Obter comparação com a comunidade
comparison = decision_tracker.get_community_comparison(
    player_data,
    chapter_id="1_1",
    choice_key="choice_1"
)
print(comparison["message"])
print(f"Sua escolha: {comparison['player_choice']}")
print(f"Porcentagem da comunidade: {comparison['player_percentage']:.1f}%")

# Obter reflexão ética
reflection = decision_tracker.get_ethical_reflection(
    player_data,
    category="power"  # Ou "loyalty", "justice", "truth", "freedom"
)
print(reflection["message"])
for prompt in reflection["reflections"]:
    print(f"- {prompt}")

# Gerar dashboard completo
dashboard = decision_tracker.generate_dashboard(player_data)
print(f"Total de escolhas feitas: {dashboard['total_choices_made']}")
print(f"Capítulos completados: {dashboard['chapters_completed']}")
```

### Testes

Testes unitários para todas as funcionalidades estão disponíveis em `tests/story_mode/test_new_features.py`. Execute-os para verificar se tudo está funcionando corretamente:

```bash
python -m unittest tests/story_mode/test_new_features.py
```
