# Correção de Permissões do CloudWatch

## Problema Corrigido

O seguinte erro foi corrigido:
```
2025-06-05 15:56:47,353 - tokugawa_bot - ERROR - Failed to set up CloudWatch logging: An error occurred (AccessDeniedException) when calling the CreateLogGroup operation: User: arn:aws:sts::959903454321:assumed-role/S3AccessRoleForTokugawa/2a10d5786ae4496a94d2cde601b41381 is not authorized to perform: logs:CreateLogGroup on resource: arn:aws:logs:us-east-1:959903454321:log-group:/ecs/tokugawa-bot:log-stream: because no identity-based policy allows the logs:CreateLogGroup action
```

## Alterações Realizadas

1. **Atualização da Política IAM**:
   - Modificado `s3-access-policy.json` para incluir permissões do CloudWatch logs
   - Adicionadas as seguintes permissões:
     - `logs:CreateLogGroup`
     - `logs:CreateLogStream`
     - `logs:PutLogEvents`
   - Estas permissões permitem que o bot crie e escreva em logs do CloudWatch

## Por Que Isso Corrige o Problema

O erro ocorreu porque o papel IAM `S3AccessRoleForTokugawa` não tinha permissão para criar um grupo de logs do CloudWatch. O bot tenta configurar o logging do CloudWatch quando executado na AWS (detectado pela presença da variável de ambiente `AWS_EXECUTION_ENV`).

No arquivo `bot.py`, o código tenta criar um grupo de logs do CloudWatch chamado `/ecs/tokugawa-bot` e um fluxo de logs chamado `discord-bot-logs`. No entanto, o papel IAM só tinha permissões para operações do S3, não para operações de logs do CloudWatch.

Ao adicionar as permissões necessárias de logs do CloudWatch à política IAM, o bot agora pode criar o grupo de logs e o fluxo, e escrever logs no CloudWatch.

## Detalhes da Implementação

A configuração do CloudWatch logging em `bot.py` (linhas 14-39) permanece inalterada. A única alteração foi na política IAM para conceder as permissões necessárias.

## Instruções de Implantação

Após confirmar estas alterações, a política IAM atualizada precisa ser aplicada ao papel `S3AccessRoleForTokugawa` na AWS. Isso pode ser feito usando a AWS CLI ou o Console de Gerenciamento da AWS:

```bash
aws iam put-role-policy \
  --role-name S3AccessRoleForTokugawa \
  --policy-name S3AccessPolicy \
  --policy-document file://s3-access-policy.json
```

## Testes

Uma vez que a política atualizada seja aplicada, o bot deve ser capaz de criar grupos e fluxos de logs do CloudWatch, e o erro não deve mais ocorrer. Os logs estarão disponíveis no console do CloudWatch sob o grupo de logs `/ecs/tokugawa-bot`.