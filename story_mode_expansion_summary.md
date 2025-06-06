# Expansão do Modo História da Academia Tokugawa

## Resumo das Alterações

Foram implementadas as seguintes melhorias no modo história do jogo Academia Tokugawa:

### 1. Adição de Novos Capítulos

Foram adicionados três novos capítulos à história do Ano 1:

#### Capítulo 3: Rivalidades e Alianças
- Explora as complexas relações entre os diferentes clubes da academia
- Apresenta diálogos específicos para cada clube sobre suas alianças e rivalidades
- Oferece escolhas que afetam a compreensão do jogador sobre a política da academia
- Inclui verificações de atributos para desbloquear informações adicionais

#### Capítulo 4: O Segredo da Biblioteca
- Introduz a Biblioteca Proibida como um local secreto na academia
- Oferece diferentes abordagens para acessar conhecimentos restritos
- Inclui verificações de atributos para diferentes estratégias
- Revela informações sobre a origem dos poderes

#### Capítulo 5: O Primeiro Desafio
- Apresenta o primeiro confronto significativo com um antagonista (Drake, o Valentão)
- Oferece múltiplas abordagens para resolver o conflito
- Inclui um sistema de batalha com recompensas baseadas no resultado
- Permite que o jogador prove seu valor na hierarquia da academia

### 2. Aprimoramento da Narrativa

- Aprofundamento das relações entre clubes e suas dinâmicas políticas
- Introdução de segredos e locais ocultos na academia
- Desenvolvimento de personagens secundários (membros dos clubes)
- Criação de um sistema de confronto com consequências na hierarquia

### 3. Atualização da Documentação

- A documentação do modo história foi atualizada para refletir os novos capítulos
- Descrições detalhadas de cada capítulo foram adicionadas
- A sequência de capítulos foi reorganizada para manter a consistência narrativa

### 4. Expansão do Capítulo da Biblioteca Proibida

O Capítulo 4 foi expandido com uma implementação detalhada chamada "O Mistério da Biblioteca Proibida":

- Narrativa ramificada completa com mais de 12 cenas únicas
- Múltiplos caminhos e finais baseados nas decisões do jogador
- Verificações de atributos que testam as estatísticas do jogador (intelecto, carisma, poder)
- Introdução de um novo personagem: Takeshi Koga, um ex-aluno preso entre dimensões
- Exploração de temas de conhecimento proibido e consequências de experimentos perigosos
- Recompensas variadas incluindo experiência, moeda e itens únicos

### 5. Otimização de Dados JSON

Para melhorar o desempenho e a manutenção do código:

- Dados JSON estáticos foram movidos de arrays codificados para arquivos JSON externos
- Criado `data/story_mode/events/event_templates.json` para armazenar modelos de eventos
- Criado `data/story_mode/events/event_choices.json` para armazenar escolhas de eventos
- Modificado `utils/narrative_events.py` para carregar dados desses arquivos JSON
- Adicionados novos modelos de eventos para enriquecer a experiência do jogador

## Próximos Passos

Para futuras expansões do modo história, recomenda-se:

1. Implementar o Capítulo 6 e os capítulos subsequentes do Ano 1
2. Desenvolver os capítulos do Ano 2, conforme descrito na estrutura existente
3. Expandir o sistema de relacionamentos com NPCs
4. Adicionar mais locais secretos e eventos climáticos
5. Implementar consequências de longo prazo para as escolhas dos jogadores
6. Continuar movendo dados estáticos para arquivos JSON para melhorar o desempenho
7. Criar ferramentas para ajudar a gerar e validar conteúdo JSON
8. Implementar um sistema de gerenciamento de conteúdo para atualizações mais fáceis

Esta expansão criativa do modo história enriquece significativamente a experiência dos jogadores, oferecendo uma narrativa mais profunda e interativa que se alinha com a visão original do jogo, enquanto também melhora o desempenho técnico do sistema.
