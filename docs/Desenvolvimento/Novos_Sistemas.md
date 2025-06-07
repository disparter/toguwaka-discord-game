# Documentação dos Novos Sistemas

Este documento descreve os novos sistemas implementados no jogo: o Sistema de Eventos Sazonais, o Sistema de Companheiros e o Dashboard de Comparação de Decisões.

## Sistema de Eventos Sazonais

O Sistema de Eventos Sazonais adiciona eventos especiais que ocorrem durante estações específicas do ano, enriquecendo a experiência narrativa do jogo e oferecendo conteúdo exclusivo aos jogadores.

### Tipos de Eventos Sazonais

1. **Eventos Sazonais Regulares**
   - Eventos que ocorrem durante uma estação específica
   - Oferecem recompensas e atividades temáticas
   - Integram-se à história principal

2. **Festivais da Academia**
   - Eventos especiais com mini-jogos e desafios exclusivos
   - Ocorrem em datas específicas durante cada estação
   - Oferecem recompensas únicas e oportunidades de desenvolvimento de personagem

3. **Eventos Climáticos**
   - Alteram a jogabilidade com efeitos climáticos específicos
   - Desbloqueiam locais normalmente inacessíveis
   - Oferecem conteúdo exclusivo relacionado ao clima

### Como Funciona

O sistema detecta automaticamente a estação atual com base na data do sistema e disponibiliza eventos apropriados para os jogadores. Cada tipo de evento tem requisitos específicos (nível, capítulos completados, etc.) e oferece recompensas únicas.

#### Estações

- **Primavera (Março-Maio)**: Eventos focados em renovação e novos começos
- **Verão (Junho-Agosto)**: Eventos focados em poder e energia
- **Outono (Setembro-Novembro)**: Eventos focados em sabedoria e colheita
- **Inverno (Dezembro-Fevereiro)**: Eventos focados em introspecção e renovação

### Integração com o Modo História

Os eventos sazonais são verificados automaticamente durante o progresso do jogador no modo história:
- Ao iniciar ou continuar a história
- Após fazer escolhas
- Após participar de eventos

### Métodos Principais

```python
# Obter eventos disponíveis na estação atual
get_current_season_events(player_data)

# Participar de um evento sazonal
participate_in_seasonal_event(player_data, event_id)

# Participar de um mini-jogo em um festival
participate_in_mini_game(player_data, festival_id, mini_game_id)

# Tentar um desafio exclusivo em um festival
attempt_festival_challenge(player_data, festival_id, challenge_id)

# Obter status de participação em eventos sazonais
get_seasonal_event_status(player_data)
```

## Sistema de Companheiros

O Sistema de Companheiros permite que os jogadores recrutem NPCs que os acompanham em certos capítulos, oferecendo assistência, histórias exclusivas e habilidades especiais.

### Características dos Companheiros

1. **Arcos Narrativos Exclusivos**
   - Cada companheiro tem sua própria história
   - Missões exclusivas que desenvolvem o personagem
   - Marcos de progresso com recompensas

2. **Habilidades de Sincronização**
   - Combinação de poderes entre jogador e companheiro
   - Efeitos poderosos que auxiliam na jogabilidade
   - Níveis de sincronização que desbloqueiam habilidades mais fortes

3. **Especialização de Poderes**
   - Cada companheiro tem um tipo de poder e especialização
   - Complementa as habilidades do jogador
   - Oferece estratégias diferentes para diferentes situações

### Como Funciona

Os companheiros ficam disponíveis para recrutamento em capítulos específicos. Após o recrutamento, o jogador pode ativar um companheiro por vez para acompanhá-lo. O relacionamento com o companheiro evolui através de missões e avanços no arco narrativo.

### Progressão do Companheiro

1. **Recrutamento**: Encontre e recrute o companheiro em um capítulo específico
2. **Ativação**: Ative o companheiro para que ele o acompanhe
3. **Missões**: Complete missões exclusivas do companheiro
4. **Progresso do Arco**: Avance no arco narrativo do companheiro
5. **Sincronização**: Desbloqueie e use habilidades de sincronização

### Integração com o Modo História

Os companheiros disponíveis são verificados automaticamente durante o progresso do jogador no modo história:
- Ao iniciar ou continuar a história
- Após fazer escolhas
- Após participar de eventos

### Comandos Discord para Interação com Companheiros

Os jogadores podem interagir com o sistema de companheiros através dos seguintes comandos Discord:

1. **`/companheiros`**: Visualiza todos os companheiros disponíveis e recrutados
   - Mostra o companheiro ativo atual
   - Lista companheiros recrutados com seus níveis de sincronização e progresso
   - Exibe companheiros disponíveis para recrutamento no capítulo atual

