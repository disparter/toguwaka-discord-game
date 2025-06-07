# Plano de Implementação dos Requisitos

## Visão Geral

Este documento detalha o plano de implementação para os requisitos especificados na tarefa de expansão do modo história da Academia Tokugawa:

1. **Expansão de Capítulos Subsequentes**: Aplicar o mesmo nível de detalhe e ramificação aos capítulos seguintes
2. **Implementação de Consequências de Longo Prazo**: Desenvolver eventos futuros que referenciem escolhas iniciais
3. **Sistema de Tags Narrativas**: Implementar um sistema formal de tags para rastrear relações com NPCs
4. **Testes de Usuário**: Coletar feedback sobre a experiência narrativa expandida
5. **Dashboard de Comparação**: Desenvolver a ferramenta para comparação de decisões entre jogadores

## 1. Expansão de Capítulos Subsequentes

### Análise da Situação Atual
- O arco de introdução está bem desenvolvido com capítulos detalhados
- Os arcos acadêmico, mistério e despertar estão criados como estruturas vazias
- É necessário expandir esses arcos com o mesmo nível de detalhe do arco de introdução

### Plano de Implementação

#### 1.1 Arco Acadêmico
Criar os seguintes capítulos no diretório `/data/story_mode/arcs/academic/`:

1. **chapter_2_1.json**: "Primeiro Dia de Aula"
   - Introdução aos professores e disciplinas
   - Escolhas que afetam a reputação acadêmica
   - Ramificações baseadas no clube escolhido anteriormente

2. **chapter_2_2.json**: "Desafio Acadêmico"
   - Teste de habilidades específicas do clube
   - Múltiplos caminhos para resolver o desafio
   - Consequências baseadas no desempenho

3. **chapter_2_3.json**: "Projeto Especial"
   - Colaboração com outros estudantes
   - Escolhas que afetam relacionamentos com NPCs
   - Descoberta de segredos da academia

#### 1.2 Arco de Mistério
Criar os seguintes capítulos no diretório `/data/story_mode/arcs/mystery/`:

1. **chapter_3_1.json**: "Rumores Estranhos"
   - Introdução ao mistério do "Incidente Zero"
   - Escolhas de investigação vs. ignorar
   - Primeiras pistas sobre anomalias na academia

2. **chapter_3_2.json**: "A Biblioteca Proibida"
   - Exploração de área restrita
   - Descoberta de documentos secretos
   - Escolhas que afetam o conhecimento sobre o mistério

3. **chapter_3_3.json**: "Confronto com a Verdade"
   - Decisão sobre o que fazer com as informações descobertas
   - Alianças com diferentes facções
   - Consequências significativas para a narrativa futura

#### 1.3 Arco de Despertar
Criar os seguintes capítulos no diretório `/data/story_mode/arcs/awakening/`:

1. **chapter_4_1.json**: "Sinais de Mudança"
   - Primeiros sinais de evolução de poderes
   - Escolhas sobre como lidar com novas habilidades
   - Reações de NPCs às mudanças

2. **chapter_4_2.json**: "O Ritual de Despertar"
   - Cerimônia para desbloquear potencial completo
   - Escolhas que determinam a direção do despertar
   - Consequências para a hierarquia da academia

3. **chapter_4_3.json**: "Novo Potencial"
   - Exploração das novas habilidades
   - Escolhas sobre como usar o poder
   - Reações das diferentes facções

## 2. Implementação de Consequências de Longo Prazo

### Análise da Situação Atual
- Existe um sistema de consequências dinâmicas em `story_mode/consequences.py`
- O sistema já suporta rastreamento de escolhas e padrões
- É necessário expandir para criar mais "Momentos de Definição" que referenciem escolhas iniciais

### Plano de Implementação

#### 2.1 Expansão do Sistema de Momentos de Definição
Modificar a classe `MomentsOfDefinition` em `story_mode/consequences.py` para adicionar novos momentos:

1. **Momento "Lealdade Testada"**
   - Trigger: Escolhas nos capítulos do arco acadêmico
   - Referência: Escolhas de lealdade no arco de introdução
   - Consequências: Diferentes reações de professores e acesso a conhecimento exclusivo

