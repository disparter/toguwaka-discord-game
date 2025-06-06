# Implantação do Bot Academia Tokugawa no AWS Fargate

Este documento contém instruções para configurar e implantar o bot Discord Academia Tokugawa no AWS Fargate.

## 🔍 Índice

- [Pré-requisitos](#pré-requisitos)
- [Publicar a Imagem no Amazon ECR](#1-publicar-a-imagem-no-amazon-ecr)
- [Configurar uma Task Definition no ECS](#2-configurar-uma-task-definition-no-ecs)
- [Criar e Executar um Serviço no AWS Fargate](#3-criar-e-executar-um-serviço-no-aws-fargate)
- [Monitoramento e Atualização](#4-monitoramento-e-atualização)
- [Solução de Problemas](#5-solução-de-problemas)
- [Otimização de Custos](#6-otimização-de-custos)

## 📋 Pré-requisitos

Antes de começar, certifique-se de que você tem:

- Conta AWS com acesso ao ECS, ECR, IAM e CloudWatch
- AWS CLI instalado e configurado
- Docker instalado localmente
- GitHub Actions configurado com segredos necessários (opcional, para CI/CD)

## 1. Publicar a Imagem no Amazon ECR

### Criar um Repositório ECR

```bash
aws ecr create-repository --repository-name tokugawa-discord-bot --region us-east-1
```

### Autenticar o Docker com ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

Substitua `ACCOUNT_ID` pelo seu ID de conta AWS.

### Construir e Enviar a Imagem Manualmente

```bash
docker build -t tokugawa-discord-bot .
docker tag tokugawa-discord-bot:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tokugawa-discord-bot:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tokugawa-discord-bot:latest
```

## 2. Configurar uma Task Definition no ECS

1. Acesse o console AWS e navegue até o ECS
2. Clique em "Task Definitions" e depois em "Create new Task Definition"
3. Selecione "Fargate" como tipo de lançamento
4. Configure a Task Definition:
   - **Nome da Task**: tokugawa-bot-task-definition
   - **Papel de Tarefa**: Crie um novo papel com permissões para ECR e CloudWatch
   - **Modo de Rede**: awsvpc
   - **CPU e Memória**: 0.5 vCPU e 1GB de memória (ajuste conforme necessário)
   - **Adicione um contêiner**:
     - **Nome do contêiner**: tokugawa-bot
     - **Imagem**: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tokugawa-discord-bot:latest
     - **Limites de memória**: Soft limit de 512 MB
     - **Mapeamentos de porta**: Não necessário para bots Discord
     - **Variáveis de ambiente**:
       - DISCORD_TOKEN: <seu-token-discord>
       - USE_PRIVILEGED_INTENTS: True
       - GUILD_ID: <seu-id-guild>
     - **Configurações de log**: Ative o CloudWatch logs

### Exemplo de JSON da Task Definition

```json
{
  "family": "tokugawa-bot-task-definition",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/<TASK_EXECUTION_ROLE>",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/<TASK_ROLE>",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "tokugawa-bot",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tokugawa-discord-bot:latest",
      "memoryReservation": 512,
      "cpu": 256,
      "essential": true,
      "environment": [
        { "name": "DISCORD_TOKEN", "value": "<seu-token-discord>" },
        { "name": "USE_PRIVILEGED_INTENTS", "value": "True" },
        { "name": "GUILD_ID", "value": "<seu-id-guild>" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/tokugawa-bot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "cpu": "512",
  "memory": "1024",
  "requiresCompatibilities": ["FARGATE"]
}
```

## 3. Criar e Executar um Serviço no AWS Fargate

### Criar um Cluster ECS

1. No console ECS, crie um novo cluster:
   - **Nome do cluster**: tokugawa-bot-cluster
   - **Rede VPC**: Selecione sua VPC
   - **Subnets**: Selecione pelo menos duas subnets públicas

### Criar um Serviço ECS

1. Dentro do cluster, crie um novo serviço:
   - **Tipo de lançamento**: Fargate
   - **Sistema operacional/Arquitetura**: Linux/X86_64
   - **Task Definition**: tokugawa-bot-task-definition
   - **Revisão**: Selecione a revisão mais recente
   - **Nome do serviço**: tokugawa-bot-service
   - **Número de tarefas desejadas**: 1
   - **Tipo de implantação**: Rolling update
   - **Configurações de rede**:
     - **VPC**: Selecione sua VPC
     - **Subnets**: Selecione pelo menos duas subnets públicas
     - **Grupos de segurança**: Crie um novo grupo de segurança sem regras de entrada (o bot não precisa receber tráfego)
     - **IP público**: ENABLED (para permitir que o bot se conecte à API do Discord)
   - **Balanceador de carga**: Nenhum (não necessário para bots Discord)
   - **Escalabilidade automática**: Desativada (opcional)

## 4. Monitoramento e Atualização

### Monitorar o Cluster

1. No console ECS, acesse seu cluster e serviço para verificar o status das tarefas
2. Verifique os logs no CloudWatch:
   - Navegue até CloudWatch > Logs > Log Groups
   - Encontre o grupo de logs associado à sua task definition (geralmente /ecs/tokugawa-bot)

### Atualizar o Bot

Para atualizações manuais:
1. Faça alterações no código
2. Envie as alterações para o GitHub
3. O GitHub Actions automaticamente construirá e implantará a nova versão (se configurado)

Para forçar uma nova implantação manualmente:
```bash
aws ecs update-service --cluster tokugawa-bot-cluster --service tokugawa-bot-service --force-new-deployment
```

## 5. Solução de Problemas

### Bot não inicia

- **Problema**: A tarefa não inicia ou falha rapidamente
- **Solução**: Verifique os logs no CloudWatch para identificar erros

### Problemas de conexão

- **Problema**: O bot não consegue se conectar ao Discord
- **Solução**: Certifique-se de que a tarefa tem acesso à internet (IP público habilitado)

### Erros de permissão

- **Problema**: Erros relacionados a permissões AWS
- **Solução**: Verifique se o papel de tarefa tem permissões adequadas

### Falhas de implantação

- **Problema**: Falhas ao implantar novas versões
- **Solução**: Verifique os eventos do serviço no console ECS

## 6. Otimização de Custos

### Estratégias para Reduzir Custos

- Configure a escalabilidade automática baseada em programação para desligar o bot durante períodos de inatividade
- Use Savings Plans ou Reserved Instances para reduzir custos de longo prazo
- Monitore o uso de recursos e ajuste a CPU/memória conforme necessário
- Considere usar Spot Instances para ambientes de desenvolvimento/teste

### Monitoramento de Custos

- Configure alertas de orçamento no AWS Budgets
- Use o AWS Cost Explorer para analisar gastos
- Implemente tags para rastrear custos por projeto ou ambiente

---

Para outras opções de implantação, consulte:
- [Implantação Local](./Local.md)
- [Implantação com Docker](./Docker.md)