# Documentação dos Novos Sistemas

Este documento descreve os novos sistemas implementados no jogo: o Sistema de Eventos Sazonais e o Sistema de Companheiros.

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

## Conclusão

Estes novos sistemas enriquecem significativamente a experiência narrativa do jogo, oferecendo conteúdo dinâmico baseado nas estações e companheiros com histórias próprias. A integração com o modo história existente garante uma experiência coesa e imersiva para os jogadores.