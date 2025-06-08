# Estrutura da História

## Visão Geral

O sistema de história da Academia Tokugawa é baseado em uma estrutura modular e flexível, permitindo narrativas complexas com múltiplos caminhos, escolhas significativas e integração com outros sistemas (clubes, romance, etc.).

## Estrutura de Arquivos

```
data/story_mode/
├── structured_story.json      # Estrutura principal da história
├── chapters/                  # Capítulos individuais
│   ├── chapter_1_1.json      # Capítulo 1.1
│   ├── chapter_1_2.json      # Capítulo 1.2
│   └── ...
└── assets/
    └── images/
        └── story/            # Imagens da história
            ├── backgrounds/  # Imagens de fundo
            ├── characters/   # Imagens de personagens
            └── locations/    # Imagens de locais
```

## Estrutura de Dados

### structured_story.json

O arquivo central que define a estrutura da história:

```json
{
  "chapters": {
    "chapter_1_1": {
      "title": "Título do Capítulo",
      "description": "Descrição do capítulo",
      "requirements": {
        "previous_chapters": ["chapter_1_0"],
        "min_stats": {
          "intelligence": 5
        }
      },
      "next_chapters": ["chapter_1_2", "chapter_1_3"],
      "club_requirements": {
        "clube_das_chamas": 2
      }
    }
  },
  "arcs": {
    "arc_1": {
      "title": "Título do Arco",
      "chapters": ["chapter_1_1", "chapter_1_2", "chapter_1_3"],
      "requirements": {
        "min_reputation": {
          "clube_das_chamas": 50
        }
      }
    }
  }
}
```

### chapter_X_Y.json

Estrutura de um capítulo individual:

```json
{
  "id": "chapter_1_1",
  "title": "Título do Capítulo",
  "text": "Texto do capítulo...",
  "background_image": "images/story/backgrounds/chapter_1_1.jpg",
  "character_images": {
    "npc_1": "images/story/characters/npc_1/normal.jpg",
    "npc_2": "images/story/characters/npc_2/happy.jpg"
  },
  "location_image": "images/story/locations/classroom.jpg",
  "choices": [
    {
      "text": "Escolha 1",
      "next_chapter": "chapter_1_2",
      "effects": {
        "reputation": {
          "clube_das_chamas": 10
        }
      }
    }
  ],
  "skill_checks": [
    {
      "skill": "intelligence",
      "difficulty": 5,
      "success_chapter": "chapter_1_2",
      "failure_chapter": "chapter_1_3"
    }
  ],
  "club_progression": {
    "clube_das_chamas": 1
  },
  "romance_route": {
    "character": "npc_1",
    "points": 5
  }
}
```

## Sistema de Imagens

### Estrutura de Imagens

1. **Imagens de Fundo**
   - Localização: `images/story/backgrounds/`
   - Formato: `chapter_X_Y.jpg`
   - Resolução recomendada: 1920x1080

2. **Imagens de Personagens**
   - Localização: `images/story/characters/[npc_id]/`
   - Formatos: `normal.jpg`, `happy.jpg`, `sad.jpg`, etc.
   - Resolução recomendada: 800x1200

3. **Imagens de Locais**
   - Localização: `images/story/locations/`
   - Formato: `[location_name].jpg`
   - Resolução recomendada: 1920x1080

### Sistema de Fallback

1. **Imagens de Fundo**
   - Fallback padrão: `images/story/backgrounds/default.jpg`
   - Fallback por capítulo: `images/story/backgrounds/chapter_X_default.jpg`

2. **Imagens de Personagens**
   - Fallback padrão: `images/story/characters/default/normal.jpg`
   - Fallback por personagem: `images/story/characters/[npc_id]/default.jpg`

3. **Imagens de Locais**
   - Fallback padrão: `images/story/locations/default.jpg`
   - Fallback por tipo: `images/story/locations/[type]_default.jpg`

## Elementos Principais

### Capítulos

- **ID**: Identificador único do capítulo
- **Título**: Nome do capítulo
- **Texto**: Conteúdo narrativo
- **Imagens**: Sistema completo de imagens
- **Escolhas**: Opções disponíveis para o jogador
- **Verificações de Habilidade**: Testes de habilidades
- **Progressão de Clube**: Impacto no progresso do clube
- **Rota de Romance**: Impacto no relacionamento romântico

### Arcos

- **Título**: Nome do arco
- **Capítulos**: Sequência de capítulos
- **Requisitos**: Condições para acessar o arco
- **Recompensas**: Benefícios ao completar o arco

## Sistema de Progressão

### Verificações de Habilidade

```json
{
  "skill_checks": [
    {
      "skill": "intelligence",
      "difficulty": 5,
      "success_chapter": "chapter_1_2",
      "failure_chapter": "chapter_1_3"
    }
  ]
}
```

### Verificações de Clube

```json
{
  "club_power_check": {
    "club": "clube_das_chamas",
    "required_power": 3,
    "success_chapter": "chapter_1_2",
    "failure_chapter": "chapter_1_3"
  }
}
```

## Integração com Outros Sistemas

### Clubes

- Progressão de clube afeta capítulos disponíveis
- Eventos de clube podem desbloquear capítulos especiais
- Reputação com clube influencia escolhas disponíveis

### Romance

- Escolhas afetam pontos de romance
- Capítulos especiais baseados no nível de relacionamento
- Múltiplos finais baseados nas escolhas

### Imagens

- Sistema completo de imagens dinâmicas
- Fallback para imagens não encontradas
- Integração com sistema de personagens

## Regras de Continuidade

1. **Sem Dead Ends**: Todo caminho deve levar a um próximo capítulo
2. **Checkpoints**: Pontos de salvamento em momentos importantes
3. **Fallback Visual**: Sistema robusto de fallback para imagens
4. **Consistência**: Manter coerência entre escolhas e consequências

## Exemplos de Uso

### Criando um Novo Capítulo

1. Crie um novo arquivo `chapter_X_Y.json`
2. Defina a estrutura básica (ID, título, texto)
3. Adicione escolhas e verificações
4. Configure o sistema de imagens
5. Integre com sistemas de clube e romance

### Adicionando um Novo Arco

1. Atualize `structured_story.json`
2. Crie os capítulos necessários
3. Defina requisitos e recompensas
4. Integre com sistemas existentes

## Boas Práticas

1. **Organização**: Mantenha uma estrutura clara de arquivos
2. **Nomenclatura**: Use IDs consistentes e descritivos
3. **Documentação**: Comente escolhas importantes
4. **Testes**: Verifique todos os caminhos possíveis
5. **Imagens**: Mantenha um padrão de nomenclatura
6. **Fallback**: Sempre forneça alternativas para imagens 