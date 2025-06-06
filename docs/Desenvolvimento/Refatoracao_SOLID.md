# Refatoração SOLID do Projeto Academia Tokugawa

Este documento descreve a refatoração do projeto Academia Tokugawa para aderir aos princípios SOLID, garantindo modularidade, reutilização de código e expansibilidade.

## Princípios SOLID Implementados

### 1. Princípio da Responsabilidade Única (SRP)

Cada classe e função agora tem uma única responsabilidade bem definida. Separamos funcionalidades relacionadas ao cálculo, eventos, narrativa e economia em componentes dedicados.

**Implementações:**
- Criamos classes específicas para cálculos:
  - `ExperienceCalculator` para lidar com cálculos de experiência
  - `HPFactorCalculator` para manipular o fator de HP

- Reorganizamos eventos como entidades isoladas:
  - `TrainingEvent` para eventos de treinamento
  - `RandomEvent` para eventos aleatórios

### 2. Princípio Aberto/Fechado (OCP)

O sistema agora está aberto para extensão, mas fechado para modificações. Novos recursos podem ser implementados sem alterar as bases do sistema.

**Implementações:**
- Criamos interfaces e classes abstratas para gerenciar cálculos, eventos e interações:
  - `ICalculator`, `IExperienceCalculator`, `IHPFactorCalculator`
  - `IEvent`, `EventBase`
  - `IDuelCalculator`, `IDuelNarrator`

- Usamos herança e composição para permitir a adição de novos tipos de eventos, cálculos e interações sem modificar o código existente.

### 3. Princípio da Substituição de Liskov (LSP)

Os módulos derivados agora podem substituir seus módulos base sem efeitos colaterais.

**Implementações:**
- Garantimos que todas as classes que implementam interfaces seguem seus contratos
- Implementamos hierarquias de classes bem definidas, como:
  - `EventBase` → `TrainingEvent`, `RandomEvent`

### 4. Princípio da Segregação de Interfaces (ISP)

As interfaces são específicas aos clientes que as utilizam, evitando métodos não utilizados.

**Implementações:**
- Dividimos interfaces complexas em interfaces menores e mais específicas:
  - `ICalculator` como interface base para calculadoras
  - `IExperienceCalculator` para cálculos de experiência
  - `IHPFactorCalculator` para cálculos de fator de HP
  - `IDuelCalculator` para cálculos de duelos
  - `IDuelNarrator` para narração de duelos

### 5. Princípio da Inversão de Dependência (DIP)

Componentes de alto nível não dependem de componentes de baixo nível; ambos dependem de abstrações.

**Implementações:**
- Usamos interfaces e classes abstratas para desacoplar dependências
- Implementamos injeção de dependência onde apropriado
- Criamos uma estrutura onde os componentes dependem de abstrações, não de implementações concretas

## Nova Estrutura de Diretórios

```
utils/
└── game_mechanics/
    ├── __init__.py                      # Re-exporta classes e funções para compatibilidade
    ├── constants.py                     # Constantes do jogo
    ├── calculators/
    │   ├── __init__.py
    │   ├── calculator_interface.py      # Interface base para calculadoras
    │   ├── experience_calculator_interface.py
    │   ├── experience_calculator.py
    │   ├── hp_factor_calculator_interface.py
    │   └── hp_factor_calculator.py
    ├── events/
    │   ├── __init__.py
    │   ├── event_interface.py           # Interface para eventos
    │   ├── event_base.py                # Classe base abstrata para eventos
    │   ├── training_event.py
    │   └── random_event.py
    └── duel/
        ├── __init__.py
        ├── duel_calculator_interface.py
        ├── duel_calculator.py
        ├── duel_narrator_interface.py
        └── duel_narrator.py
```

## Benefícios da Refatoração

1. **Modularidade**: Cada componente tem uma responsabilidade clara e bem definida
2. **Extensibilidade**: Novos tipos de eventos, cálculos e interações podem ser adicionados facilmente
3. **Testabilidade**: Componentes isolados são mais fáceis de testar
4. **Manutenibilidade**: Código mais organizado e com menos acoplamento
5. **Reutilização**: Componentes podem ser reutilizados em diferentes partes do sistema

## Compatibilidade com Código Existente

Para garantir compatibilidade com o código existente, mantivemos as funções originais no módulo `utils/game_mechanics/__init__.py`, que agora delegam para as novas implementações. Isso permite uma migração gradual para a nova arquitetura sem quebrar o código existente.

## Próximos Passos

1. ✅ Migrar gradualmente o código existente para usar as novas classes e interfaces
2. ✅ Adicionar testes unitários para os novos componentes
3. ✅ Expandir o sistema com novos tipos de eventos, cálculos e interações
4. ✅ Documentar as novas classes e interfaces para facilitar o uso por outros desenvolvedores
5. Garantir que todos os comandos estão sincronizados corretamente
6. Continuar usando os JSONs para facilitar expansão de diálogos e eventos

