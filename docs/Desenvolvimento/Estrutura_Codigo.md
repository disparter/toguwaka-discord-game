# Estrutura de Código do Bot Academia Tokugawa

Este documento descreve a organização do código-fonte do bot Academia Tokugawa, explicando os principais diretórios, arquivos e suas funções.

## 🔍 Índice

- [Visão Geral](#visão-geral)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
  - [Diretório Raiz](#diretório-raiz)
  - [Cogs](#cogs)
  - [Utils](#utils)
  - [Data](#data)
  - [Story Mode](#story-mode)
  - [Tests](#tests)
- [Fluxo de Execução](#fluxo-de-execução)
- [Arquitetura do Bot](#arquitetura-do-bot)

## 📋 Visão Geral

O bot Academia Tokugawa é construído usando Python e a biblioteca discord.py. O código segue uma arquitetura modular, com diferentes componentes organizados em diretórios específicos:

- **bot.py**: Arquivo principal que inicializa o bot e carrega os módulos
- **cogs/**: Módulos de comandos do Discord
- **utils/**: Utilitários e mecânicas de jogo
- **data/**: Armazenamento de dados e configurações
- **story_mode/**: Sistema de modo história
- **tests/**: Testes automatizados

## 📁 Estrutura de Diretórios

### Diretório Raiz

O diretório raiz contém os arquivos principais do projeto:

- **bot.py**: Ponto de entrada principal do bot
- **run_tests.py**: Script para executar testes automatizados
- **requirements.txt**: Lista de dependências do projeto
- **.env**: Arquivo de configuração com variáveis de ambiente (não versionado)
- **Dockerfile**: Configuração para construir a imagem Docker
- **bot_execution.sh**: Script para iniciar o bot

### Cogs

O diretório `cogs/` contém os módulos de comandos do Discord, organizados por funcionalidade:

- **player_status.py**: Comandos relacionados ao status do jogador
- **economy.py**: Sistema econômico (loja, mercado, itens)
- **scheduled_events.py**: Eventos programados e periódicos
- **story_mode.py**: Comandos relacionados ao modo história
- **[outros módulos]**: Outros conjuntos de comandos específicos

Cada arquivo Cog é uma classe que herda de `commands.Cog` da biblioteca discord.py e contém um grupo de comandos relacionados.

### Utils

O diretório `utils/` contém utilitários e implementações de mecânicas de jogo:

- **game_mechanics/**: Implementações das mecânicas principais do jogo
  - **calculators/**: Calculadoras para experiência, dano, etc.
  - **duel/**: Sistema de duelos
  - **events/**: Sistema de eventos aleatórios
- **database/**: Funções para interação com o banco de dados
- **formatters/**: Formatadores de mensagens e embeds
- **validators/**: Validadores de entrada e permissões

### Data

O diretório `data/` armazena dados persistentes e configurações:

- **economy/**: Dados relacionados à economia (itens, preços)
- **events/**: Configurações de eventos
- **schemas/**: Esquemas de dados
- **story_mode/**: Dados do modo história
  - **chapters/**: Capítulos da história
  - **events/**: Eventos específicos da história
  - **narrative_templates/**: Templates de narrativa
  - **npcs/**: Personagens não-jogáveis

### Story Mode

O diretório `story_mode/` contém a implementação do sistema de modo história:

- **chapter_manager.py**: Gerenciador de capítulos
- **narrative_engine.py**: Motor de narrativa
- **choice_processor.py**: Processador de escolhas
- **event_handler.py**: Manipulador de eventos da história
- **[outros módulos]**: Componentes adicionais do modo história

### Tests

O diretório `tests/` contém testes automatizados, seguindo a mesma estrutura do código-fonte:

- **utils/**: Testes para os utilitários
  - **game_mechanics/**: Testes para as mecânicas de jogo
    - **calculators/**: Testes para as calculadoras
    - **duel/**: Testes para o sistema de duelos
    - **events/**: Testes para o sistema de eventos
- **story_mode/**: Testes para o modo história
- **[outros diretórios]**: Testes para outros componentes

## ⚙️ Fluxo de Execução

O fluxo de execução do bot segue estas etapas:

1. **Inicialização**: O arquivo `bot.py` é executado, configurando o bot com base nas variáveis de ambiente
2. **Carregamento de Cogs**: Os módulos Cog são carregados, registrando comandos e eventos
3. **Conexão**: O bot se conecta ao Discord usando o token fornecido
4. **Processamento de Eventos**: O bot processa eventos do Discord (mensagens, reações, etc.)
5. **Execução de Comandos**: Quando um comando é invocado, o Cog correspondente processa a solicitação
6. **Interação com Dados**: Os comandos interagem com o sistema de dados para ler/escrever informações

## 🏗️ Arquitetura do Bot

O bot segue uma arquitetura baseada em componentes:

1. **Interface do Discord**: Gerenciada pela biblioteca discord.py
2. **Camada de Comandos**: Implementada através dos Cogs
3. **Camada de Lógica de Negócios**: Implementada nos módulos utils/game_mechanics
4. **Camada de Dados**: Gerenciada pelos módulos de banco de dados e arquivos JSON

O design segue os princípios SOLID:
- **S**: Cada classe tem uma única responsabilidade
- **O**: As classes são abertas para extensão, mas fechadas para modificação
- **L**: As subclasses podem substituir suas classes base
- **I**: Interfaces específicas são preferíveis a interfaces genéricas
- **D**: Dependências são baseadas em abstrações, não em implementações concretas

---

Para informações sobre como personalizar o bot, consulte o guia de [Personalização](./Personalizacao.md).
Para informações sobre testes, consulte o guia de [Testes](./Testes.md).