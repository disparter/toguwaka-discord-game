# Sistema de Clubes

## Visão Geral

O sistema de clubes da Academia Tokugawa permite que os jogadores participem de diferentes clubes, cada um com sua própria história, mecânicas e progressão. Os clubes são uma parte fundamental da experiência do jogo, oferecendo oportunidades únicas de desenvolvimento de personagem e interação social.

## Estrutura de Arquivos

```
data/story_mode/
├── clubs/
│   ├── clube_das_chamas.json
│   ├── clube_elementalistas.json
│   └── ...
└── reputation/
    ├── club_reputation.json
    └── reputation_items.json
```

## Estrutura de Dados

### clube_X.json

```json
{
  "id": "clube_das_chamas",
  "name": "Clube das Chamas",
  "description": "Descrição do clube...",
  "leader": "npc_1",
  "members": ["npc_2", "npc_3"],
  "requirements": {
    "min_stats": {
      "fire_power": 3
    }
  },
  "phases": {
    "introduction": {
      "chapters": ["chapter_1_1", "chapter_1_2"],
      "rewards": {
        "reputation": 10,
        "skills": ["fire_control"]
      }
    },
    "crisis": {
      "chapters": ["chapter_2_1", "chapter_2_2"],
      "requirements": {
        "reputation": 20
      }
    },
    "resolution": {
      "chapters": ["chapter_3_1", "chapter_3_2"],
      "requirements": {
        "reputation": 40
      }
    },
    "final": {
      "chapters": ["chapter_4_1"],
      "requirements": {
        "reputation": 60
      }
    }
  },
  "special_events": [
    {
      "id": "event_1",
      "name": "Festival do Fogo",
      "requirements": {
        "reputation": 30
      },
      "rewards": {
        "reputation": 15,
        "items": ["fire_crystal"]
      }
    }
  ]
}
```

## Fases do Clube

### 1. Introdução

- Apresentação do clube e seus membros
- Tutorial das mecânicas específicas
- Primeiras missões e interações
- Recompensas iniciais

### 2. Crise

- Conflito ou desafio para o clube
- Escolhas significativas
- Impacto na reputação
- Desenvolvimento de habilidades

### 3. Resolução

- Resolução da crise
- Consequências das escolhas
- Recompensas especiais
- Novas oportunidades

### 4. Final

- Conclusão da história do clube
- Recompensas finais
- Impacto no jogo
- Legado do clube

## Sistema de Reputação

### Níveis de Reputação

1. **Neutro** (0-20)
   - Acesso básico ao clube
   - Interações limitadas

2. **Respeitado** (21-40)
   - Acesso a eventos especiais
   - Descontos em lojas
   - Novas interações

3. **Valorizado** (41-60)
   - Acesso a missões exclusivas
   - Benefícios especiais
   - Influência nas decisões

4. **Líder** (61-80)
   - Acesso a todas as funcionalidades
   - Poder de decisão
   - Recompensas exclusivas

5. **Lenda** (81-100)
   - Status máximo
   - Benefícios únicos
   - Legado no clube

## Eventos Especiais

### Tipos de Eventos

1. **Festivais**
   - Eventos periódicos
   - Recompensas especiais
   - Interações únicas

2. **Competições**
   - Desafios entre membros
   - Prêmios exclusivos
   - Desenvolvimento de habilidades

3. **Missões Especiais**
   - Histórias únicas
   - Recompensas raras
   - Impacto na narrativa

## Integração com Outros Sistemas

### História Principal

- Capítulos especiais baseados no clube
- Escolhas afetam a reputação
- Eventos únicos para membros

### Sistema de Romance

- Rotas românticas com membros do clube
- Eventos especiais para casais
- Benefícios exclusivos

### Sistema de Lojas

- Descontos baseados na reputação
- Itens exclusivos do clube
- Preços especiais para membros

## Exemplos de Uso

### Criando um Novo Clube

1. Crie um novo arquivo `clube_X.json`
2. Defina a estrutura básica (ID, nome, descrição)
3. Configure as fases e requisitos
4. Adicione eventos especiais
5. Integre com outros sistemas

### Adicionando um Evento Especial

1. Atualize o arquivo do clube
2. Defina requisitos e recompensas
3. Crie capítulos específicos
4. Integre com o sistema de reputação

## Boas Práticas

1. **Balanceamento**: Mantenha as recompensas equilibradas
2. **Progressão**: Crie uma curva de progressão clara
3. **Variedade**: Ofereça diferentes tipos de atividades
4. **Integração**: Mantenha conexões com outros sistemas
5. **Feedback**: Forneça feedback claro sobre o progresso 