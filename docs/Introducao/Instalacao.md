# Instalação do Bot Academia Tokugawa

Este guia contém instruções detalhadas para configurar o bot Academia Tokugawa em diferentes ambientes.

## 📋 Pré-requisitos

Antes de começar, certifique-se de que você tem:

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Um token de bot do Discord
- Git (para clonar o repositório)

## 🔄 Opções de Implantação

Você pode executar o bot de três maneiras diferentes:

1. [Instalação Local](#instalação-local) - Configuração tradicional em sua máquina local
2. [Contêiner Docker](#contêiner-docker) - Execução em contêiner para melhor portabilidade
3. [AWS Fargate](#aws-fargate) - Hospedagem na nuvem para disponibilidade contínua

Escolha a opção que melhor atende às suas necessidades.

## 💻 Instalação Local

Siga estas etapas para configurar o bot em sua máquina local:

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/tokugawa-discord-game.git
cd tokugawa-discord-game
```

### 2. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o Arquivo .env

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```
# Discord Bot Token
DISCORD_TOKEN=seu_token_aqui

# Configuração de Intents Privilegiados
# Defina como False se não quiser habilitar intents privilegiados no Portal do Desenvolvedor Discord
# Nota: Alguns recursos serão limitados se definido como False
USE_PRIVILEGED_INTENTS=True

# ID do Servidor (Guild ID) para registro de comandos
# Substitua pelo ID do seu servidor Discord para registrar comandos diretamente nele
# Isso faz com que os comandos apareçam instantaneamente no servidor especificado
GUILD_ID=seu_id_do_servidor_aqui
```

### 4. Configure os Intents Privilegiados

O bot usa intents privilegiados para acessar informações de membros e conteúdo de mensagens. Você precisa habilitá-los no [Portal do Desenvolvedor Discord](https://discord.com/developers/applications/):

1. Acesse o portal e selecione seu aplicativo/bot
2. Vá para as configurações de "Bot"
3. Ative "SERVER MEMBERS INTENT" e "MESSAGE CONTENT INTENT" na seção "Privileged Gateway Intents"

Alternativamente, defina `USE_PRIVILEGED_INTENTS=False` no arquivo `.env` para executar o bot com funcionalidade limitada.

### 5. Configure o ID do Servidor (Guild ID)

Configurar o GUILD_ID permite que os comandos do bot sejam registrados diretamente em um servidor específico, fazendo com que apareçam instantaneamente:

1. Ative o "Modo Desenvolvedor" nas configurações do Discord (Configurações > Avançado > Modo Desenvolvedor)
2. Clique com o botão direito no nome do servidor e selecione "Copiar ID"
3. Cole o ID copiado no campo `GUILD_ID` do arquivo `.env`

Se você deixar o campo `GUILD_ID` vazio, os comandos serão registrados globalmente (pode levar até 1 hora para aparecerem).

### 6. Execute o Bot

```bash
python bot.py
```

## 🐳 Contêiner Docker

Para executar o bot em um contêiner Docker, siga estas etapas:

### 1. Certifique-se de ter o Docker Instalado

Verifique se o Docker está instalado em sua máquina:

```bash
docker --version
```

Se não estiver instalado, [baixe e instale o Docker](https://www.docker.com/get-started).

### 2. Clone o Repositório (se ainda não o fez)

```bash
git clone https://github.com/seu-usuario/tokugawa-discord-game.git
cd tokugawa-discord-game
```

### 3. Construa a Imagem Docker

```bash
docker build -t tokugawa-bot .
```

### 4. Execute o Contêiner

```bash
docker run -d --name tokugawa-discord-bot \
  -e DISCORD_TOKEN=seu_token_aqui \
  -e USE_PRIVILEGED_INTENTS=True \
  -e GUILD_ID=seu_id_do_servidor_aqui \
  tokugawa-bot
```

Substitua `seu_token_aqui` e `seu_id_do_servidor_aqui` pelos valores apropriados.

### 5. Verifique o Status do Contêiner

```bash
docker ps
```

Para ver os logs do contêiner:

```bash
docker logs tokugawa-discord-bot
```

## ☁️ AWS Fargate

Para implantação no AWS Fargate, consulte o guia detalhado [AWS Fargate](../Implantacao/AWS_Fargate.md).

## 🔗 Adicionando o Bot ao Discord

Depois de configurar o bot, você precisa adicioná-lo ao seu servidor Discord:

### 1. Crie uma Aplicação no Portal do Desenvolvedor

1. Acesse o [Portal do Desenvolvedor Discord](https://discord.com/developers/applications/)
2. Clique em "New Application" e dê um nome para sua aplicação
3. Vá para a seção "Bot" e clique em "Add Bot"
4. Copie o token do bot e adicione-o ao seu arquivo `.env`

### 2. Configure as Permissões e Gere o Link de Convite

1. Na seção "OAuth2" > "URL Generator", selecione os seguintes escopos:
   - `bot`
   - `applications.commands`
2. Nas permissões do bot, selecione:
   - "Send Messages"
   - "Embed Links"
   - "Read Message History"
   - "Add Reactions"
   - "Use Slash Commands"
   - "Read Messages/View Channels"
3. Copie o URL gerado

### 3. Convide o Bot para seu Servidor

1. Abra o URL gerado em seu navegador
2. Selecione o servidor onde deseja adicionar o bot
3. Confirme as permissões e complete o processo de autorização
4. O bot aparecerá na lista de membros do servidor

## ❓ Solução de Problemas

### O Bot Não Inicia

- Verifique se todas as dependências foram instaladas corretamente
- Certifique-se de que o token do Discord está correto no arquivo `.env`
- Verifique se o Python está na versão 3.8 ou superior

### Comandos Não Aparecem

- Verifique se o bot tem as permissões necessárias no servidor
- Se você definiu um GUILD_ID, certifique-se de que está correto
- Aguarde até 1 hora para comandos globais aparecerem

### Erro de Intents Privilegiados

- Verifique se você habilitou os intents privilegiados no Portal do Desenvolvedor Discord
- Ou defina `USE_PRIVILEGED_INTENTS=False` no arquivo `.env` para executar com funcionalidade limitada

### Problemas com Docker

- Verifique se o Docker está em execução
- Certifique-se de que a porta não está sendo usada por outro contêiner
- Verifique os logs do contêiner para identificar erros

---

Após a instalação, consulte as [Instruções de Jogo](../Guias_de_Jogo/Instrucoes_de_Jogo.md) para começar a jogar.