2. **`/recrutar [nome]`**: Recruta um companheiro disponível
   - Verifica se o companheiro está disponível no capítulo atual
   - Adiciona o companheiro à lista de companheiros recrutados do jogador

3. **`/ativar_companheiro [nome]`**: Ativa um companheiro recrutado
   - Desativa qualquer companheiro atualmente ativo
   - Torna o companheiro especificado ativo
   - Exibe as habilidades de sincronização disponíveis

4. **`/desativar_companheiro`**: Desativa o companheiro atual
   - Remove o status ativo do companheiro atual

5. **`/status_companheiro [nome]`**: Exibe detalhes de um companheiro
   - Mostra informações básicas (tipo de poder, especialização, etc.)
   - Lista missões disponíveis e completadas
   - Exibe habilidades de sincronização disponíveis

6. **`/completar_missao [nome] [id_missao]`**: Completa uma missão de companheiro
   - Marca a missão como concluída
   - Concede recompensas (EXP, TUSD, itens especiais)
   - Avança o progresso do arco narrativo do companheiro

7. **`/sincronizar [id_habilidade]`**: Usa uma habilidade de sincronização
   - Verifica se o companheiro está ativo
   - Aplica os efeitos da habilidade (aumento de atributos, ações especiais)
   - Coloca a habilidade em cooldown

### Métodos Principais

```python
# Obter companheiros disponíveis no capítulo atual
get_available_companions(player_data, chapter_id)

# Obter companheiros recrutados
get_recruited_companions(player_data)

# Obter companheiro ativo
get_active_companion(player_data)

# Recrutar um companheiro
recruit_companion(player_data, companion_id)

# Ativar um companheiro
activate_companion(player_data, companion_id)

# Desativar um companheiro
deactivate_companion(player_data, companion_id)

# Avançar no arco narrativo de um companheiro
advance_companion_arc(player_data, companion_id, progress_amount)

# Completar uma missão de um companheiro
complete_companion_mission(player_data, companion_id, mission_id)

# Usar uma habilidade de sincronização
perform_sync_ability(player_data, companion_id, ability_id)

# Obter status detalhado de um companheiro
get_companion_status(player_data, companion_id)
```

## Exemplos de Uso

### Eventos Sazonais

```python
# Verificar eventos disponíveis na estação atual
events = story_mode.get_current_season_events(player_data)

# Participar de um evento sazonal
result = story_mode.participate_in_seasonal_event(player_data, "spring_awakening")
player_data = result["player_data"]  # Atualizar dados do jogador

# Participar de um mini-jogo em um festival
result = story_mode.participate_in_mini_game(player_data, "spring_festival", "spring_archery")
player_data = result["player_data"]  # Atualizar dados do jogador

# Verificar status de participação em eventos sazonais
status = story_mode.get_seasonal_event_status(player_data)
```

### Companheiros

```python
# Verificar companheiros disponíveis no capítulo atual
chapter_id = story_mode.progress_manager.get_current_chapter(player_data)
companions = story_mode.get_available_companions(player_data, chapter_id)

# Recrutar um companheiro
result = story_mode.recruit_companion(player_data, "akira_tanaka")
player_data = result["player_data"]  # Atualizar dados do jogador

# Ativar um companheiro
result = story_mode.activate_companion(player_data, "akira_tanaka")
player_data = result["player_data"]  # Atualizar dados do jogador

# Completar uma missão de um companheiro
result = story_mode.complete_companion_mission(player_data, "akira_tanaka", "akira_m1")
player_data = result["player_data"]  # Atualizar dados do jogador

# Usar uma habilidade de sincronização
result = story_mode.perform_sync_ability(player_data, "akira_tanaka", "akira_sync1")
player_data = result["player_data"]  # Atualizar dados do jogador
```

## Estrutura de Dados

### Eventos Sazonais

Os eventos sazonais são armazenados na estrutura `story_progress` do jogador:

```json
"story_progress": {
  "seasonal_events": {
    "participated_events": ["spring_awakening", "summer_solstice"],
    "mini_games": {
      "spring_archery": {
        "participated": true,
        "won": true,
        "timestamp": "2023-05-01T14:30:00"
      }
    },
    "challenges": {
      "spring_duel": {
        "attempted": true,
        "completed": false,
        "timestamp": "2023-05-02T16:45:00"
      }
    },
    "weather_events": {
      "spring_rain": {
        "experienced": true,
        "timestamp": "2023-05-03T10:15:00"
      }
    }
  }
}
```

