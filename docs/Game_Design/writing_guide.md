# Guia de Escrita

## Introdução

Este guia foi criado para ajudar novos colaboradores a criar conteúdo para a Academia Tokugawa. Aqui você encontrará informações sobre como estruturar capítulos, criar eventos e integrar diferentes sistemas do jogo.

## Estrutura Básica

### Capítulos

1. **Identificação**
   - Use o formato `chapter_X_Y.json`
   - X representa o arco
   - Y representa o número do capítulo

2. **Elementos Obrigatórios**
   ```json
   {
     "id": "chapter_1_1",
     "title": "Título do Capítulo",
     "text": "Texto do capítulo...",
     "background_image": "images/story/chapter_1_1.jpg"
   }
   ```

3. **Elementos Opcionais**
   ```json
   {
     "choices": [...],
     "skill_checks": [...],
     "club_progression": {...},
     "romance_route": {...}
   }
   ```

### Eventos

1. **Identificação**
   - Use o formato `event_X.json`
   - X representa o número do evento

2. **Elementos Obrigatórios**
   ```json
   {
     "id": "event_1",
     "name": "Nome do Evento",
     "description": "Descrição do evento...",
     "requirements": {...}
   }
   ```

## Boas Práticas

### Escrita

1. **Tom e Estilo**
   - Mantenha um tom consistente
   - Use linguagem apropriada para o público
   - Evite gírias excessivas
   - Mantenha a coerência com o universo

2. **Estrutura**
   - Comece com um gancho
   - Desenvolva o conflito
   - Crie um clímax
   - Resolva de forma satisfatória

3. **Personagens**
   - Mantenha a personalidade consistente
   - Use diálogos naturais
   - Desenvolva arcos de personagem
   - Respeite o background estabelecido

### Integração

1. **Sistema de Clubes**
   - Considere o nível de reputação
   - Respeite as fases do clube
   - Integre com eventos especiais
   - Mantenha a coerência com a história do clube

2. **Sistema de Romance**
   - Respeite os níveis de relacionamento
   - Crie momentos significativos
   - Mantenha a personalidade do personagem
   - Ofereça escolhas impactantes

3. **Sistema de Imagens**
   - Use imagens apropriadas
   - Mantenha a consistência visual
   - Forneça alternativas quando necessário
   - Documente as referências de imagem

## Exemplos

### Capítulo Básico

```json
{
  "id": "chapter_1_1",
  "title": "Primeiro Dia",
  "text": "O sol nasce sobre a Academia Tokugawa...",
  "background_image": "images/story/chapter_1_1.jpg",
  "choices": [
    {
      "text": "Explorar o campus",
      "next_chapter": "chapter_1_2",
      "effects": {
        "reputation": {
          "clube_das_chamas": 5
        }
      }
    },
    {
      "text": "Ir para a sala de aula",
      "next_chapter": "chapter_1_3",
      "effects": {
        "skills": {
          "intelligence": 2
        }
      }
    }
  ]
}
```

### Evento Especial

```json
{
  "id": "event_1",
  "name": "Festival do Fogo",
  "description": "O Clube das Chamas organiza seu festival anual...",
  "requirements": {
    "club_membership": "clube_das_chamas",
    "reputation": 30
  },
  "choices": [
    {
      "text": "Participar da competição",
      "effects": {
        "reputation": 10,
        "skills": {
          "fire_power": 5
        }
      }
    },
    {
      "text": "Ajudar na organização",
      "effects": {
        "reputation": 15,
        "relationships": {
          "npc_1": 5
        }
      }
    }
  ]
}
```

## Checklist de Revisão

### Antes de Enviar

1. **Estrutura**
   - [ ] IDs únicos e consistentes
   - [ ] Todos os campos obrigatórios preenchidos
   - [ ] Formato JSON válido
   - [ ] Referências corretas

2. **Conteúdo**
   - [ ] Texto revisado
   - [ ] Escolhas significativas
   - [ ] Consequências claras
   - [ ] Integração com sistemas

3. **Imagens**
   - [ ] Imagens disponíveis
   - [ ] Referências corretas
   - [ ] Alternativas definidas
   - [ ] Direitos autorais verificados

4. **Testes**
   - [ ] Todos os caminhos testados
   - [ ] Requisitos verificados
   - [ ] Efeitos funcionando
   - [ ] Integrações testadas

## Recursos Úteis

### Ferramentas

1. **Editores**
   - VS Code com extensão JSON
   - JSONLint para validação
   - Git para controle de versão

2. **Referências**
   - `structured_story.json` para estrutura
   - `chapter_schema.json` para validação
   - Documentação dos sistemas

### Suporte

1. **Canais**
   - Discord para discussão
   - Issues no GitHub
   - Pull Requests para revisão

2. **Documentação**
   - Guias específicos por sistema
   - Exemplos de código
   - Templates prontos

## Conclusão

Este guia é um ponto de partida. Use-o como referência, mas não tenha medo de inovar e trazer novas ideias. O importante é manter a qualidade e a coerência com o universo da Academia Tokugawa. 