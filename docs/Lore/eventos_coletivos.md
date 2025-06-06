# Eventos Coletivos e Competitivos

## Visão Geral

Os Eventos Coletivos e Competitivos são atividades que dependem da participação de múltiplos jogadores para serem desencadeados ou resolvidos. Estes eventos enriquecem a experiência de jogo, promovendo interações entre jogadores e criando impactos duradouros no mundo do jogo.

## Tipos de Eventos Coletivos

### 1. Motins

Os Motins são eventos que surgem quando há insatisfação generalizada entre os estudantes da academia. Eles podem ser desencadeados por decisões controversas da administração, revelações sobre o Segredo de Tokugawa, ou conflitos entre facções.

#### Mecânica
- **Início**: Um Motim começa quando pelo menos 10 jogadores expressam insatisfação com um aspecto específico da academia.
- **Participação**: Os jogadores podem escolher apoiar ou reprimir o Motim.
- **Resolução**: O resultado do Motim é determinado pela proporção de jogadores que o apoiam versus aqueles que o reprimem.
- **Consequências**: 
  - **Sucesso**: Mudanças nas políticas da academia, acesso a áreas restritas, novos itens na loja.
  - **Fracasso**: Aumento da vigilância, restrições temporárias, penalidades para os participantes.

### 2. Eleições do Conselho Escolar

As Eleições do Conselho Escolar ocorrem periodicamente e permitem que os jogadores influenciem o equilíbrio de poder entre os clubes da academia.

#### Mecânica
- **Candidatura**: Jogadores com alto prestígio podem se candidatar a posições no Conselho.
- **Campanha**: Os candidatos podem fazer promessas e alianças para ganhar apoio.
- **Votação**: Todos os jogadores podem votar em seus candidatos preferidos.
- **Resultados**: Os candidatos eleitos ganham habilidades especiais e podem implementar políticas que afetam todos os jogadores.
- **Consequências**:
  - Alteração no equilíbrio de poder entre clubes
  - Mudanças nos preços da loja e disponibilidade de itens
  - Novas oportunidades de exploração e eventos

### 3. Sabotagens

As Sabotagens são ações secretas que os jogadores podem realizar para atrapalhar rivais ou facções opostas.

#### Mecânica
- **Planejamento**: Jogadores podem formar grupos secretos para planejar sabotagens.
- **Execução**: A sabotagem requer a participação coordenada de múltiplos jogadores.
- **Detecção**: Outros jogadores podem tentar descobrir e impedir a sabotagem.
- **Consequências**:
  - **Sucesso**: Enfraquecimento temporário do alvo, vantagens para os sabotadores.
  - **Descoberta**: Penalidades para os sabotadores, aumento de prestígio para os que descobriram.

## Implementação Técnica

### Comandos

1. **`/atividade motim [apoiar|reprimir]`**
   - Permite que o jogador participe de um motim ativo, escolhendo apoiá-lo ou reprimi-lo.

2. **`/atividade eleicao [votar|candidatar] [candidato|cargo]`**
   - Permite que o jogador vote em um candidato ou se candidate a um cargo no Conselho Escolar.

3. **`/atividade sabotagem [planejar|executar|investigar] [alvo]`**
   - Permite que o jogador planeje, execute ou investigue uma sabotagem.

4. **`/atividade coletivo [info|participar] [id_evento]`**
   - Fornece informações sobre eventos coletivos ativos ou permite a participação em um evento específico.

### Rastreamento de Eventos

Os eventos coletivos são rastreados em um sistema centralizado que:
- Registra a participação de cada jogador
- Calcula o progresso e resultado do evento
- Aplica as consequências apropriadas
- Atualiza o histórico de eventos para referência futura

## Impacto no Jogo

Os Eventos Coletivos e Competitivos têm impactos significativos no mundo do jogo:

### Impacto Narrativo
- Desenvolvimento de arcos narrativos baseados nas ações coletivas dos jogadores
- Revelação de novos fragmentos do Segredo de Tokugawa
- Evolução das relações entre clubes e facções

### Impacto Econômico
- Alteração nos preços da loja com base nos resultados de eleições e motins
- Desbloqueio de novos itens limitados após eventos bem-sucedidos
- Bônus econômicos para participantes de eventos vitoriosos

### Impacto Social
- Formação de alianças e rivalidades entre jogadores
- Criação de reputação baseada em ações em eventos coletivos
- Desenvolvimento de uma comunidade mais engajada e colaborativa

## Exemplos de Eventos

### Exemplo 1: Motim contra Restrições de Acesso
*Trigger: Revelação de que a administração está ocultando informações sobre o Evento Zero*

Os jogadores podem escolher apoiar o motim para exigir acesso a documentos restritos, ou reprimi-lo para manter a ordem. Se bem-sucedido, novos documentos sobre o Segredo de Tokugawa são revelados.

### Exemplo 2: Eleição para Presidente do Conselho
*Trigger: Início do novo ano letivo*

Os jogadores podem se candidatar ou apoiar candidatos com diferentes plataformas (mais liberdade vs. mais segurança). O vencedor pode implementar políticas que afetam o acesso a áreas da academia e os preços na loja.

### Exemplo 3: Sabotagem do Experimento Interdimensional
*Trigger: Descoberta de um experimento perigoso sendo conduzido secretamente*

Jogadores podem formar um grupo para sabotar o experimento, enquanto outros podem tentar protegê-lo. O resultado afeta o progresso na descoberta do Segredo de Tokugawa e pode desbloquear ou bloquear certos caminhos narrativos.

## Integração com o Sistema de Moralidade

As ações dos jogadores em eventos coletivos afetam sua moralidade e reputação:

- **Apoiar motins**: Pode ser visto como rebelde ou justo, dependendo da causa
- **Reprimir motins**: Pode ser visto como leal ou opressor
- **Participar de sabotagens**: Afeta negativamente a reputação se descoberto
- **Denunciar sabotagens**: Aumenta a reputação com a administração, mas pode diminuir com certos grupos

Estas decisões são registradas no sistema de karma/moralidade do jogador e influenciam como NPCs e eventos futuros respondem a ele.

## Conclusão

Os Eventos Coletivos e Competitivos adicionam uma camada de profundidade social e estratégica ao jogo, incentivando os jogadores a colaborarem, competirem e formarem alianças. Eles criam um mundo dinâmico que evolui com base nas ações coletivas dos jogadores, tornando cada servidor do Discord uma experiência única.