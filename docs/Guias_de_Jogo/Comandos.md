# Comandos do Bot Academia Tokugawa

Este guia contém uma lista detalhada de todos os comandos disponíveis no bot Academia Tokugawa, organizados por categoria.

## 🔍 Índice

- [Comandos Básicos](#comandos-básicos)
- [Registro e Informações](#registro-e-informações)
- [Atividades](#atividades)
- [Clubes](#clubes)
- [Economia](#economia)
- [Dicas de Uso](#dicas-de-uso)

## 📝 Comandos Básicos

### `/ping`
- **Descrição**: Verifica se o bot está funcionando
- **Uso**: Digite `/ping` em qualquer canal
- **Resposta**: O bot responderá com "Pong!" e o tempo de resposta
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Nenhuma

### `/ajuda`
- **Descrição**: Exibe a lista de comandos disponíveis
- **Uso**: Digite `/ajuda` em qualquer canal
- **Resposta**: O bot enviará uma mensagem com todos os comandos disponíveis
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Nenhuma

## 📋 Registro e Informações

### `/registro ingressar`
- **Descrição**: Cria seu personagem e ingressa na Academia Tokugawa
- **Uso**: Digite `/registro ingressar` e siga as instruções
- **Resposta**: O bot guiará você pelo processo de criação de personagem
- **Cooldown**: Nenhum (só pode ser usado uma vez por usuário)
- **Permissões Necessárias**: Nenhuma

### `/status status`
- **Descrição**: Exibe seu perfil e estatísticas
- **Uso**: Digite `/status status`
- **Resposta**: O bot mostrará seu nível, experiência, TUSD e atributos
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado

### `/status inventario`
- **Descrição**: Exibe seus itens e técnicas
- **Uso**: Digite `/status inventario`
- **Resposta**: O bot mostrará todos os itens e técnicas que você possui
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado

### `/status top`
- **Descrição**: Exibe o ranking dos melhores alunos
- **Uso**: Digite `/status top`
- **Resposta**: O bot mostrará os jogadores com maior nível e reputação
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Nenhuma

## 🎯 Atividades

### `/atividade treinar`
- **Descrição**: Treina para ganhar experiência e melhorar atributos
- **Uso**: Digite `/atividade treinar`
- **Resposta**: O bot informará quanto de experiência você ganhou e qual atributo melhorou
- **Cooldown**: 1 hora
- **Permissões Necessárias**: Ter um personagem registrado

### `/atividade duelar @usuário [tipo]`
- **Descrição**: Desafia outro aluno para um duelo
- **Uso**: Digite `/atividade duelar @usuário [tipo]`, onde:
  - `@usuário` é a menção ao jogador que você deseja desafiar
  - `[tipo]` é o tipo de duelo (physical, mental, strategic, social)
- **Resposta**: O bot enviará um desafio ao oponente, que precisa aceitar
- **Cooldown**: 30 minutos
- **Permissões Necessárias**: Ter um personagem registrado
- **Observações**: O oponente também precisa ter um personagem registrado

### `/atividade explorar`
- **Descrição**: Explora a academia em busca de eventos aleatórios
- **Uso**: Digite `/atividade explorar`
- **Resposta**: O bot descreverá um evento aleatório e suas consequências
- **Cooldown**: 1 hora
- **Permissões Necessárias**: Ter um personagem registrado

### `/atividade evento`
- **Descrição**: Participa do evento atual
- **Uso**: Digite `/atividade evento`
- **Resposta**: O bot permitirá que você participe do evento atual, se houver um
- **Cooldown**: Varia conforme o evento
- **Permissões Necessárias**: Ter um personagem registrado
- **Observações**: Nem sempre há eventos ativos

## 🏫 Clubes

### `/clube info`
- **Descrição**: Exibe informações sobre seu clube
- **Uso**: Digite `/clube info`
- **Resposta**: O bot mostrará detalhes sobre o clube ao qual você pertence
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado e pertencer a um clube

### `/clube lista`
- **Descrição**: Exibe a lista de todos os clubes
- **Uso**: Digite `/clube lista`
- **Resposta**: O bot mostrará todos os clubes disponíveis na academia
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Nenhuma

## 💰 Economia

### `/economia loja`
- **Descrição**: Acessa a loja da academia
- **Uso**: Digite `/economia loja`
- **Resposta**: O bot mostrará os itens disponíveis para compra
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado

### `/economia comprar <id>`
- **Descrição**: Compra um item da loja
- **Uso**: Digite `/economia comprar <id>`, onde `<id>` é o identificador do item
- **Resposta**: O bot confirmará a compra e adicionará o item ao seu inventário
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado e TUSD suficiente

### `/economia mercado`
- **Descrição**: Acessa o mercado de itens entre jogadores
- **Uso**: Digite `/economia mercado`
- **Resposta**: O bot mostrará os itens disponíveis no mercado
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado

### `/economia vender <id> <preço>`
- **Descrição**: Vende um item no mercado
- **Uso**: Digite `/economia vender <id> <preço>`, onde:
  - `<id>` é o identificador do item no seu inventário
  - `<preço>` é o valor em TUSD que você deseja receber
- **Resposta**: O bot confirmará a listagem do item no mercado
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado e possuir o item

### `/economia comprar_mercado <id>`
- **Descrição**: Compra um item do mercado
- **Uso**: Digite `/economia comprar_mercado <id>`, onde `<id>` é o identificador do item no mercado
- **Resposta**: O bot confirmará a compra e adicionará o item ao seu inventário
- **Cooldown**: Nenhum
- **Permissões Necessárias**: Ter um personagem registrado e TUSD suficiente

### `/economia usar <id>`
- **Descrição**: Usa um item do seu inventário
- **Uso**: Digite `/economia usar <id>`, onde `<id>` é o identificador do item no seu inventário
- **Resposta**: O bot aplicará os efeitos do item
- **Cooldown**: Varia conforme o item
- **Permissões Necessárias**: Ter um personagem registrado e possuir o item

## 💡 Dicas de Uso

- Todos os comandos são slash commands e começam com `/`
- Alguns comandos têm cooldown, então você precisa esperar antes de usá-los novamente
- Os comandos só funcionam em canais de texto onde o bot tem permissão para enviar mensagens
- Para ver informações detalhadas sobre um comando, digite `/` e selecione o comando desejado
- Se um comando não funcionar, verifique se você digitou corretamente e se tem as permissões necessárias

---

Para mais informações sobre como jogar, consulte o guia de [Instruções de Jogo](./Instrucoes_de_Jogo.md).