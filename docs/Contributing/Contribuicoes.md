# Contribuindo para o Bot Academia Tokugawa

Este guia contém diretrizes para contribuir com o desenvolvimento do bot Academia Tokugawa. Agradecemos seu interesse em ajudar a melhorar o projeto!

## 🔍 Índice

- [Código de Conduta](#código-de-conduta)
- [Como Contribuir](#como-contribuir)
  - [Reportando Bugs](#reportando-bugs)
  - [Sugerindo Melhorias](#sugerindo-melhorias)
  - [Contribuindo com Código](#contribuindo-com-código)
- [Processo de Pull Request](#processo-de-pull-request)
- [Padrões de Código](#padrões-de-código)
- [Testes](#testes)
- [Documentação](#documentação)
- [Versionamento](#versionamento)

## 📝 Código de Conduta

Ao participar deste projeto, você concorda em manter um ambiente respeitoso e colaborativo. Esperamos que todos os contribuidores:

- Usem linguagem acolhedora e inclusiva
- Respeitem diferentes pontos de vista e experiências
- Aceitem críticas construtivas com elegância
- Foquem no que é melhor para a comunidade
- Demonstrem empatia com outros membros da comunidade

## 🤝 Como Contribuir

### Reportando Bugs

Bugs são rastreados como issues no GitHub. Ao reportar um bug, por favor inclua:

1. **Título claro e descritivo** do problema
2. **Passos detalhados para reproduzir** o bug
3. **Comportamento esperado** vs. **comportamento observado**
4. **Capturas de tela** se aplicável
5. **Informações do ambiente** (sistema operacional, versão do Python, etc.)

Use o template de issue para bugs, se disponível.

### Sugerindo Melhorias

Sugestões de melhorias também são rastreadas como issues. Ao sugerir uma melhoria:

1. **Use um título claro e descritivo**
2. **Forneça uma descrição detalhada** da melhoria sugerida
3. **Explique por que** esta melhoria seria útil para o projeto
4. **Inclua exemplos** de como a melhoria funcionaria, se possível

Use o template de issue para sugestões de recursos, se disponível.

### Contribuindo com Código

1. **Fork o repositório** para sua conta GitHub
2. **Clone seu fork** para sua máquina local
3. **Crie uma branch** para sua contribuição:
   ```bash
   git checkout -b feature/nome-da-sua-feature
   ```
   ou
   ```bash
   git checkout -b fix/nome-do-seu-fix
   ```
4. **Faça suas alterações** seguindo os padrões de código do projeto
5. **Escreva testes** para suas alterações
6. **Atualize a documentação** conforme necessário
7. **Commit suas alterações** com mensagens claras e descritivas:
   ```bash
   git commit -am 'Adiciona nova funcionalidade: descrição concisa'
   ```
8. **Push para sua branch**:
   ```bash
   git push origin feature/nome-da-sua-feature
   ```
9. **Abra um Pull Request** para a branch principal do projeto

## 📥 Processo de Pull Request

1. Certifique-se de que sua branch está atualizada com a branch principal:
   ```bash
   git fetch upstream
   git merge upstream/main
   ```
2. Resolva quaisquer conflitos de merge
3. Certifique-se de que todos os testes passam
4. Preencha o template de Pull Request com todas as informações necessárias
5. Aguarde a revisão de código
6. Faça as alterações solicitadas, se houver
7. Quando aprovado, seu Pull Request será mesclado

## 💻 Padrões de Código

### Estilo de Código

- Siga o [PEP 8](https://www.python.org/dev/peps/pep-0008/) para código Python
- Use 4 espaços para indentação (não tabs)
- Limite as linhas a 88 caracteres (compatível com Black)
- Use nomes descritivos para variáveis, funções e classes
- Documente todas as funções, métodos e classes com docstrings

### Formatação

Recomendamos o uso do formatador [Black](https://black.readthedocs.io/) para manter a consistência do código:

```bash
# Instalar Black
pip install black

# Formatar um arquivo
black caminho/para/arquivo.py

# Formatar todo o projeto
black .
```

### Linting

Use [Flake8](https://flake8.pycqa.org/) para verificar problemas de estilo e potenciais erros:

```bash
# Instalar Flake8
pip install flake8

# Verificar um arquivo
flake8 caminho/para/arquivo.py

# Verificar todo o projeto
flake8 .
```

## 🧪 Testes

Todos os novos recursos e correções de bugs devem incluir testes. Nosso projeto usa o framework `unittest` do Python.

### Escrevendo Testes

1. Crie um arquivo de teste no diretório apropriado dentro de `tests/`
2. Nomeie o arquivo com o prefixo `test_` seguido do nome do módulo que está testando
3. Implemente uma classe de teste que herde de `unittest.TestCase`
4. Escreva métodos de teste que comecem com `test_`

Para mais detalhes sobre como escrever testes, consulte o [guia de testes](./Desenvolvimento/Testes.md).

### Executando Testes

Para executar todos os testes:

```bash
python run_tests.py
```

Para executar um teste específico:

```bash
python run_tests.py tests/caminho/para/test_arquivo.py
```

## 📚 Documentação

A documentação é uma parte crucial do projeto. Ao contribuir:

1. Atualize a documentação relevante para refletir suas alterações
2. Use linguagem clara e concisa
3. Inclua exemplos quando apropriado
4. Verifique se os links internos funcionam corretamente
5. Mantenha a formatação consistente com o resto da documentação

## 🔢 Versionamento

Este projeto segue o [Versionamento Semântico](https://semver.org/):

- **MAJOR.MINOR.PATCH** (ex.: 1.2.3)
- **MAJOR**: alterações incompatíveis com versões anteriores
- **MINOR**: adições de funcionalidades compatíveis com versões anteriores
- **PATCH**: correções de bugs compatíveis com versões anteriores

### Mensagens de Commit

Siga o padrão de [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé(s) opcional(is)]
```

Tipos comuns:
- **feat**: nova funcionalidade
- **fix**: correção de bug
- **docs**: alterações na documentação
- **style**: alterações que não afetam o código (formatação, etc.)
- **refactor**: refatoração de código
- **test**: adição ou correção de testes
- **chore**: alterações em ferramentas de build, etc.

Exemplo:
```
feat(economia): adiciona sistema de leilões

Implementa um sistema de leilões onde jogadores podem oferecer itens
para outros jogadores licitarem.

Closes #123
```

## 🙏 Agradecimentos

Agradecemos a todos os contribuidores que ajudam a melhorar o bot Academia Tokugawa. Seu tempo e esforço são muito apreciados!

---

Para mais informações sobre o projeto, consulte:
- [Introdução ao Projeto](./Introducao/Objetivo.md)
- [Guia de Desenvolvimento](./Desenvolvimento/Estrutura_Codigo.md)