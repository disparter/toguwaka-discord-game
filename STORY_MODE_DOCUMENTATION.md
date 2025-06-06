# Academia Tokugawa - Modo História

Este documento descreve a nova implementação do modo história do jogo Academia Tokugawa, utilizando os princípios SOLID de design de software.

## Visão Geral

A nova arquitetura do modo história foi projetada para ser modular, extensível e de fácil manutenção. Ela segue os princípios SOLID:

- **S**ingle Responsibility Principle (Princípio da Responsabilidade Única)
- **O**pen/Closed Principle (Princípio Aberto/Fechado)
- **L**iskov Substitution Principle (Princípio da Substituição de Liskov)
- **I**nterface Segregation Principle (Princípio da Segregação de Interface)
- **D**ependency Inversion Principle (Princípio da Inversão de Dependência)

## Estrutura do Projeto

O sistema está organizado nos seguintes módulos:

```
story_mode/
├── interfaces.py     # Interfaces para os componentes do sistema
├── chapter.py        # Implementações de capítulos
├── event.py          # Implementações de eventos
├── npc.py            # Implementações de NPCs
├── progress.py       # Gerenciamento de progresso do jogador
└── story_mode.py     # Classe principal que coordena os componentes
```

## Componentes Principais

### Interfaces (interfaces.py)

Este arquivo define as interfaces para os principais componentes do sistema:

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

## Integração com o Discord (story_mode.py)

Um novo cog que integra o sistema de modo história com o bot do Discord:

- `StoryModeCog`: Implementa comandos slash para interagir com o sistema

## Formato dos Dados

### Capítulos

Os capítulos são definidos em arquivos JSON com a seguinte estrutura:

```json
{
  "1_1": {
    "type": "story",
    "title": "Meu Primeiro Dia de Aula",
    "description": "Seu primeiro dia na Academia Tokugawa. Conheça a escola e seus colegas.",
    "dialogues": [
      {"npc": "Diretor", "text": "Bem-vindo à Academia Tokugawa!"},
      {"npc": "Junie", "text": "Olá! Eu sou Junie, sua assistente virtual."}
    ],
    "choices": [
      {"text": "Sim, vamos conhecer os clubes!", "next_dialogue": 5},
      {"text": "Prefiro explorar por conta própria.", "next_dialogue": 6}
    ],
    "completion_exp": 50,
    "completion_tusd": 100,
    "next_chapter": "1_2"
  }
}
```

### Eventos

Os eventos são definidos em arquivos JSON com a seguinte estrutura:

```json
{
  "torneio_anual": {
    "type": "climactic",
    "name": "Torneio Anual",
    "description": "O maior evento da academia, onde estudantes de todos os anos competem por glória e reconhecimento.",
    "requirements": {"level": 10},
    "rewards": {"exp": 500, "tusd": 1000, "hierarchy_points": 3},
    "frequency": "yearly",
    "impact": "major",
    "story_changes": {"hierarchy_tier": 3}
  }
}
```

### NPCs

Os NPCs são definidos em arquivos JSON com a seguinte estrutura:

```json
{
  "kai_flameheart": {
    "type": "student",
    "name": "Kai Flameheart",
    "background": {
      "background": "Nascido em uma família de manipuladores de fogo, Kai sempre foi considerado um prodígio.",
      "motivation": "Tornar-se forte o suficiente para nunca mais perder alguém importante.",
      "secrets": "Kai esconde que, em momentos de extrema emoção, perde o controle de seus poderes."
    },
    "year": 2,
    "club_id": 1,
    "power": "Fogo",
    "hierarchy_tier": 4,
    "dialogues": {
      "greeting": {
        "default": {"text": "E aí, novato! Pronto para sentir o calor do treinamento?"},
        "friendly": {"text": "Ei, bom te ver! Como vai o treinamento?"},
        "close": {"text": "Meu amigo! Estava esperando por você!"}
      }
    }
  }
}
```

## Progresso do Jogador

O progresso do jogador é armazenado no campo `story_progress` do jogador com a seguinte estrutura:

```json
{
  "current_year": 1,
  "current_chapter": 1,
  "current_challenge_chapter": null,
  "completed_chapters": ["1_1", "1_2"],
  "completed_challenge_chapters": [],
  "available_chapters": ["1_3"],
  "club_progress": {},
  "villain_defeats": [],
  "minion_defeats": [],
  "hierarchy_tier": 1,
  "hierarchy_points": 15,
  "discovered_secrets": ["Biblioteca Proibida"],
  "special_items": ["Tomo do Conhecimento Proibido"],
  "character_relationships": {
    "Kai Flameheart": 25,
    "Luna Mindweaver": -10
  },
  "story_choices": {
    "1_1": {
      "dialogue_0_choice": 0,
      "dialogue_3_choice": 1
    }
  },
  "triggered_events": {
    "torneio_anual": "2023-07-15T14:30:00"
  }
}
```

## Como Usar

### Configuração Inicial

1. Crie os diretórios necessários:
   ```
   mkdir -p data/story_mode/chapters data/story_mode/events data/story_mode/npcs
   ```

2. Adicione arquivos JSON para capítulos, eventos e NPCs nos diretórios correspondentes.

3. Registre o cog no bot:
   ```python
   bot.load_extension("cogs.story_mode")
   ```

### Comandos do Discord

- `/historia`: Inicia ou continua o modo história
- `/status_historia`: Mostra o status atual do progresso na história
- `/relacionamento [personagem] [afinidade]`: Mostra ou altera relacionamentos com NPCs
- `/evento [evento_id]`: Participa de eventos disponíveis

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

## Princípios SOLID Aplicados

### Single Responsibility Principle

Cada classe tem uma única responsabilidade:
- `Chapter`: Gerenciar o conteúdo e progressão de um capítulo
- `Event`: Gerenciar a ocorrência e efeitos de um evento
- `NPC`: Gerenciar atributos e interações de um personagem
- `StoryProgressManager`: Gerenciar o progresso do jogador

### Open/Closed Principle

O sistema é aberto para extensão, mas fechado para modificação:
- Novas classes de capítulos, eventos e NPCs podem ser adicionadas sem modificar o código existente
- O comportamento pode ser estendido através de herança e composição

### Liskov Substitution Principle

As subclasses podem ser usadas onde as classes base são esperadas:
- Todas as implementações de `Chapter` podem ser usadas pelo `ChapterLoader`
- Todas as implementações de `Event` podem ser usadas pelo `EventManager`
- Todas as implementações de `NPC` podem ser usadas pelo `NPCManager`

### Interface Segregation Principle

As interfaces são específicas para seus casos de uso:
- `Chapter` define apenas métodos relacionados a capítulos
- `Event` define apenas métodos relacionados a eventos
- `NPC` define apenas métodos relacionados a NPCs

### Dependency Inversion Principle

Módulos de alto nível não dependem de módulos de baixo nível, ambos dependem de abstrações:
- `StoryMode` depende das interfaces `ChapterLoader`, `EventManager`, etc., não de implementações concretas
- As implementações concretas podem ser substituídas sem afetar o sistema como um todo

## Conclusão

A nova arquitetura do modo história proporciona uma base sólida para expansão futura, permitindo adicionar novos capítulos, eventos e NPCs de forma modular e sem afetar o código existente. Os princípios SOLID garantem que o sistema seja flexível, extensível e de fácil manutenção.