### Companheiros

Os companheiros são armazenados na estrutura `story_progress` do jogador:

```json
"story_progress": {
  "companions": {
    "akira_tanaka": {
      "recruited": true,
      "active": true,
      "arc_progress": 25,
      "completed_missions": ["akira_m1"],
      "sync_level": 2,
      "recruited_date": "2023-05-01T14:30:00",
      "sync_cooldowns": {
        "akira_sync1": "2023-05-03T10:15:00"
      }
    }
  }
}
```

## Sistema de Eventos Aleatórios Aprimorado

O Sistema de Eventos Aleatórios foi aprimorado para oferecer experiências mais envolventes e variadas aos jogadores, com opções de diálogo, verificações de atributos e recompensas/penalidades diversificadas.

### Características do Sistema Aprimorado

1. **Títulos Significativos**
   - Todos os eventos agora possuem títulos descritivos e significativos
   - Eliminação do problema "Untitled Event" que ocorria anteriormente
   - Melhor contextualização para os jogadores

2. **Opções de Diálogo**
   - Os jogadores podem escolher entre diferentes opções de diálogo
   - Cada opção pode conceder bônus em verificações de atributos específicos
   - Respostas personalizadas baseadas no sucesso ou fracasso

3. **Verificações de Atributos**
   - Eventos podem exigir verificações de atributos (Intelecto, Poder, etc.)
   - Dificuldade variável baseada no contexto do evento
   - Resultados diferentes baseados no sucesso ou fracasso

4. **Recompensas e Penalidades Variadas**
   - Múltiplas possibilidades de recompensas para eventos bem-sucedidos
   - Diferentes penalidades para falhas
   - Descrições detalhadas dos resultados

5. **Categorização e Raridade**
   - Eventos organizados por categorias (social, combate, acadêmico, etc.)
   - Sistema de raridade que determina a frequência de ocorrência
   - Eventos lendários com recompensas excepcionais

### Estrutura de um Evento Aleatório Aprimorado

```json
{
  "title": "Título do Evento",
  "description": "Descrição do evento",
  "type": "positive/negative/neutral",
  "effect": {
    "attribute_check": "nome_do_atributo",
    "difficulty": 7,
    "rewards": {
      "success": [
        {
          "description": "Descrição do sucesso",
          "exp": 100,
          "tusd": 50,
          "atributo": 1
        }
      ],
      "failure": [
        {
          "description": "Descrição da falha",
          "exp": 20,
          "tusd": -10
        }
      ]
    }
  },
  "dialogue_options": [
    {
      "text": "Texto da opção de diálogo",
      "attribute_bonus": "atributo",
      "bonus_value": 2,
      "success_text": "Texto exibido em caso de sucesso",
      "failure_text": "Texto exibido em caso de falha"
    }
  ],
  "category": "categoria",
  "rarity": "raridade"
}
```

### Integração com o Sistema de Jogo

O sistema aprimorado de eventos aleatórios se integra com outros sistemas do jogo:

- **Modo História**: Eventos aleatórios podem ocorrer durante a progressão da história
- **Sistema de Clubes**: Eventos específicos para membros de determinados clubes
- **Sistema de Atributos**: Verificações de atributos e bônus baseados nas estatísticas do jogador
- **Sistema de Economia**: Recompensas e penalidades econômicas variadas

### Métodos Principais

```python
# Obter um evento aleatório
event = RandomEvent.create_random_event()

# Disparar um evento para um jogador
result = event.trigger(player_data)

# Disparar um evento com escolha de diálogo
result = event.trigger(player_data, dialogue_choice=1)

# Verificar o resultado do evento
if "attribute_check" in result:
    success = result["attribute_check"]["success"]
    # Processar resultado baseado no sucesso ou falha
```

## Dashboard de Comparação de Decisões

O Dashboard de Comparação de Decisões é uma ferramenta interativa que permite aos jogadores visualizar como suas escolhas narrativas se comparam às da comunidade geral, mantendo o anonimato dos dados.

### Funcionalidades Principais

1. **Comparação de Escolhas Narrativas**
   - Exibição de estatísticas sobre as escolhas feitas em pontos-chave da história
   - Gráficos visuais mostrando a distribuição de escolhas entre todos os jogadores
   - Comparação das escolhas do jogador com as tendências gerais

2. **Análise de Caminhos Narrativos**
   - Visualização dos caminhos narrativos mais populares através da história
   - Identificação de caminhos raros ou pouco explorados
   - Mapa de calor mostrando pontos de decisão com maior divergência entre jogadores

