# Sistema de Logs Narrativos e Validação

Este documento descreve o sistema de logs narrativos e validação implementado para o jogo Tokugawa Discord.

## Visão Geral

O sistema de logs narrativos foi projetado para rastrear e analisar os fluxos narrativos no modo história do jogo. Ele permite:

1. Rastrear escolhas dos jogadores
2. Rastrear caminhos narrativos
3. Rastrear erros e problemas
4. Analisar os dados para identificar padrões e tendências

Além disso, um sistema de validação foi implementado para garantir a integridade dos dados e prevenir erros comuns.

## Componentes

### NarrativeLogger

A classe `NarrativeLogger` é responsável por registrar eventos narrativos e fornecer métodos para análise dos dados. Ela é implementada como um singleton para garantir que haja apenas uma instância em todo o sistema.

Principais métodos:

- `log_choice`: Registra uma escolha feita por um jogador
- `log_path`: Registra um caminho narrativo seguido por um jogador
- `log_error`: Registra um erro ocorrido durante a progressão da história
- `log_validation_error`: Registra um erro de validação
- `log_chapter_transition`: Registra uma transição entre capítulos

Métodos de análise:

- `get_most_common_choices`: Retorna as escolhas mais comuns
- `get_most_common_paths`: Retorna os caminhos mais comuns
- `get_most_common_errors`: Retorna os erros mais comuns
- `get_chapter_analytics`: Retorna análises detalhadas para um capítulo específico
- `export_analytics_for_dashboard`: Exporta dados de análise para o dashboard

### StoryValidator

A classe `StoryValidator` é responsável por validar elementos da história, como IDs de capítulos, escolhas, mudanças de afinidade e condicionais. Ela também é implementada como um singleton.

Principais métodos:

- `validate_chapter_id`: Valida um ID de capítulo
- `validate_choice`: Valida uma escolha de jogador
- `validate_affinity_change`: Valida uma mudança de afinidade
- `validate_conditional`: Valida uma declaração condicional
- `validate_chapter_data`: Valida dados de um capítulo

## Integração com o Sistema Existente

### StoryMode

A classe `StoryMode` foi modificada para usar o logger narrativo e o validador. As principais modificações incluem:

1. Inicialização do logger narrativo e do validador no construtor
2. Adição de chamadas de log em pontos-chave:
   - Ao iniciar a história
   - Ao processar escolhas
   - Ao transitar entre capítulos
   - Ao disparar eventos
3. Adição de validações em pontos-chave:
   - Validação de IDs de capítulos
   - Validação de escolhas
   - Validação de mudanças de afinidade
   - Validação de condicionais

### DecisionDashboard

A classe `DecisionDashboard` foi modificada para usar o logger narrativo para análise de dados. As principais modificações incluem:

1. Inicialização do logger narrativo no construtor
2. Adição de um novo comando `analytics` para exibir análises do logger narrativo

## Estrutura de Arquivos

- `story_mode/narrative_logger.py`: Implementação do logger narrativo
- `story_mode/validation.py`: Implementação do validador
- `tests/story_mode/test_narrative_logger.py`: Testes para o logger narrativo e o validador

## Formato dos Logs

Os logs são armazenados em arquivos JSON e JSONL no diretório `data/logs/narrative`:

- `choice_logs.json`: Registros agregados de escolhas
- `path_logs.json`: Registros agregados de caminhos
- `error_logs.json`: Registros agregados de erros
- `detailed_choice_logs.jsonl`: Registros detalhados de escolhas
- `detailed_path_logs.jsonl`: Registros detalhados de caminhos
- `detailed_error_logs.jsonl`: Registros detalhados de erros
- `detailed_validation_logs.jsonl`: Registros detalhados de erros de validação
- `detailed_transition_logs.jsonl`: Registros detalhados de transições entre capítulos

## Uso

### Registrando Eventos

```python
from story_mode.narrative_logger import get_narrative_logger

logger = get_narrative_logger()

# Registrar uma escolha
logger.log_choice(player_id, chapter_id, choice_key, choice_value)

# Registrar um caminho
logger.log_path(player_id, [chapter_id1, chapter_id2, chapter_id3])

# Registrar um erro
logger.log_error(player_id, chapter_id, error_type, error_message)

# Registrar uma transição entre capítulos
logger.log_chapter_transition(player_id, from_chapter_id, to_chapter_id, transition_type)
```

### Validando Elementos

```python
from story_mode.validation import get_story_validator

validator = get_story_validator()

# Validar um ID de capítulo
is_valid = validator.validate_chapter_id(chapter_id)

# Validar uma escolha
result = validator.validate_choice(player_data, chapter_id, choice_index, available_choices)

# Validar uma mudança de afinidade
result = validator.validate_affinity_change(player_data, npc_name, change)

# Validar uma declaração condicional
result = validator.validate_conditional(player_data, condition)
```

### Analisando Dados

```python
from story_mode.narrative_logger import get_narrative_logger

logger = get_narrative_logger()

# Obter as escolhas mais comuns
most_common_choices = logger.get_most_common_choices()

# Obter os caminhos mais comuns
most_common_paths = logger.get_most_common_paths()

# Obter os erros mais comuns
most_common_errors = logger.get_most_common_errors()

# Obter análises para um capítulo específico
chapter_analytics = logger.get_chapter_analytics(chapter_id)

# Exportar dados para o dashboard
dashboard_data = logger.export_analytics_for_dashboard()
```

## Benefícios

1. **Rastreamento de Erros**: O sistema permite rastrear erros e problemas na progressão da história, facilitando a identificação e correção de bugs.

2. **Análise de Caminhos**: O sistema permite analisar os caminhos mais populares entre os jogadores, ajudando a identificar padrões e tendências.

3. **Validação de Dados**: O sistema valida elementos da história, prevenindo erros comuns e garantindo a integridade dos dados.

4. **Compatibilidade com o Dashboard**: O sistema é compatível com o dashboard de decisões, permitindo visualizar e analisar os dados coletados.

## Considerações Futuras

1. **Armazenamento em Banco de Dados**: Atualmente, os logs são armazenados em arquivos JSON e JSONL. No futuro, pode ser interessante migrar para um banco de dados para melhor desempenho e escalabilidade.

2. **Análises Mais Avançadas**: Implementar análises mais avançadas, como análise de sentimento, clustering de jogadores com base em escolhas similares, etc.

3. **Integração com Telemetria**: Integrar o sistema de logs narrativos com um sistema de telemetria mais amplo para análise de métricas de jogo.

4. **Interface de Usuário para Análise**: Desenvolver uma interface de usuário dedicada para análise dos dados coletados, além do dashboard de decisões.