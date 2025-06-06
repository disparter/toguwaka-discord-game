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

#### Capítulo 6: O Despertar do Potencial
- Explora o despertar de novos poderes no personagem do jogador
- Apresenta o conceito de "Despertar Secundário" inspirado em histórias de super-heróis
- Introduz facções políticas dentro da academia (Elite e Igualitários)
- Oferece escolhas significativas sobre alianças e posicionamento na hierarquia
- Aborda temas de discriminação baseada em poder e responsabilidade
- Inclui mais de 15 cenas com múltiplos caminhos narrativos

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

### 5. Adição do Capítulo "O Despertar do Potencial"

Um novo capítulo completo foi implementado, inspirado em histórias como Unordinary e X-Men:

- Narrativa ramificada com mais de 15 cenas únicas e múltiplos finais
- Foco em temas de descoberta de poderes e evolução de habilidades
- Introdução do conceito de "Despertar Secundário" como ponto central da trama
- Exploração de dinâmicas sociais e políticas baseadas em níveis de poder
- Apresentação de duas facções opostas: a Elite (que defende a hierarquia) e os Igualitários (que lutam por igualdade)
- Personagens novos como Professor Takeda, Drake, Aria e o líder dos Igualitários
- Escolhas morais que afetam a reputação do jogador e seu lugar na sociedade da academia
- Sistema de consequências que reflete as decisões do jogador em seu desenvolvimento
- Recompensas especiais incluindo o "Cristal do Despertar", um item raro que melhora o controle de habilidades

### 6. Otimização de Dados JSON

Para melhorar o desempenho e a manutenção do código:

- Dados JSON estáticos foram movidos de arrays codificados para arquivos JSON externos
- Criado `data/story_mode/events/event_templates.json` para armazenar modelos de eventos
- Criado `data/story_mode/events/event_choices.json` para armazenar escolhas de eventos
- Modificado `utils/narrative_events.py` para carregar dados desses arquivos JSON
- Adicionados novos modelos de eventos para enriquecer a experiência do jogador

## Implementação dos Próximos Passos

Os próximos passos recomendados anteriormente foram implementados:

### 1. Correção do erro "Next chapter not found: 1_1_2"

Foi corrigido um erro na lógica de navegação entre capítulos que causava a mensagem "Next chapter not found: 1_1_2". O problema ocorria quando a propriedade `next_chapter` de um capítulo continha apenas um número (ex: "2"), e o sistema construía incorretamente o ID do próximo capítulo.

### 2. Implementação dos capítulos ausentes "1_4_success" e "1_4_failure"

Foram adicionados os seguintes capítulos que estavam faltando:

- **1_4_success**: Capítulo que segue após completar com sucesso o desafio no capítulo 1_3
- **1_4_failure**: Capítulo que segue após falhar no desafio do capítulo 1_3

Ambos os capítulos oferecem experiências narrativas diferentes baseadas no desempenho do jogador, mas eventualmente convergem para a mesma linha principal da história (capítulo 1_5).

### 3. Desenvolvimento dos capítulos do Ano 2

Foi criado um novo arquivo `chapter_2.json` com uma estrutura abrangente para o Ano 2 da história, incluindo:

- **2_1**: Introdução ao segundo ano com novas responsabilidades e desafios
- **2_2**: Seleção de especialização baseada no clube do jogador
- **2_3**: Mentoria de um estudante novato chamado Hikari
- **2_4**: Um capítulo ramificado sobre anomalias na floresta
- **Múltiplos caminhos ramificados** (2_5_discovery, 2_5_investigation, 2_5_warning, 2_5_alliance) baseados nas escolhas do jogador

Os capítulos do Ano 2 introduzem novos elementos de gameplay:
- Sistema de especialização para poderes
- Mecânicas de mentoria
- Uma história mais profunda envolvendo o "Evento Zero" e anomalias dimensionais
- Relacionamentos mais complexos com NPCs

### 4. Expansão do sistema de relacionamentos com NPCs

O sistema existente de relacionamentos com NPCs foi analisado e expandido:
- Níveis de afinidade (hostil, não amigável, neutro, amigável, próximo, confiável)
- Opções de diálogo baseadas em afinidade
- Interações específicas para cada personagem

Os capítulos do Ano 2 expandem este sistema com:
- Introdução de relacionamentos mais complexos com novos personagens (ex: Hikari, o mentorado)
- Criação de situações onde relacionamentos passados afetam opções atuais
- Adição de consequências mais significativas para escolhas de relacionamento