## Migração Realizada

O código foi migrado gradualmente para usar as novas classes e interfaces:

1. **Atividades**: O módulo `cogs/activities.py` foi atualizado para usar:
   - `TrainingEvent` para eventos de treinamento
   - `RandomEvent` para eventos aleatórios
   - `ExperienceCalculator` para cálculos de experiência
   - `DuelCalculator` para cálculos de duelos
   - `DuelNarrator` para narração de duelos

2. **Modo História**: O módulo `story_mode/story_mode.py` foi atualizado para integrar com o novo sistema de eventos.

## Testes Unitários

Foram adicionados testes unitários para os novos componentes:

1. **Calculadoras**:
   - `TestExperienceCalculator`: Testa cálculos de experiência
   - `TestHPFactorCalculator`: Testa cálculos de fator de HP

2. **Eventos**:
   - `TestTrainingEvent`: Testa eventos de treinamento
   - `TestRandomEvent`: Testa eventos aleatórios

3. **Duelos**:
   - `TestDuelCalculator`: Testa cálculos de duelos
   - `TestDuelNarrator`: Testa narração de duelos

## Novos Tipos de Eventos

O sistema foi expandido com novos tipos de eventos:

1. **FestivalEvent**: Eventos especiais que ocorrem durante festivais
   - Fornecem bônus de experiência e TUSD
   - Aplicam bônus baseado no carisma do jogador
   - Têm duração em dias

2. **StoryEvent**: Eventos que ocorrem durante o modo história
   - Podem ter escolhas que levam a diferentes resultados
   - Fornecem recompensas variadas (exp, TUSD, atributos, itens)
   - Podem atualizar o progresso da história

## Exemplos de Uso

### Exemplo 1: Criando e Disparando um Evento de Treinamento

```python
from utils.game_mechanics.events.training_event import TrainingEvent

# Criar um evento de treinamento personalizado
event = TrainingEvent(
    "Treinamento Intensivo",
    "Você treinou intensamente e sentiu seu poder crescer!",
    exp_gain=25,
    attribute_gain="dexterity"
)

# Ou criar um evento aleatório
event = TrainingEvent.create_random_training_event()

# Disparar o evento para um jogador
player_data = get_player(user_id)
result = event.trigger(player_data)

# Processar o resultado
exp_gain = result["exp_gain"]
attribute = result.get("attribute_gain")
```

### Exemplo 2: Calculando Nível e Progresso

```python
from utils.game_mechanics.calculators.experience_calculator import ExperienceCalculator

# Calcular nível a partir da experiência
exp = 1500
level = ExperienceCalculator.calculate_level(exp)

# Calcular progresso para o próximo nível
progress = ExperienceCalculator.calculate_progress(exp, level)
```

### Exemplo 3: Calculando Resultado de Duelo

```python
from utils.game_mechanics.duel.duel_calculator import DuelCalculator
from utils.game_mechanics.duel.duel_narrator import DuelNarrator

# Calcular resultado do duelo
duel_result = DuelCalculator.calculate_outcome(challenger, opponent, "physical")

# Gerar narração do duelo
narration = DuelNarrator.generate_narration(duel_result)
```

### Exemplo 4: Criando e Disparando um Evento de Festival

```python
from utils.game_mechanics.events.festival_event import FestivalEvent

# Criar um evento de festival
event = FestivalEvent(
    "Festival dos Poderes",
    "Um grande festival está acontecendo na Academia Tokugawa!",
    exp_gain=100,
    tusd_gain=50,
    duration=3
)

# Disparar o evento para um jogador
player_data = get_player(user_id)
result = event.trigger(player_data)

# Processar o resultado
exp_change = result["exp_change"]
tusd_change = result["tusd_change"]
duration = result["duration"]
```

### Exemplo 5: Criando e Processando um Evento de História

```python
from utils.game_mechanics.events.story_event import StoryEvent

# Criar um evento de história com escolhas
event = StoryEvent(
    "Encontro Misterioso",
    "Você encontra uma figura misteriosa no campus...",
    chapter_id="1_2",
    event_type="story",
    rewards={"exp": 50},
    choices=[
        {
            "text": "Aproximar-se e conversar",
            "description": "Você se aproxima e inicia uma conversa...",
            "rewards": {"exp": 30, "attribute": "charisma"}
        },
        {
            "text": "Observar à distância",
            "description": "Você decide observar de longe...",
            "rewards": {"exp": 20, "attribute": "intellect"}
        }
    ]
)

# Disparar o evento para um jogador
player_data = get_player(user_id)
result = event.trigger(player_data)

# Processar uma escolha
choice_result = event.process_choice(player_data, 0)  # Escolha 0: Aproximar-se
```