2. **Momento "Segredos Revelados"**
   - Trigger: Progresso no arco de mistério
   - Referência: Curiosidade demonstrada em capítulos anteriores
   - Consequências: Revelações diferentes baseadas em escolhas passadas

3. **Momento "Potencial Realizado"**
   - Trigger: Capítulos do arco de despertar
   - Referência: Abordagem de treinamento nos primeiros capítulos
   - Consequências: Diferentes manifestações de poder baseadas em escolhas anteriores

#### 2.2 Sistema de Variáveis Persistentes
Implementar um sistema para rastrear variáveis narrativas de longo prazo:

1. Adicionar à estrutura `StoryProgress` em `story_mode/progress.py`:
```python
"narrative_variables": Dict[str, Any]
```

2. Implementar métodos para gerenciar essas variáveis:
```python
def set_narrative_variable(self, player_data: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """Set a narrative variable that persists across chapters."""
    
def get_narrative_variable(self, player_data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a narrative variable value."""
```

3. Utilizar essas variáveis nos novos capítulos para criar continuidade narrativa

## 3. Sistema de Tags Narrativas para Relações com NPCs

### Análise da Situação Atual
- Existe um sistema básico de afinidade com NPCs em `story_mode/npc.py`
- O sistema atual rastreia apenas um valor numérico de afinidade
- É necessário expandir para um sistema de tags que capture aspectos específicos dos relacionamentos

### Plano de Implementação

#### 3.1 Definição da Estrutura de Tags
Modificar a estrutura `character_relationships` em `story_mode/progress.py`:

```python
"character_relationships": {
    "npc_name": {
        "affinity": int,
        "tags": List[str],
        "interactions": Dict[str, Any],
        "relationship_type": str
    }
}
```

#### 3.2 Implementação do Sistema de Tags
Adicionar à classe `BaseNPC` em `story_mode/npc.py`:

1. **Método para adicionar tags**:
```python
def add_relationship_tag(self, player_data: Dict[str, Any], tag: str) -> Dict[str, Any]:
    """Add a relationship tag to track specific aspects of the relationship."""
```

2. **Método para verificar tags**:
```python
def has_relationship_tag(self, player_data: Dict[str, Any], tag: str) -> bool:
    """Check if a relationship has a specific tag."""
```

3. **Método para definir tipo de relacionamento**:
```python
def set_relationship_type(self, player_data: Dict[str, Any], relationship_type: str) -> Dict[str, Any]:
    """Set the type of relationship (mentor, rival, friend, etc.)."""
```

#### 3.3 Integração com o Sistema de Diálogos
Modificar o método `get_dialogue` em `BaseNPC` para considerar tags:

```python
def get_dialogue(self, dialogue_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
    """Returns dialogue based on affinity level and relationship tags."""
    # Existing code...
    
    # Check for tag-specific dialogues
    relationship = self._get_relationship(player_data)
    tags = relationship.get("tags", [])
    
    for tag in tags:
        tag_key = f"{dialogue_id}_{tag}"
        if tag_key in self.dialogues:
            return self.dialogues[tag_key]
    
    # Continue with existing code...
```

## 4. Testes de Usuário e Coleta de Feedback

### Análise da Situação Atual
- Não existe um sistema formal para coletar feedback dos usuários
- É necessário implementar mecanismos para coletar feedback sobre a experiência narrativa

### Plano de Implementação

#### 4.1 Comando de Feedback
Implementar um novo comando Discord `/feedback` em um novo arquivo `cogs/feedback.py`:

```python
@commands.slash_command(name="feedback", description="Envie seu feedback sobre o modo história")
async def feedback_command(
    self, 
    interaction: discord.Interaction,
    tipo: Option(str, "Tipo de feedback", choices=["Bug", "Sugestão", "Elogio", "Crítica"]),
    capitulo: Option(str, "Capítulo (opcional)", required=False),
    mensagem: Option(str, "Sua mensagem de feedback")
):
    """Comando para enviar feedback sobre o modo história."""
    # Implementation...
```

#### 4.2 Sistema de Pesquisas Pós-Capítulo
Modificar `story_mode/story_mode.py` para exibir pesquisas após a conclusão de capítulos:

1. Adicionar método para criar pesquisas:
```python
async def create_chapter_survey(self, interaction: discord.Interaction, chapter_id: str):
    """Create a survey after chapter completion."""
    # Implementation...
```