### 5. Adição de mais locais secretos e eventos climáticos

O sistema de eventos climáticos existente foi aprimorado e novos locais secretos foram adicionados:
- Adição de uma floresta misteriosa com anomalias
- Criação de novos fenômenos climáticos nos capítulos do Ano 2
- Integração mais profunda dos eventos climáticos com a história

### 6. Implementação de consequências de longo prazo para escolhas dos jogadores

O sistema de progressão da história foi aprimorado para melhor rastrear e utilizar as escolhas dos jogadores:
- Escolhas no Ano 1 agora afetam opções e eventos no Ano 2
- O sistema de mentoria no Ano 2 proporciona consequências de longo prazo
- A história da anomalia cria caminhos ramificados com diferenças significativas

### 7. Movimentação de mais dados estáticos para arquivos JSON

Foram identificados dados codificados no código-fonte e criado um plano para movê-los para arquivos de configuração JSON:
- Constantes do jogo (fatores de HP, níveis de experiência, etc.)
- Raridades de itens
- Resultados de treinamento
- Eventos aleatórios

### 8. Criação de ferramentas para gerar e validar conteúdo JSON

Foi desenvolvido um módulo abrangente de ferramentas JSON (`utils/json_tools.py`) com:
- **JSONValidator**: Valida arquivos JSON contra esquemas
- **JSONGenerator**: Gera arquivos JSON a partir de templates
- **Funções utilitárias**: Para converter constantes, carregar configurações e mesclar arquivos

O módulo lida graciosamente com dependências ausentes e fornece mensagens de erro claras.

### 9. Implementação de um sistema de gerenciamento de conteúdo

Foi criado um sistema de gerenciamento de conteúdo (`utils/content_manager.py`) que fornece:
- Uma interface de linha de comando para gerenciar conteúdo do jogo
- Métodos para listar, criar, editar e excluir conteúdo
- Validação contra esquemas para garantir a integridade dos dados
- Geração de conteúdo baseada em templates
- Registro e tratamento abrangente de erros

## Como Usar as Novas Ferramentas

### Ferramentas JSON

```python
from utils.json_tools import JSONValidator, JSONGenerator, convert_constants_to_json

# Validar arquivos JSON contra esquemas
validator = JSONValidator("data/schemas")
validator.validate_file("data/story_mode/chapters/chapter_1.json", "chapter")

# Gerar arquivos JSON a partir de templates
generator = JSONGenerator("data/templates")
new_content = generator.generate_from_template("event_template", {"name": "Meu Evento"})

# Converter constantes Python para JSON
import utils.game_mechanics.constants as constants
convert_constants_to_json(constants, "data/config")
```

### Sistema de Gerenciamento de Conteúdo

O sistema de gerenciamento de conteúdo pode ser usado via linha de comando:

```bash
# Listar conteúdo disponível
python -m utils.content_manager list --type chapters

# Criar novo conteúdo
python -m utils.content_manager create chapters 1_5 --template chapter_template --data '{"title": "Novo Capítulo"}'

# Editar conteúdo existente
python -m utils.content_manager edit chapters 1_5 --data '{"title": "Capítulo Atualizado"}'

# Validar conteúdo
python -m utils.content_manager validate chapters --id 1_5

# Criar esquema a partir de exemplo
python -m utils.content_manager schema chapters

# Criar template
python -m utils.content_manager template chapter_template --data '{"title": "", "description": ""}'
```

## Próximos Passos

Para futuras expansões do modo história, recomenda-se:

1. **Completar os capítulos do Ano 2**: Finalizar a implementação de todos os caminhos ramificados e desfechos para o Ano 2.

2. **Criar mais templates**: Desenvolver templates para tipos comuns de conteúdo para agilizar a criação de conteúdo.

3. **Desenvolver esquemas para todos os tipos de conteúdo**: Criar esquemas abrangentes para validar todo o conteúdo do jogo.

4. **Mover todos os dados codificados para JSON**: Continuar o processo de mover dados estáticos para arquivos de configuração.

5. **Aprimorar o sistema de gerenciamento de conteúdo**: Adicionar uma interface web para criadores de conteúdo não técnicos.

6. **Adicionar mais testes**: Criar testes unitários para as novas funcionalidades para garantir estabilidade.

Esta expansão do modo história enriquece significativamente a experiência dos jogadores, oferecendo uma narrativa mais profunda e interativa que se alinha com a visão original do jogo, enquanto também melhora o desempenho técnico e a manutenibilidade do sistema.
