# Academia Tokugawa - Modo História

Este documento descreve a implementação do modo história do jogo Academia Tokugawa, utilizando os princípios SOLID de design de software. O modo história oferece aos jogadores uma experiência narrativa imersiva e interativa dentro do universo do jogo.

## Índice

- [Visão Geral](#visão-geral)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Componentes Principais](#componentes-principais)
  - [Interfaces](#interfaces-interfacespy)
  - [Capítulos](#capítulos-chapterpy)
  - [Eventos](#eventos-eventpy)
  - [NPCs](#npcs-npcpy)
  - [Progresso](#progresso-progresspy)
  - [Modo História](#modo-história-story_modepy)
- [Integração com o Discord](#integração-com-o-discord-story_modepy)
- [Formato dos Dados](#formato-dos-dados)
  - [Capítulos](#capítulos)
  - [Eventos](#eventos)
  - [NPCs](#npcs)
- [Progresso do Jogador](#progresso-do-jogador)
- [Como Usar](#como-usar)
  - [Configuração Inicial](#configuração-inicial)
  - [Comandos do Discord](#comandos-do-discord)
- [Extensão do Sistema](#extensão-do-sistema)
  - [Adicionando Novos Capítulos](#adicionando-novos-capítulos)
  - [Adicionando Novos Eventos](#adicionando-novos-eventos)
  - [Adicionando Novos NPCs](#adicionando-novos-npcs)
- [Princípios SOLID Aplicados](#princípios-solid-aplicados)
- [Ferramentas de Desenvolvimento](#ferramentas-de-desenvolvimento)
- [Próximos Passos](#próximos-passos)
- [Conclusão](#conclusão)

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
  - Agora com títulos significativos (corrigindo o problema "Untitled Event")
  - Suporte para opções de diálogo e escolhas do jogador
  - Verificações de atributos com dificuldade variável
  - Recompensas e penalidades diversificadas baseadas no sucesso ou fracasso
  - Categorização por tipo e sistema de raridade
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

#### Evento Climático

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

#### Evento Aleatório Aprimorado

```json
{
  "encontro_mestre": {
    "title": "Encontro com o Mestre",
    "description": "Você encontra um mestre misterioso que oferece compartilhar sua sabedoria.",
    "type": "positive",
    "effect": {
      "attribute_check": "intellect",
      "difficulty": 7,
      "rewards": {
        "success": [
          {
            "description": "Você absorve o conhecimento avançado",
            "exp": 100,
            "intellect": 2
          },
          {
            "description": "Você aprende uma técnica secreta",
            "exp": 80,
            "power_stat": 1,
            "tusd": 50
          }
        ],
        "failure": [
          {
            "description": "Você não consegue compreender os ensinamentos",
            "exp": 20
          }
        ]
      }
    },
    "dialogue_options": [
      {
        "text": "Pedir para aprender técnicas de combate",
        "attribute_bonus": "power_stat",
        "bonus_value": 2,
        "success_text": "O mestre fica impressionado com sua aptidão para o combate!",
        "failure_text": "O mestre nota que você precisa de mais treinamento básico."
      },
      {
        "text": "Pedir para aprender conhecimentos arcanos",
        "attribute_bonus": "intellect",
        "bonus_value": 2,
        "success_text": "Sua mente absorve rapidamente os conhecimentos arcanos!",
        "failure_text": "Os conceitos são muito complexos para seu nível atual."
      }
    ],
    "category": "training",
    "rarity": "rare"
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

## Ferramentas de Desenvolvimento

Para facilitar o desenvolvimento e manutenção do modo história, foram criadas ferramentas especializadas:

### Ferramentas JSON

O módulo `utils/json_tools.py` fornece classes e funções para trabalhar com dados JSON:

- **JSONValidator**: Valida arquivos JSON contra esquemas definidos
  ```python
  from utils.json_tools import JSONValidator

  validator = JSONValidator("data/schemas")
  validator.validate_file("data/story_mode/chapters/chapter_1.json", "chapter")
  ```

- **JSONGenerator**: Gera arquivos JSON a partir de templates
  ```python
  from utils.json_tools import JSONGenerator

  generator = JSONGenerator("data/templates")
  new_content = generator.generate_from_template("event_template", {"name": "Meu Evento"})
  ```

- **Funções Utilitárias**: Para converter constantes, carregar configurações e mesclar arquivos
  ```python
  from utils.json_tools import convert_constants_to_json
  import utils.game_mechanics.constants as constants

  convert_constants_to_json(constants, "data/config")
  ```

### Sistema de Gerenciamento de Conteúdo

O módulo `utils/content_manager.py` fornece uma interface de linha de comando para gerenciar conteúdo do jogo:

```bash
# Listar conteúdo disponível
python -m utils.content_manager list --type chapters

# Criar novo conteúdo
python -m utils.content_manager create chapters 1_5 --template chapter_template --data '{"title": "Novo Capítulo"}'

# Editar conteúdo existente
python -m utils.content_manager edit chapters 1_5 --data '{"title": "Capítulo Atualizado"}'

# Validar conteúdo
python -m utils.content_manager validate chapters --id 1_5

# Criar esquema a partir de exemplo
python -m utils.content_manager schema chapters

# Criar template
python -m utils.content_manager template chapter_template --data '{"title": "", "description": ""}'
```

## Próximos Passos

Para o desenvolvimento futuro do modo história, apresentamos um plano abrangente dividido em categorias estratégicas:

### Expansão Narrativa

1. **Completar os capítulos do Ano 2**
   - Finalizar todos os caminhos ramificados e desfechos
   - Desenvolver a conclusão do arco das anomalias dimensionais
   - Criar um evento climático de fim de ano que reflita as escolhas acumuladas do jogador

2. **Introduzir o Ano 3 - "O Legado"**
   - Desenvolver uma estrutura narrativa onde o jogador começa a criar seu próprio legado na academia
   - Implementar um sistema de "Mentoria Avançada" onde as decisões do jogador moldam o desenvolvimento de NPCs juniores
   - Criar desafios que testam não apenas o poder do jogador, mas sua influência e reputação

3. **Desenvolver Arcos Narrativos para Clubes**
   - Criar histórias específicas para cada clube que aprofundam sua filosofia e segredos
   - Implementar "Missões de Clube" que oferecem recompensas exclusivas e desenvolvimento de personagem
   - Adicionar rivalidades inter-clubes com competições e alianças estratégicas

4. **Expandir o Universo Além da Academia**
   - Introduzir locais externos como a "Cidade Proibida" e o "Vale dos Ancestrais"
   - Criar capítulos de "Expedição" onde os jogadores exploram o mundo além da academia
   - Desenvolver uma mitologia mais profunda sobre a origem dos poderes e sua conexão com dimensões alternativas

### Aprimoramentos de Gameplay

1. **Implementar Sistema de Consequências Dinâmicas**
   - Desenvolver um algoritmo que rastreia padrões nas escolhas do jogador e adapta futuros eventos
   - Criar "Momentos de Definição" onde escolhas passadas convergem em consequências significativas
   - Implementar um sistema de "Reputação Faccionária" que afeta como diferentes grupos respondem ao jogador

2. **Criar Sistema de Evolução de Poderes**
   - Desenvolver uma árvore de habilidades para cada tipo de poder
   - Implementar "Rituais de Despertar" que permitem desbloquear habilidades avançadas
   - Criar desafios específicos para cada tipo de poder que testam a maestria do jogador

3. **Adicionar Eventos Sazonais Narrativos**
   - Desenvolver eventos especiais para cada estação que se integram à história principal
   - Criar "Festivais da Academia" com mini-jogos e desafios exclusivos
   - Implementar eventos climáticos sazonais que afetam a jogabilidade e desbloqueiam conteúdo exclusivo

4. **Expandir Sistema de Companheiros**
   - Adicionar mais companheiros com histórias e habilidades únicas
   - Desenvolver missões especiais que requerem companheiros específicos
   - Criar eventos de grupo que envolvem múltiplos companheiros

### Aprimoramentos Técnicos

1. **Expandir as ferramentas de desenvolvimento**
   - Criar mais templates e assistentes de geração para facilitar a criação de novos capítulos
   - Desenvolver validadores avançados que verificam consistência narrativa
   - Implementar ferramentas de visualização para testar fluxos narrativos

2. **Implementar análise de dados e métricas**
   - Desenvolver um sistema que rastreia as escolhas mais populares dos jogadores
   - Criar dashboards para visualizar o progresso dos jogadores na história
   - Implementar ferramentas para identificar pontos de abandono na narrativa

3. **Melhorar a integração com outros sistemas**
   - Aprimorar a conexão entre o modo história e o sistema de duelos
   - Integrar melhor com o sistema de clubes e hierarquia
   - Desenvolver APIs para permitir extensões por outros desenvolvedores

### Engajamento da Comunidade

1. **Criar Sistema de Histórias da Comunidade**
   - Desenvolver ferramentas para que jogadores avançados criem conteúdo narrativo
   - Implementar um sistema de votação para histórias criadas pela comunidade
   - Criar eventos especiais baseados nas melhores histórias da comunidade

2. **Implementar Eventos Narrativos Colaborativos**
   - Desenvolver capítulos especiais onde as escolhas coletivas da comunidade afetam o resultado
   - Criar "Crises Dimensionais" onde jogadores colaboram para resolver ameaças à academia
   - Implementar um sistema de "Legado Compartilhado" onde as ações de todos os jogadores moldam o mundo do jogo

## Conclusão

A nova arquitetura do modo história proporciona uma base sólida para expansão futura, permitindo adicionar novos capítulos, eventos e NPCs de forma modular e sem afetar o código existente. Os princípios SOLID garantem que o sistema seja flexível, extensível e de fácil manutenção.