2. Integrar com a conclusão de capítulos:
```python
# After chapter completion
await self.create_chapter_survey(interaction, chapter_id)
```

#### 4.3 Sistema de Classificação de Eventos
Implementar um sistema de classificação opcional para eventos e capítulos:

1. Adicionar componentes de classificação aos embeds de conclusão:
```python
# Add rating buttons to chapter completion embed
view = RatingView(chapter_id)
await interaction.followup.send(embed=embed, view=view)
```

2. Criar classe para processar classificações:
```python
class RatingView(discord.ui.View):
    """View for rating chapters and events."""
    # Implementation...
```

## 5. Dashboard de Comparação de Decisões

### Análise da Situação Atual
- Existe uma implementação robusta do dashboard em `story_mode/decision_dashboard.py`
- O sistema já suporta comparação de escolhas, análise de caminhos e reflexões éticas
- É necessário integrar com os novos capítulos e o sistema de tags de relacionamento

### Plano de Implementação

#### 5.1 Integração com o Sistema de Tags de Relacionamento
Modificar a classe `DecisionTracker` em `story_mode/decision_dashboard.py`:

1. Adicionar método para analisar relacionamentos com NPCs:
```python
def analyze_npc_relationships(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze player's relationships with NPCs including tags."""
    # Implementation...
```

2. Integrar com o método `generate_dashboard`:
```python
# In generate_dashboard method
relationships = self.analyze_npc_relationships(player_data)
# Add to return dictionary
"npc_relationships": relationships
```

#### 5.2 Visualizações para Novos Capítulos
Atualizar o comando `/dashboard caminhos` em `cogs/decision_dashboard.py` para incluir os novos arcos narrativos:

```python
# Update path visualization to include new arcs
arcs = ["introduction", "academic", "mystery", "awakening"]
# Implementation...
```

#### 5.3 Melhorias na Interface do Usuário
Aprimorar a apresentação visual do dashboard:

1. Adicionar gráficos mais detalhados usando matplotlib
2. Criar visualizações específicas para cada arco narrativo
3. Implementar uma visualização de rede para relacionamentos com NPCs

## Plano de Testes

Para garantir que todas as implementações funcionem conforme esperado, serão desenvolvidos os seguintes testes:

1. **Testes de Capítulos**:
   - Verificar se todos os caminhos narrativos são acessíveis
   - Testar condições e transições entre capítulos
   - Validar a integração com o sistema de progresso

2. **Testes de Consequências**:
   - Verificar se os momentos de definição são acionados corretamente
   - Testar se as escolhas anteriores afetam eventos futuros
   - Validar o sistema de variáveis narrativas persistentes

3. **Testes do Sistema de Tags**:
   - Verificar a adição e remoção de tags de relacionamento
   - Testar a integração com o sistema de diálogos
   - Validar diferentes tipos de relacionamento

4. **Testes de Feedback**:
   - Verificar se o comando de feedback funciona corretamente
   - Testar o sistema de pesquisas pós-capítulo
   - Validar o armazenamento e recuperação de classificações

5. **Testes do Dashboard**:
   - Verificar a geração de todas as visualizações
   - Testar a integração com o sistema de tags de relacionamento
   - Validar a apresentação de dados para os novos capítulos

## Cronograma de Implementação

1. **Semana 1**: Expansão de Capítulos Subsequentes
   - Implementação do Arco Acadêmico
   - Implementação do Arco de Mistério
   - Implementação do Arco de Despertar

2. **Semana 2**: Consequências de Longo Prazo e Sistema de Tags
   - Expansão do Sistema de Momentos de Definição
   - Implementação do Sistema de Variáveis Persistentes
   - Implementação do Sistema de Tags de Relacionamento

3. **Semana 3**: Feedback e Dashboard
   - Implementação do Sistema de Feedback
   - Integração do Dashboard com Novos Sistemas
   - Testes e Ajustes Finais

## Conclusão

Este plano de implementação aborda todos os requisitos especificados na tarefa de expansão do modo história da Academia Tokugawa. A implementação seguirá as melhores práticas de desenvolvimento, mantendo a compatibilidade com os sistemas existentes e garantindo uma experiência narrativa rica e imersiva para os jogadores.