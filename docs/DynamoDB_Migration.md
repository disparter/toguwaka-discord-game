# Migração para Amazon DynamoDB

Este documento descreve a migração do banco de dados SQLite para o Amazon DynamoDB no projeto Academia Tokugawa.

## Visão Geral

A migração para o DynamoDB permite maior escalabilidade, flexibilidade e desempenho para o jogo. Em vez de usar múltiplas tabelas como no modelo anterior, agora usamos uma única tabela com um esquema flexível, seguindo as melhores práticas para DynamoDB.

## Estrutura da Tabela

A tabela principal `AcademiaTokugawa` usa o seguinte esquema:

- **Chave de Partição (PK)**: Identifica o tipo e ID do item (ex: `PLAYER#12345`, `CLUBE#1`, `EVENTO#abc123`)
- **Chave de Ordenação (SK)**: Categoriza os dados dentro de uma partição (ex: `PROFILE`, `INVENTORY`, `MEMBROS`)
- **Índice Secundário Global (GSI1)**: Permite consultas por tipo de entidade usando GSI1PK e GSI1SK

### Exemplos de Estrutura de Dados

#### Perfil de Jogador
```json
{
  "PK": "PLAYER#12345",
  "SK": "PROFILE",
  "GSI1PK": "PLAYERS",
  "GSI1SK": "Shiro",
  "nome": "Shiro",
  "superpoder": "Ilusão Mental",
  "nivel": 5,
  "atributos": {
    "destreza": 3,
    "intelecto": 5,
    "carisma": 4,
    "poder": 4
  }
}
```

#### Inventário de Jogador
```json
{
  "PK": "PLAYER#12345",
  "SK": "INVENTORY",
  "itens": [
    { "id": "POTION_01", "quantidade": 3 },
    { "id": "ARMOR_02", "quantidade": 1 }
  ]
}
```

#### Clube
```json
{
  "PK": "CLUBE#1",
  "SK": "PROFILE",
  "GSI1PK": "CLUBES",
  "GSI1SK": "Clube das Chamas",
  "nome": "Clube das Chamas",
  "descricao": "Mestres do fogo e das artes marciais explosivas.",
  "lider_id": 54321,
  "membros_count": 10,
  "reputacao": 100
}
```

#### Membros do Clube
```json
{
  "PK": "CLUBE#1",
  "SK": "MEMBROS",
  "membros": [
    "PLAYER#12345",
    "PLAYER#54321"
  ]
}
```

## Arquivos Criados/Modificados

1. **deployment_tools/dynamodb_cli.sh**: Script atualizado para criar a tabela única do DynamoDB
2. **utils/dynamodb.py**: Nova implementação do banco de dados usando DynamoDB
3. **utils/db.py**: Camada de compatibilidade que permite alternar entre SQLite e DynamoDB
4. **utils/migrate_to_dynamodb.py**: Script para migrar dados do SQLite para o DynamoDB
5. **.env**: Atualizado com configurações para DynamoDB

## Como Usar

### Configuração

Edite o arquivo `.env` para configurar o DynamoDB:

```
# DynamoDB Configuration
USE_DYNAMODB=true
DYNAMODB_TABLE=AcademiaTokugawa
AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Criação da Tabela

Execute o script `dynamodb_cli.sh` para criar a tabela no DynamoDB:

```bash
cd deployment_tools
./dynamodb_cli.sh
# Selecione a opção 1 para criar a tabela única
```

### Migração de Dados

Para migrar dados do SQLite para o DynamoDB:

```bash
python -m utils.migrate_to_dynamodb
```

### Uso no Código

Não é necessário alterar o código existente. A camada de compatibilidade `utils/db.py` detecta automaticamente qual implementação usar com base na configuração `USE_DYNAMODB` no arquivo `.env`.

Para importar funções do banco de dados, use:

```python
from utils.db import get_player, update_player, get_club, ...
```

## Vantagens da Migração

1. **Escalabilidade**: O DynamoDB é altamente escalável, permitindo que o jogo suporte um grande volume de jogadores e eventos simultaneamente.
2. **Flexibilidade no Esquema**: A estrutura de chave composta (PK/SK) permite armazenar diferentes tipos de dados sem precisar ajustar constantemente a estrutura das tabelas.
3. **Baixa Latência**: Oferece latência em milissegundos para leitura e gravação, garantindo respostas rápidas no jogo.
4. **Eventos Reais/Escala Global**: Ideal para armazenar e consultar dados de eventos coletivos.
5. **Custos**: O DynamoDB é pago conforme o uso, e geralmente é mais econômico com configuração adequada.

## Solução de Problemas

- **Erro de Conexão**: Verifique se as credenciais AWS estão configuradas corretamente.
- **Tabela Não Encontrada**: Certifique-se de que a tabela foi criada usando o script `dynamodb_cli.sh`.
- **Erros de Permissão**: Verifique se o usuário AWS tem permissões para acessar o DynamoDB.