# Sistema de Romance

## Visão Geral

O sistema de romance da Academia Tokugawa oferece 7 rotas românticas distintas, cada uma com sua própria história, personagens e desenvolvimento. O sistema é integrado com outros aspectos do jogo, como clubes e eventos especiais.

## Estrutura de Arquivos

```
data/story_mode/
├── npcs/
│   ├── npc_1.json
│   ├── npc_2.json
│   └── ...
├── romance/
│   ├── routes/
│   │   ├── route_1.json
│   │   ├── route_2.json
│   │   └── ...
│   └── events/
│       ├── event_1.json
│       ├── event_2.json
│       └── ...
└── assets/
    └── images/
        └── characters/
            ├── npc_1/
            │   ├── normal.jpg
            │   ├── happy.jpg
            │   └── ...
            └── ...
```

## Estrutura de Dados

### npc_X.json

```json
{
  "id": "npc_1",
  "name": "Nome do Personagem",
  "description": "Descrição do personagem...",
  "personality": ["trait_1", "trait_2"],
  "romance_route": {
    "id": "route_1",
    "requirements": {
      "min_stats": {
        "charisma": 5
      }
    },
    "events": [
      {
        "id": "event_1",
        "requirements": {
          "relationship_level": 2
        }
      }
    ]
  }
}
```

### route_X.json

```json
{
  "id": "route_1",
  "character": "npc_1",
  "name": "Nome da Rota",
  "description": "Descrição da rota...",
  "levels": {
    "1": {
      "name": "Conhecidos",
      "points_required": 0,
      "events": ["event_1", "event_2"]
    },
    "2": {
      "name": "Amigos",
      "points_required": 20,
      "events": ["event_3", "event_4"]
    },
    "3": {
      "name": "Próximos",
      "points_required": 40,
      "events": ["event_5", "event_6"]
    },
    "4": {
      "name": "Românticos",
      "points_required": 60,
      "events": ["event_7", "event_8"]
    },
    "5": {
      "name": "Comprometidos",
      "points_required": 80,
      "events": ["event_9", "event_10"]
    }
  },
  "special_events": [
    {
      "id": "special_1",
      "name": "Evento Especial",
      "requirements": {
        "relationship_level": 4,
        "club_membership": "clube_das_chamas"
      }
    }
  ]
}
```

## Níveis de Relacionamento

### 1. Conhecidos (0-19 pontos)
- Interações básicas
- Diálogos iniciais
- Eventos de introdução

### 2. Amigos (20-39 pontos)
- Mais interações disponíveis
- Eventos de amizade
- Descontos em lojas

### 3. Próximos (40-59 pontos)
- Eventos especiais
- Cenas românticas iniciais
- Benefícios exclusivos

### 4. Românticos (60-79 pontos)
- Eventos românticos
- Cenas especiais
- Recompensas únicas

### 5. Comprometidos (80-100 pontos)
- Eventos finais
- Múltiplos finais
- Recompensas máximas

## Eventos de Romance

### Tipos de Eventos

1. **Eventos Diários**
   - Interações casuais
   - Pequenos presentes
   - Conversas informais

2. **Eventos Especiais**
   - Datas
   - Festivais
   - Momentos únicos

3. **Eventos de Clube**
   - Atividades conjuntas
   - Treinamentos
   - Competições

4. **Eventos de História**
   - Momentos narrativos
   - Escolhas significativas
   - Impacto na trama

## Sistema de Pontos

### Ganhando Pontos

1. **Interações Positivas**
   - Escolhas corretas
   - Presentes adequados
   - Ações consideradas

2. **Eventos Especiais**
   - Datas bem-sucedidas
   - Festivais
   - Momentos únicos

3. **Ações de Clube**
   - Trabalho em equipe
   - Competições
   - Treinamentos

### Perdendo Pontos

1. **Interações Negativas**
   - Escolhas ruins
   - Ações desconsideradas
   - Conflitos

2. **Eventos Falhos**
   - Datas mal-sucedidas
   - Erros em eventos
   - Desentendimentos

## Integração com Outros Sistemas

### Clubes

- Eventos especiais para casais
- Benefícios exclusivos
- Interações únicas

### História Principal

- Capítulos especiais
- Escolhas significativas
- Impacto na narrativa

### Sistema de Imagens

- CGs especiais
- Variações de expressão
- Cenas únicas

## Exemplos de Uso

### Criando uma Nova Rota

1. Crie um novo arquivo `route_X.json`
2. Defina a estrutura básica
3. Configure os níveis e eventos
4. Adicione eventos especiais
5. Integre com outros sistemas

### Adicionando um Evento

1. Crie um novo arquivo de evento
2. Defina requisitos e recompensas
3. Configure as escolhas
4. Adicione imagens especiais

## Boas Práticas

1. **Variedade**: Ofereça diferentes tipos de interações
2. **Progressão**: Crie uma curva de progressão natural
3. **Consequências**: Faça as escolhas importarem
4. **Integração**: Mantenha conexões com outros sistemas
5. **Feedback**: Forneça feedback claro sobre o progresso 