# Implantação do Bot Academia Tokugawa com Docker

Este guia contém instruções detalhadas para configurar e executar o bot Academia Tokugawa usando contêineres Docker, proporcionando melhor portabilidade e isolamento.

## 🔍 Índice

- [Pré-requisitos](#pré-requisitos)
- [Visão Geral do Docker](#visão-geral-do-docker)
- [Configuração](#configuração)
- [Construção da Imagem](#construção-da-imagem)
- [Execução do Contêiner](#execução-do-contêiner)
- [Gerenciamento do Contêiner](#gerenciamento-do-contêiner)
- [Solução de Problemas](#solução-de-problemas)
- [Boas Práticas](#boas-práticas)

## 📋 Pré-requisitos

Antes de começar, certifique-se de que você tem:

- Docker instalado em sua máquina ([Guia de instalação do Docker](https://docs.docker.com/get-docker/))
- Um token de bot do Discord (obtido no [Portal do Desenvolvedor Discord](https://discord.com/developers/applications/))
- Git (para clonar o repositório, se necessário)

## 🐳 Visão Geral do Docker

Docker é uma plataforma que permite desenvolver, enviar e executar aplicações em contêineres. Usar Docker para o bot Academia Tokugawa oferece várias vantagens:

- **Isolamento**: O bot e suas dependências são isolados do sistema operacional host
- **Portabilidade**: O contêiner pode ser executado em qualquer ambiente que suporte Docker
- **Consistência**: Garante que o bot funcione da mesma forma em diferentes ambientes
- **Facilidade de implantação**: Simplifica o processo de implantação e atualização

## ⚙️ Configuração

### 1. Clone o Repositório (se ainda não o fez)

```bash
git clone https://github.com/seu-usuario/tokugawa-discord-game.git
cd tokugawa-discord-game
```

### 2. Entenda o Dockerfile

O projeto inclui um Dockerfile que define como a imagem Docker será construída. Aqui está uma explicação do Dockerfile:

```dockerfile
# Usa a imagem oficial do Python como base
FROM python:3.9-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia os arquivos de requisitos
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código-fonte
COPY . .

# Comando para executar o bot quando o contêiner iniciar
CMD ["python", "bot.py"]
```

### 3. Configuração das Variáveis de Ambiente

Você pode configurar o bot de duas maneiras:

#### Opção 1: Usando um arquivo .env (recomendado para desenvolvimento)

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```
DISCORD_TOKEN=seu_token_aqui
USE_PRIVILEGED_INTENTS=True
GUILD_ID=seu_id_do_servidor_aqui
```

#### Opção 2: Passando variáveis de ambiente diretamente (recomendado para produção)

As variáveis de ambiente serão passadas diretamente ao executar o contêiner Docker.

## 🏗️ Construção da Imagem

Para construir a imagem Docker do bot:

```bash
docker build -t tokugawa-bot .
```

Este comando cria uma imagem Docker chamada `tokugawa-bot` baseada no Dockerfile no diretório atual.

## ▶️ Execução do Contêiner

### Usando Variáveis de Ambiente

Execute o contêiner passando as variáveis de ambiente necessárias:

```bash
docker run -d --name tokugawa-discord-bot \
  -e DISCORD_TOKEN=seu_token_aqui \
  -e USE_PRIVILEGED_INTENTS=True \
  -e GUILD_ID=seu_id_do_servidor_aqui \
  tokugawa-bot
```

### Usando um Arquivo .env

Se você preferir usar um arquivo `.env`:

```bash
docker run -d --name tokugawa-discord-bot \
  --env-file .env \
  tokugawa-bot
```

### Persistência de Dados

Para persistir os dados do bot entre reinicializações do contêiner, monte um volume:

```bash
docker run -d --name tokugawa-discord-bot \
  -e DISCORD_TOKEN=seu_token_aqui \
  -e USE_PRIVILEGED_INTENTS=True \
  -e GUILD_ID=seu_id_do_servidor_aqui \
  -v $(pwd)/data:/app/data \
  tokugawa-bot
```

Este comando monta o diretório `data` do seu sistema local no diretório `/app/data` dentro do contêiner.

## 🔄 Gerenciamento do Contêiner

### Verificando o Status

Para verificar se o contêiner está em execução:

```bash
docker ps
```

Para ver todos os contêineres, incluindo os parados:

```bash
docker ps -a
```

### Visualizando Logs

Para ver os logs do bot:

```bash
docker logs tokugawa-discord-bot
```

Para acompanhar os logs em tempo real:

```bash
docker logs -f tokugawa-discord-bot
```

### Parando o Contêiner

Para parar o contêiner:

```bash
docker stop tokugawa-discord-bot
```

### Reiniciando o Contêiner

Para reiniciar o contêiner:

```bash
docker restart tokugawa-discord-bot
```

### Removendo o Contêiner

Para remover o contêiner (os dados serão perdidos a menos que você tenha montado um volume):

```bash
docker rm tokugawa-discord-bot
```

## ❓ Solução de Problemas

### Contêiner Não Inicia

- **Problema**: O contêiner não inicia ou para imediatamente após iniciar
- **Solução**: Verifique os logs com `docker logs tokugawa-discord-bot` para identificar o problema

### Erro de Variáveis de Ambiente

- **Problema**: O bot não consegue acessar as variáveis de ambiente
- **Solução**: Verifique se você passou as variáveis de ambiente corretamente ao executar o contêiner

### Problemas de Permissão com Volumes

- **Problema**: Erros de permissão ao acessar arquivos em volumes montados
- **Solução**: Verifique as permissões dos diretórios montados e ajuste-as conforme necessário

### Contêiner Usa Muitos Recursos

- **Problema**: O contêiner está usando muitos recursos do sistema
- **Solução**: Limite os recursos disponíveis para o contêiner:

```bash
docker run -d --name tokugawa-discord-bot \
  -e DISCORD_TOKEN=seu_token_aqui \
  -e USE_PRIVILEGED_INTENTS=True \
  -e GUILD_ID=seu_id_do_servidor_aqui \
  --memory=512m --cpus=0.5 \
  tokugawa-bot
```

## 📝 Boas Práticas

### Segurança

- **Nunca armazene tokens ou credenciais no Dockerfile** ou na imagem Docker
- Use variáveis de ambiente ou arquivos `.env` para configurações sensíveis
- Mantenha o Docker e a imagem base atualizados para evitar vulnerabilidades

### Otimização

- Use a tag `slim` ou `alpine` para imagens base menores
- Implemente o cache de camadas do Docker eficientemente
- Remova arquivos temporários e caches após a instalação de dependências

### Monitoramento

- Configure um sistema de monitoramento para acompanhar a saúde do contêiner
- Implemente reinicialização automática em caso de falha:

```bash
docker run -d --name tokugawa-discord-bot \
  -e DISCORD_TOKEN=seu_token_aqui \
  -e USE_PRIVILEGED_INTENTS=True \
  -e GUILD_ID=seu_id_do_servidor_aqui \
  --restart=unless-stopped \
  tokugawa-bot
```

### Backup

- Faça backup regular dos dados persistentes
- Considere usar volumes Docker nomeados para melhor gerenciamento:

```bash
# Criar um volume nomeado
docker volume create tokugawa-data

# Usar o volume nomeado
docker run -d --name tokugawa-discord-bot \
  -e DISCORD_TOKEN=seu_token_aqui \
  -e USE_PRIVILEGED_INTENTS=True \
  -e GUILD_ID=seu_id_do_servidor_aqui \
  -v tokugawa-data:/app/data \
  tokugawa-bot
```

---

Para outras opções de implantação, consulte:
- [Implantação Local](./Local.md)
- [Implantação no AWS Fargate](./AWS_Fargate.md)