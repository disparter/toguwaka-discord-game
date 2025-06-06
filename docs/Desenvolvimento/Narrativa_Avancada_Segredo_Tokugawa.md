# Implementação da Narrativa Avançada: "O Segredo de Tokugawa"

Este documento descreve a implementação da narrativa oculta "O Segredo de Tokugawa" e os sistemas de dilemas morais e eventos coletivos na Academia Tokugawa.

## Visão Geral das Implementações

### 1. Narrativa Oculta: O Segredo de Tokugawa

Foi implementada uma camada de mistério à escola através da narrativa oculta "O Segredo de Tokugawa". Esta narrativa é descoberta pelos jogadores de forma fragmentada através de:

- **Explorações especiais** com baixa probabilidade de trigger
- **Eventos de grupo** que requerem colaboração de múltiplos jogadores
- **Interações específicas de clubes** que envolvem competição ou cooperação

A documentação completa do segredo está disponível em:
- `docs/Lore/tokugawa_secret.md` - Documento base para rastrear o progresso coletivo
- `docs/Lore/segredo_tokugawa.md` - Detalhes completos do lore para desenvolvedores

### 2. Eventos Coletivos e Competitivos

Foram implementados eventos que dependem de múltiplos jogadores para serem desencadeados ou resolvidos:

- **Motins** - Jogadores podem apoiar ou reprimir protestos na academia
- **Eleições do Conselho Escolar** - Afetam o equilíbrio de poder entre os clubes
- **Sabotagens** - Permitem que alunos atuem secretamente para atrapalhar rivais

Estes eventos impactam narrativas futuras, sistemas de ranking global e a economia do jogo.

A documentação dos eventos coletivos está disponível em:
- `docs/Lore/eventos_coletivos.md`

### 3. Dilemas Morais e Ambiguidade

Foram introduzidos dilemas morais em eventos narrativos, como:
- Escolher entre ajudar um amigo ou ganhar recompensas exclusivas
- Decidir entre revelar informações sobre o "Segredo de Tokugawa" ou guardá-las
- Fazer pactos com clubes rivais que podem minar o prestígio do próprio clube

Um sistema de rastreamento de decisões morais foi implementado para moldar como futuros eventos e diálogos se desenvolvem para cada jogador.

### 4. Tom Ambíguo nas Interações

Os diálogos do sistema e eventos do jogo foram ajustados para incorporar um tom mais ambíguo, incentivando os jogadores a interpretarem os eventos de formas diferentes.

### 5. Memória Coletiva dos Jogadores

Foi implementado um sistema para registrar ações coletivas, eventos desbloqueados e decisões de impacto moral, criando uma "memória coletiva" que influencia o mundo do jogo.

## Arquivos Criados

### Documentação

1. **`docs/Lore/tokugawa_secret.md`**
   - Documento base para rastrear o progresso coletivo na descoberta do Segredo de Tokugawa
   - Contém fragmentos descobertos e eventos relacionados
   - Será atualizado à medida que os jogadores avançam na narrativa

2. **`docs/Lore/segredo_tokugawa.md`**
   - Documento detalhado com o lore completo do Segredo de Tokugawa
   - Inclui a verdadeira história da academia, facções secretas, e pistas a serem descobertas
   - Recurso para desenvolvedores e moderadores

3. **`docs/Lore/eventos_coletivos.md`**
   - Documentação técnica dos eventos coletivos
   - Descreve mecânicas de motins, eleições e sabotagens
   - Inclui exemplos de implementação

4. **`docs/Guias_de_Jogo/Dilemas_e_Eventos_Coletivos.md`**
   - Guia para jogadores sobre os novos sistemas
   - Explica como funcionam os dilemas morais e eventos coletivos
   - Inclui comandos e dicas estratégicas

### Código

1. **`cogs/moral_choices.py`**
   - Implementa o cog MoralChoices para gerenciar dilemas morais e eventos coletivos
   - Adiciona os comandos `/dilema` e `/atividade`
   - Inclui sistema de rastreamento de escolhas morais

## Modificações em Arquivos Existentes

1. **`bot.py`**
   - Adicionado 'cogs.moral_choices' à lista de initial_extensions para carregar o novo cog

## Novos Comandos Implementados

### 1. Comando de Dilema

```
/dilema
```

Este comando apresenta ao jogador um dilema moral aleatório com múltiplas escolhas. Cada escolha tem consequências diferentes em termos de atributos, reputação com facções e tendência moral.

### 2. Comando de Atividade

```
/atividade [tipo] [ação] [alvo]
```

Este comando permite participar de diferentes tipos de atividades coletivas:

- **Tipos**: motim, eleicao, sabotagem, coletivo, dilema
- **Ações**: info, participar, apoiar, reprimir, votar, candidatar, planejar, executar, investigar
- **Alvo**: ID do evento, nome do candidato, etc. (opcional em alguns casos)

## Sistema de Moralidade

Foi implementado um sistema para rastrear as escolhas morais dos jogadores, categorizando-as em diferentes tendências:

- Leal
- Rebelde
- Justo
- Pragmático
- Colaborativo
- Honesto
- Diplomático

Estas tendências influenciam como NPCs e eventos futuros respondem ao jogador.

## Integração com Sistemas Existentes

### 1. Integração com o Sistema de Clubes

Os eventos coletivos e dilemas morais consideram o clube do jogador, oferecendo escolhas e consequências específicas baseadas nessa afiliação.

### 2. Integração com o Sistema de Economia

Eventos coletivos podem afetar a economia do jogo, alterando preços na loja ou desbloqueando novos itens.

### 3. Integração com o Modo História

Dilemas morais e eventos coletivos podem revelar fragmentos do Segredo de Tokugawa, avançando a narrativa principal.

## Próximos Passos

### 1. Expansão de Conteúdo

- Adicionar mais dilemas morais com escolhas e consequências variadas
- Implementar eventos coletivos específicos para cada estação do ano
- Criar dilemas específicos para cada clube

### 2. Refinamento do Sistema de Moralidade

- Implementar um dashboard para jogadores visualizarem sua tendência moral
- Adicionar NPCs que respondem especificamente a certas tendências morais
- Criar recompensas exclusivas para jogadores com tendências morais específicas

### 3. Desenvolvimento da Narrativa do Segredo

- Adicionar mais fragmentos do segredo para serem descobertos
- Implementar eventos especiais quando certos fragmentos são descobertos
- Criar um "evento final" quando todos os fragmentos forem descobertos

## Conclusão

A implementação da narrativa avançada "O Segredo de Tokugawa" e dos sistemas de dilemas morais e eventos coletivos enriquece significativamente a experiência de jogo na Academia Tokugawa. Estas adições criam uma experiência mais imersiva, estratégica e emocionalmente envolvente para os jogadores, incentivando a colaboração, o debate e a exploração do mundo do jogo.