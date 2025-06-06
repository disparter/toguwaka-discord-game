# Testes do Bot Academia Tokugawa

Este guia explica como executar e implementar testes para o bot Academia Tokugawa, garantindo a qualidade e o funcionamento correto do código.

## 🔍 Índice

- [Visão Geral dos Testes](#visão-geral-dos-testes)
- [Estrutura de Testes](#estrutura-de-testes)
- [Executando Testes](#executando-testes)
- [Escrevendo Novos Testes](#escrevendo-novos-testes)
- [Melhores Práticas](#melhores-práticas)
- [Integração Contínua](#integração-contínua)

## 📋 Visão Geral dos Testes

O projeto Academia Tokugawa utiliza testes unitários para garantir que cada componente do sistema funcione corretamente de forma isolada. Os testes são escritos usando o framework `unittest` do Python e estão organizados em uma estrutura que espelha a estrutura do código-fonte.

Os testes cobrem diversos aspectos do bot, incluindo:

- Mecânicas de jogo (cálculos, duelos, eventos)
- Comandos e interações com o Discord
- Manipulação de dados e persistência
- Modo história e narrativa
- Integração entre componentes

## 📁 Estrutura de Testes

Os testes estão localizados no diretório `tests/` e seguem a mesma estrutura de diretórios do código-fonte:

```
tests/
├── utils/
│   ├── game_mechanics/
│   │   ├── calculators/
│   │   │   ├── test_experience_calculator.py
│   │   │   └── test_damage_calculator.py
│   │   ├── duel/
│   │   │   └── test_duel_system.py
│   │   └── events/
│   │       └── test_event_system.py
│   └── test_database.py
├── story_mode/
│   ├── test_chapter_manager.py
│   └── test_narrative_engine.py
└── test_new_systems.py
```

Cada arquivo de teste contém uma ou mais classes de teste que herdam de `unittest.TestCase` e implementam métodos de teste para verificar o comportamento esperado dos componentes.

## ⚙️ Executando Testes

### Executando Todos os Testes

Para executar todos os testes do projeto, use o script `run_tests.py` na raiz do projeto:

```bash
python run_tests.py
```

Alternativamente, você pode usar o módulo `unittest` diretamente:

```bash
# Certifique-se de que o diretório raiz do projeto está no PYTHONPATH
PYTHONPATH=$PYTHONPATH:$(pwd) python -m unittest discover -s tests
```

### Executando Testes Específicos

Para executar um teste específico ou um conjunto de testes:

```bash
# Executar um arquivo de teste específico
python run_tests.py tests/utils/game_mechanics/calculators/test_experience_calculator.py

# Executar um método de teste específico
python run_tests.py tests/utils/game_mechanics/calculators/test_experience_calculator.py::TestExperienceCalculator::test_calculate_exp_gain

# Executar todos os testes em um diretório
python run_tests.py tests/utils/game_mechanics
```

Usando o módulo `unittest` diretamente:

```bash
# Executar um arquivo de teste específico
PYTHONPATH=$PYTHONPATH:$(pwd) python -m unittest tests.utils.game_mechanics.calculators.test_experience_calculator

# Executar uma classe de teste específica
PYTHONPATH=$PYTHONPATH:$(pwd) python -m unittest tests.utils.game_mechanics.calculators.test_experience_calculator.TestExperienceCalculator

# Executar um método de teste específico
PYTHONPATH=$PYTHONPATH:$(pwd) python -m unittest tests.utils.game_mechanics.calculators.test_experience_calculator.TestExperienceCalculator.test_calculate_exp_gain
```

## 📝 Escrevendo Novos Testes

Ao adicionar novas funcionalidades ao bot, é importante criar testes correspondentes para garantir que elas funcionem corretamente e continuem funcionando após futuras alterações.

### Criando um Novo Arquivo de Teste

1. Crie um novo arquivo no diretório apropriado dentro de `tests/`
2. Nomeie o arquivo com o prefixo `test_` seguido do nome do módulo que está testando
3. Implemente uma classe de teste que herde de `unittest.TestCase`

Exemplo:

```python
import unittest
from utils.seu_modulo import SuaClasse

class TestSuaClasse(unittest.TestCase):
    def setUp(self):
        """Configuração executada antes de cada teste"""
        self.instancia = SuaClasse()
        
    def tearDown(self):
        """Limpeza executada após cada teste"""
        # Código de limpeza, se necessário
        
    def test_seu_metodo(self):
        """Testa o comportamento do método seu_metodo"""
        # Arrange (Preparação)
        entrada = "valor_de_teste"
        valor_esperado = "resultado_esperado"
        
        # Act (Ação)
        resultado = self.instancia.seu_metodo(entrada)
        
        # Assert (Verificação)
        self.assertEqual(resultado, valor_esperado)
```

### Padrão AAA (Arrange-Act-Assert)

Ao escrever testes, siga o padrão AAA:

1. **Arrange**: Prepare os dados e objetos necessários para o teste
2. **Act**: Execute a ação que está sendo testada
3. **Assert**: Verifique se o resultado é o esperado

### Tipos de Asserções

O módulo `unittest` fornece várias asserções úteis:

- `assertEqual(a, b)`: Verifica se a == b
- `assertNotEqual(a, b)`: Verifica se a != b
- `assertTrue(x)`: Verifica se bool(x) é True
- `assertFalse(x)`: Verifica se bool(x) é False
- `assertIs(a, b)`: Verifica se a é b
- `assertIsNot(a, b)`: Verifica se a não é b
- `assertIsNone(x)`: Verifica se x é None
- `assertIsNotNone(x)`: Verifica se x não é None
- `assertIn(a, b)`: Verifica se a está em b
- `assertNotIn(a, b)`: Verifica se a não está em b
- `assertRaises(exc, fun, *args, **kwds)`: Verifica se fun(*args, **kwds) levanta a exceção exc

## 🔧 Melhores Práticas

### 1. Testes Independentes

Cada teste deve ser independente dos outros. Um teste não deve depender do estado deixado por outro teste.

```python
# Bom: Cada teste configura seu próprio estado
def test_metodo_a(self):
    instancia = MinhaClasse()
    # Teste para o método A
    
def test_metodo_b(self):
    instancia = MinhaClasse()
    # Teste para o método B
```

### 2. Testes Focados

Cada teste deve testar apenas uma funcionalidade específica.

```python
# Bom: Testes focados
def test_calculo_experiencia_nivel_baixo(self):
    # Testa cálculo de experiência para níveis baixos
    
def test_calculo_experiencia_nivel_alto(self):
    # Testa cálculo de experiência para níveis altos
```

### 3. Nomes Descritivos

Use nomes descritivos para seus testes, indicando o que está sendo testado e em quais condições.

```python
# Bom: Nome descritivo
def test_calculo_dano_quando_defensor_tem_resistencia(self):
    # Teste aqui
```

### 4. Mocks e Stubs

Use mocks e stubs para isolar o código que está sendo testado de suas dependências externas.

```python
from unittest.mock import Mock, patch

def test_comando_com_mock(self):
    # Cria um mock para o contexto do Discord
    ctx = Mock()
    ctx.respond = Mock()
    
    # Executa o comando com o mock
    await meu_comando(ctx)
    
    # Verifica se o método respond foi chamado
    ctx.respond.assert_called_once_with("Resposta esperada")
```

### 5. Testes de Borda

Teste casos de borda e valores extremos.

```python
def test_calculo_experiencia_nivel_maximo(self):
    # Testa o cálculo de experiência no nível máximo
    
def test_calculo_experiencia_nivel_zero(self):
    # Testa o cálculo de experiência no nível zero
```

## 🔄 Integração Contínua

O projeto utiliza GitHub Actions para executar testes automaticamente em cada push e pull request. Isso garante que apenas código que passa em todos os testes seja integrado ao branch principal.

### Configuração do GitHub Actions

O arquivo de configuração do GitHub Actions está localizado em `.github/workflows/tests.yml` e define o pipeline de testes:

1. Checkout do código
2. Configuração do ambiente Python
3. Instalação das dependências
4. Execução dos testes
5. Geração de relatório de cobertura (opcional)

### Verificando Resultados

Os resultados dos testes de integração contínua podem ser visualizados na aba "Actions" do repositório no GitHub. Certifique-se de que todos os testes estão passando antes de mesclar suas alterações.

---

Para mais informações sobre a estrutura do código, consulte o guia de [Estrutura de Código](./Estrutura_Codigo.md).
Para informações sobre como personalizar o bot, consulte o guia de [Personalização](./Personalizacao.md).