3. **Estatísticas de Facções e Alianças**
   - Distribuição de jogadores entre as diferentes facções (Elite vs. Igualitários)
   - Tendências de alianças com NPCs específicos
   - Comparação das escolhas de facção com base no clube escolhido

4. **Métricas de Estilo de Jogo**
   - Análise do estilo de jogo baseado em padrões de escolha (diplomático, agressivo, estratégico, etc.)
   - Comparação do estilo de jogo do jogador com a comunidade
   - Sugestões de conteúdo baseadas no estilo de jogo identificado

### Como Funciona

O dashboard coleta anonimamente as escolhas feitas por todos os jogadores durante o modo história e as agrega para criar visualizações estatísticas. Quando um jogador acessa o dashboard, suas próprias escolhas são comparadas com as estatísticas agregadas da comunidade.

### Comandos Discord

Os jogadores podem acessar o dashboard através dos seguintes comandos Discord:

1. **`/dashboard escolhas [capítulo]`**: Mostra uma comparação das escolhas do jogador com a comunidade
   - Exibe gráficos de barras comparando as escolhas do jogador com as tendências gerais
   - Opcionalmente filtra por capítulo específico
   - Fornece estatísticas sobre quantos jogadores fizeram as mesmas escolhas

2. **`/dashboard caminhos`**: Analisa os caminhos narrativos através da história
   - Mostra os caminhos mais populares e como o caminho do jogador se compara
   - Identifica se o caminho do jogador é comum ou raro
   - Fornece estatísticas sobre a popularidade de diferentes sequências de capítulos

3. **`/dashboard faccoes`**: Exibe estatísticas sobre facções e alianças
   - Mostra a distribuição de jogadores entre diferentes clubes
   - Compara as reputações de facção do jogador com as médias da comunidade
   - Identifica tendências de alianças com NPCs específicos

4. **`/dashboard estilo`**: Analisa o estilo de jogo do jogador
   - Identifica o estilo dominante do jogador (diplomático, agressivo, estratégico, etc.)
   - Compara o estilo do jogador com as tendências da comunidade
   - Oferece sugestões de conteúdo baseadas no estilo identificado

### Métodos Principais

```python
# Obter as escolhas de um jogador
_get_player_choices(player, chapter_id=None)

# Obter escolhas agregadas da comunidade
_get_community_choices(chapter_id=None)

# Obter o caminho narrativo de um jogador
_get_player_path(player)

# Obter caminhos narrativos agregados da comunidade
_get_community_paths()

# Obter dados de facção de um jogador
_get_player_faction_data(player)

# Obter dados de facção agregados da comunidade
_get_community_faction_data()

# Analisar o estilo de jogo de um jogador
_analyze_gameplay_style(player, player_choices)

# Obter dados de estilo de jogo agregados da comunidade
_get_community_style_data()

# Criar visualização de comparação de escolhas
_create_choice_comparison(player, player_choices, community_choices, chapter_id)

# Criar visualização de análise de caminhos
_create_path_analysis(player, player_path, community_paths)

# Criar visualização de estatísticas de facção
_create_faction_stats(player, player_faction, community_factions)

# Criar visualização de análise de estilo de jogo
_create_style_analysis(player, player_style, community_styles)
```

### Estrutura de Dados

O dashboard utiliza os dados de escolhas já armazenados na estrutura `story_progress` do jogador:

```json
"story_progress": {
  "story_choices": {
    "1_1": {
      "choice_0": 1,
      "choice_1": 0
    },
    "1_2": {
      "choice_0": 2
    }
  },
  "completed_chapters": ["1_1", "1_2", "1_3"],
  "faction_reputations": {
    "elite": 25,
    "igualitarios": -10
  }
}
```

### Integração com o Modo História

O dashboard se integra com o modo história existente:
- Utiliza as escolhas já registradas pelo sistema de história
- Não requer alterações no fluxo de jogo existente
- Fornece insights adicionais sobre a experiência narrativa

### Requisitos Técnicos

O dashboard utiliza as seguintes bibliotecas para criar visualizações:
- matplotlib: Para geração de gráficos
- numpy: Para processamento de dados estatísticos

Estas dependências foram adicionadas ao arquivo requirements.txt do projeto.

## Conclusão

Estes novos sistemas enriquecem significativamente a experiência narrativa do jogo, oferecendo conteúdo dinâmico baseado nas estações, companheiros com histórias próprias, eventos aleatórios mais envolventes com opções de diálogo e resultados variados, e um dashboard interativo para comparação de decisões. A integração com o modo história existente garante uma experiência coesa e imersiva para os jogadores.
