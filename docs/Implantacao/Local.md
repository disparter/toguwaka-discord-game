# Implantação Local do Bot Academia Tokugawa

Este guia contém instruções detalhadas para configurar e executar o bot Academia Tokugawa em um ambiente local.

## 🔍 Índice

- [Pré-requisitos](#pré-requisitos)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Instalação](#instalação)
- [Configuração do Bot](#configuração-do-bot)
- [Execução](#execução)
- [Solução de Problemas](#solução-de-problemas)
- [Manutenção](#manutenção)

## 📋 Pré-requisitos

Antes de começar, certifique-se de que você tem:

- Python 3.8 ou superior instalado
- pip (gerenciador de pacotes Python)
- Um token de bot do Discord (obtido no [Portal do Desenvolvedor Discord](https://discord.com/developers/applications/))
- Git (para clonar o repositório)
- Acesso a um terminal ou prompt de comando

## 🛠️ Configuração do Ambiente

### Verificando a Instalação do Python

Verifique se o Python está instalado corretamente:

```bash
python --version
# ou
python3 --version
```

A versão exibida deve ser 3.8 ou superior. Se o Python não estiver instalado, baixe-o em [python.org](https://www.python.org/downloads/).

### Verificando o pip

Verifique se o pip está instalado:

```bash
pip --version
# ou
pip3 --version
```

Se o pip não estiver instalado, você pode instalá-lo seguindo as instruções em [pip.pypa.io](https://pip.pypa.io/en/stable/installation/).

### Configurando um Ambiente Virtual (Recomendado)

É recomendável usar um ambiente virtual para isolar as dependências do projeto:

```bash
# Criar um ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate
```

## 📥 Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/tokugawa-discord-game.git
cd tokugawa-discord-game
```

### 2. Instale as Dependências

Com o ambiente virtual ativado, instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

## ⚙️ Configuração do Bot

### 1. Crie um Arquivo .env

Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:

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

Substitua `seu_token_aqui` pelo token do seu bot e `seu_id_do_servidor_aqui` pelo ID do seu servidor Discord.

### 2. Configure os Intents Privilegiados

O bot usa intents privilegiados para acessar informações de membros e conteúdo de mensagens. Você precisa habilitá-los no Portal do Desenvolvedor Discord:

1. Acesse o [Portal do Desenvolvedor Discord](https://discord.com/developers/applications/)
2. Selecione sua aplicação/bot
3. Vá para as configurações de "Bot"
4. Ative "SERVER MEMBERS INTENT" e "MESSAGE CONTENT INTENT" na seção "Privileged Gateway Intents"

Alternativamente, defina `USE_PRIVILEGED_INTENTS=False` no arquivo `.env` para executar o bot com funcionalidade limitada.

### 3. Obtenha o ID do Servidor (Guild ID)

Para obter o ID do seu servidor Discord:

1. Ative o "Modo Desenvolvedor" nas configurações do Discord (Configurações > Avançado > Modo Desenvolvedor)
2. Clique com o botão direito no nome do servidor e selecione "Copiar ID"
3. Cole o ID copiado no campo `GUILD_ID` do arquivo `.env`

Se você deixar o campo `GUILD_ID` vazio, os comandos serão registrados globalmente (pode levar até 1 hora para aparecerem).

## ▶️ Execução

### Executando o Bot

Com todas as configurações feitas, execute o bot:

```bash
python bot.py
```

Se tudo estiver configurado corretamente, você verá uma mensagem indicando que o bot está online e conectado ao Discord.

### Usando o Script de Execução

Alternativamente, você pode usar o script `bot_execution.sh` (no Linux/macOS) para executar o bot:

```bash
# Tornar o script executável
chmod +x bot_execution.sh

# Executar o script
./bot_execution.sh
```

### Verificando se o Bot Está Funcionando

Para verificar se o bot está funcionando corretamente:

1. Vá para um canal de texto no servidor Discord onde o bot foi adicionado
2. Digite o comando `/ping`
3. O bot deve responder com "Pong!" e o tempo de resposta

## ❓ Solução de Problemas

### O Bot Não Inicia

- **Problema**: Erro ao iniciar o bot
- **Solução**: Verifique se o token do Discord está correto no arquivo `.env`

### Erro de Módulo Não Encontrado

- **Problema**: `ModuleNotFoundError: No module named 'x'`
- **Solução**: Certifique-se de que todas as dependências foram instaladas corretamente com `pip install -r requirements.txt`

### Erro de Intents Privilegiados

- **Problema**: Erro relacionado a intents privilegiados
- **Solução**: Verifique se você habilitou os intents privilegiados no Portal do Desenvolvedor Discord ou defina `USE_PRIVILEGED_INTENTS=False` no arquivo `.env`

### Comandos Não Aparecem

- **Problema**: Os comandos slash não aparecem no Discord
- **Solução**: 
  - Verifique se o bot tem as permissões necessárias no servidor
  - Se você definiu um GUILD_ID, certifique-se de que está correto
  - Aguarde até 1 hora para comandos globais aparecerem

### Problemas de Permissão

- **Problema**: O bot não responde ou não tem permissão para enviar mensagens
- **Solução**: Verifique se o bot tem as permissões necessárias no servidor e no canal

## 🔄 Manutenção

### Atualizando o Bot

Para atualizar o bot com as últimas alterações do repositório:

```bash
# Navegue até o diretório do projeto
cd caminho/para/tokugawa-discord-game

# Puxe as últimas alterações
git pull

# Atualize as dependências
pip install -r requirements.txt

# Reinicie o bot
python bot.py
```

### Backup de Dados

É recomendável fazer backup regularmente dos dados do bot:

```bash
# Copie os arquivos de dados para um diretório de backup
cp -r data/ backup/data_$(date +%Y%m%d)/
```

### Logs

Os logs do bot são úteis para diagnosticar problemas. Verifique o console onde o bot está sendo executado para ver mensagens de log.

---

Para outras opções de implantação, consulte:
- [Implantação com Docker](./Docker.md)
- [Implantação no AWS Fargate](./AWS_Fargate.md)