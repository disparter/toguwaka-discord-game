# Melhorias no Comando "explorar"

## Problema Original
O comando `explorar` sempre retornava o mesmo evento, tornando a experiência de exploração repetitiva e previsível.

## Solução Implementada

### 1. Sistema de Eventos Aleatórios Aprimorado
- **Implementação de histórico de eventos**: Adicionado um sistema que rastreia os últimos eventos exibidos para evitar repetições.
- **Seleção verdadeiramente aleatória**: Modificado o algoritmo de seleção para garantir uma distribuição mais uniforme dos eventos.
- **Logging de eventos**: Adicionado registro de eventos selecionados para facilitar depuração.

### 2. Expansão da Variedade de Eventos
- **Aumento significativo no número de eventos**: Expandido de 5 para 20 eventos diferentes.
- **Sistema de categorias**: Eventos agora são organizados em categorias:
  - Social: Eventos relacionados a interações sociais na academia
  - Treinamento: Eventos focados em aprimoramento de habilidades
  - Combate: Desafios e confrontos com outros estudantes
  - Descoberta: Exploração de locais secretos e artefatos
  - Clube: Atividades relacionadas aos clubes da academia
  - Especial: Eventos raros e únicos

### 3. Sistema de Raridade
- **Níveis de raridade**: Implementado sistema com 5 níveis de raridade para eventos:
  - Comum (50% de chance)
  - Incomum (30% de chance)
  - Raro (15% de chance)
  - Épico (4% de chance)
  - Lendário (1% de chance)
- **Recompensas baseadas em raridade**: Eventos mais raros oferecem recompensas mais valiosas.
- **Indicadores visuais**: Cores e emojis diferentes para cada nível de raridade.

### 4. Efeitos Expandidos
- **Múltiplos atributos**: Eventos agora podem afetar múltiplos atributos simultaneamente.
- **Efeitos positivos e negativos**: Alguns eventos podem melhorar um atributo enquanto prejudicam outro.
- **Bônus para todos os atributos**: Eventos especiais podem aumentar todos os atributos de uma vez.
- **Sistema de itens aprimorado**: Itens com diferentes raridades e efeitos.

### 5. Melhorias na Interface
- **Exibição de categoria e raridade**: O embed do evento agora mostra claramente a categoria e raridade.
- **Emojis temáticos**: Adicionados emojis para categorias e raridades para melhor visualização.
- **Cores baseadas em raridade**: Eventos raros, épicos e lendários têm cores distintas.
- **Exibição detalhada de efeitos**: Todos os efeitos são claramente listados no embed.

### 6. Tratamento de Erros Aprimorado
- **Logging detalhado**: Adicionado logging mais detalhado para facilitar a depuração.
- **Tratamento de exceções**: Implementado tratamento de exceções para evitar falhas no comando.
- **Mensagens de erro amigáveis**: Mensagens de erro mais claras para os usuários.

## Exemplos de Novos Eventos

### Eventos Sociais
- **Festa Surpresa**: Seus colegas organizaram uma festa surpresa para você!
- **Debate Acalorado**: Você se envolveu em um debate sobre teorias de poder.
- **Fofoca Prejudicial**: Alguém espalhou fofocas sobre você pela academia.

### Eventos de Treinamento
- **Treinamento Intensivo**: Você encontrou um local secreto perfeito para treinamento.
- **Livro Antigo de Técnicas**: Na biblioteca, você descobriu um livro antigo com técnicas esquecidas.
- **Lesão no Treinamento**: Você se machucou durante um treinamento intenso.

### Eventos de Combate
- **Torneio Relâmpago**: Você participou de um torneio organizado pelos veteranos.
- **Emboscada de Rivais**: Um grupo de estudantes rivais tentou emboscar você.

### Eventos de Descoberta
- **Sala Secreta**: Você descobriu uma sala secreta na academia com artefatos antigos.
- **Manuscrito Perdido**: Entre livros empoeirados, você encontrou um manuscrito com conhecimentos perdidos.
- **Anomalia Dimensional**: Você testemunhou uma estranha anomalia dimensional.

### Eventos de Clube
- **Projeto Colaborativo**: Seu clube iniciou um projeto e você foi escolhido para liderar.
- **Competição Entre Clubes**: Você representou seu clube em uma competição.

### Eventos Especiais
- **Visita do Diretor**: O diretor da Academia Tokugawa notou seu potencial!
- **Fenômeno Sobrenatural**: Um estranho fenômeno sobrenatural ocorreu enquanto você explorava.

## Conclusão
O comando `explorar` foi significativamente melhorado, oferecendo uma experiência mais variada, interessante e recompensadora para os jogadores. A implementação de categorias, raridades e efeitos expandidos torna a exploração da Academia Tokugawa uma atividade muito mais envolvente.