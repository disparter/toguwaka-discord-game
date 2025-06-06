# Personalização do Bot Academia Tokugawa

Este guia explica como personalizar e estender o bot Academia Tokugawa, adicionando novos comandos, funcionalidades ou modificando comportamentos existentes.

## 🔍 Índice

- [Adicionando Novos Comandos](#adicionando-novos-comandos)
- [Criando Novos Eventos](#criando-novos-eventos)
- [Adicionando Itens ao Jogo](#adicionando-itens-ao-jogo)
- [Criando Novos Clubes](#criando-novos-clubes)
- [Expandindo o Modo História](#expandindo-o-modo-história)
- [Modificando Mecânicas de Jogo](#modificando-mecânicas-de-jogo)
- [Boas Práticas](#boas-práticas)

## 🔧 Adicionando Novos Comandos

Para adicionar novos comandos ao bot, você precisa criar ou modificar um Cog. Os Cogs são módulos que agrupam comandos relacionados.

### Criando um Novo Cog

1. Crie um novo arquivo Python no diretório `cogs/`, por exemplo `meu_modulo.py`
2. Implemente a classe do Cog seguindo este modelo:

```python
import discord
from discord.ext import commands

class MeuModulo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="meu_comando", description="Descrição do meu comando")
    async def meu_comando(self, ctx):
        """Implementação do comando"""
        await ctx.respond("Olá! Este é meu novo comando!")

    # Mais comandos aqui...

def setup(bot):
    bot.add_cog(MeuModulo(bot))
```

3. Registre o Cog no arquivo `bot.py`, adicionando-o à lista de extensões:

```python
# No arquivo bot.py
initial_extensions = [
    # Outros cogs...
    'cogs.meu_modulo'
]
```

### Adicionando Comandos a um Cog Existente

1. Abra o arquivo do Cog existente em `cogs/`
2. Adicione seu novo comando como um método da classe:

```python
@commands.slash_command(name="novo_comando", description="Descrição do novo comando")
async def novo_comando(self, ctx, parametro: str = None):
    """Implementação do comando"""
    if parametro:
        await ctx.respond(f"Você forneceu o parâmetro: {parametro}")
    else:
        await ctx.respond("Comando executado sem parâmetros!")
```

### Parâmetros de Comandos

Você pode adicionar parâmetros aos seus comandos:

```python
@commands.slash_command(name="comando_parametros")
async def comando_parametros(
    self, 
    ctx, 
    texto: discord.Option(str, "Um texto qualquer", required=True),
    numero: discord.Option(int, "Um número", required=False, default=0),
    opcao: discord.Option(str, "Escolha uma opção", choices=["A", "B", "C"])
):
    await ctx.respond(f"Texto: {texto}, Número: {numero}, Opção: {opcao}")
```

## 🎲 Criando Novos Eventos

Os eventos são ocorrências aleatórias que podem acontecer durante a exploração ou em momentos específicos do jogo.

### Adicionando um Evento de Exploração

1. Abra o arquivo de eventos em `utils/game_mechanics/events/exploration_events.py`
2. Adicione seu novo evento ao dicionário de eventos:

```python
EXPLORATION_EVENTS = {
    # Eventos existentes...

    "meu_novo_evento": {
        "title": "Título do Evento",
        "description": "Descrição detalhada do que acontece neste evento.",
        "options": [
            {
                "text": "Opção 1",
                "result": "Resultado da opção 1",
                "effects": {
                    "tusd": 50,  # Ganho de TUSD
                    "exp": 20,   # Ganho de experiência
                    "attributes": {"power": 1}  # Aumento de atributo
                }
            },
            {
                "text": "Opção 2",
                "result": "Resultado da opção 2",
                "effects": {
                    "tusd": -20,  # Perda de TUSD
                    "exp": 30,    # Ganho de experiência
                    "item": "item_raro"  # Ganho de item
                }
            }
        ],
        "requirements": {
            "min_level": 5,  # Nível mínimo para o evento aparecer
            "club": "Clube das Chamas"  # Clube específico (opcional)
        },
        "weight": 10  # Peso para a probabilidade de ocorrência
    }
}
```

### Criando um Evento Programado

Para eventos que ocorrem em horários específicos:

1. Abra o arquivo `cogs/scheduled_events.py`
2. Adicione uma nova tarefa programada:

```python
@tasks.loop(hours=24)  # Executa a cada 24 horas
async def meu_evento_diario(self):
    """Implementação do evento diário"""
    # Lógica do evento aqui
    channel = self.bot.get_channel(CHANNEL_ID)
    await channel.send("Anunciando meu evento diário!")

    # Iniciar o evento
    # ...
```

3. Certifique-se de iniciar a tarefa no método `cog_load`:

```python
def cog_load(self):
    # Outras inicializações...
    self.meu_evento_diario.start()
```

## 🎁 Adicionando Itens ao Jogo

Para adicionar novos itens à loja ou ao sistema de recompensas:

1. Abra o arquivo de itens em `data/economy/items.json` (ou crie-o se não existir)
2. Adicione a definição do seu novo item:

```json
{
  "items": [
    {
      "id": "meu_novo_item",
      "name": "Nome do Item",
      "description": "Descrição detalhada do item",
      "price": 500,
      "type": "consumable",
      "effects": {
        "temporary": {
          "attributes": {"power": 2, "dexterity": 1},
          "duration": 3600
        },
        "permanent": {
          "attributes": {"charisma": 1}
        }
      },
      "rarity": "rare",
      "usable": true,
      "tradeable": true
    }
  ]
}
```

Observações:
- `type` pode ser: consumable, equipment, accessory
- `rarity` pode ser: common, uncommon, rare, epic, legendary
- `duration` é em segundos

3. Se necessário, adicione lógica específica para o item no arquivo `cogs/economy.py` no método `usar_item`.

## 🏫 Criando Novos Clubes

Para adicionar um novo clube ao jogo:

1. Abra o arquivo de clubes em `data/clubs.json` (ou crie-o se não existir)
2. Adicione a definição do seu novo clube:

```json
{
  "clubs": [
    {
      "id": "meu_novo_clube",
      "name": "Nome do Clube",
      "description": "Descrição detalhada do clube",
      "specialty": "Especialidade do clube",
      "attribute_bonus": {
        "power": 2,
        "intellect": 1
      },
      "exclusive_techniques": ["tecnica_1", "tecnica_2"],
      "requirements": {
        "min_level": 5
      }
    }
  ]
}
```

Observação: Este exemplo mostra apenas o novo clube. Na prática, você adicionaria este objeto à lista de clubes existentes.

3. Atualize a lógica de seleção de clubes no arquivo `cogs/player_status.py` se necessário.

## 📚 Expandindo o Modo História

Para adicionar novos capítulos ou eventos ao modo história:

### Adicionando um Novo Capítulo

1. Crie um novo arquivo JSON no diretório `data/story_mode/chapters/`, por exemplo `capitulo_6.json`
2. Defina a estrutura do capítulo:

```json
{
  "chapter_id": "capitulo_6",
  "title": "Título do Capítulo",
  "description": "Descrição introdutória do capítulo",
  "scenes": [
    {
      "scene_id": "cena_1",
      "narrative": "Texto narrativo da cena...",
      "choices": [
        {
          "text": "Opção 1",
          "next_scene": "cena_2",
          "requirements": {
            "attributes": {"intellect": 3}
          }
        },
        {
          "text": "Opção 2",
          "next_scene": "cena_3"
        }
      ]
    }
  ],
  "rewards": {
    "exp": 100,
    "tusd": 200,
    "items": ["item_especial"]
  },
  "requirements": {
    "previous_chapters": ["capitulo_5"],
    "min_level": 10
  }
}
```

Observação: Este é um exemplo simplificado. Na prática, você adicionaria mais cenas ao capítulo.

3. Registre o novo capítulo no gerenciador de capítulos em `story_mode/chapter_manager.py`.

## ⚙️ Modificando Mecânicas de Jogo

Para modificar mecânicas existentes, como cálculos de dano, experiência ou economia:

### Alterando Cálculos de Experiência

1. Abra o arquivo `utils/game_mechanics/calculators/experience_calculator.py`
2. Modifique a fórmula de cálculo de experiência:

```python
def calculate_exp_gain(player_level, activity_type):
    """Calcula o ganho de experiência baseado no nível do jogador e tipo de atividade"""
    base_exp = 10

    # Fator de nível
    level_factor = 1 + (player_level * 0.1)

    # Fator de atividade
    activity_factors = {
        "training": 1.0,
        "duel_win": 2.0,
        "duel_lose": 0.5,
        "exploration": 1.2,
        "event": 1.5
    }

    # Sua modificação aqui
    activity_factor = activity_factors.get(activity_type, 1.0)

    # Cálculo final
    exp_gain = int(base_exp * level_factor * activity_factor)

    return exp_gain
```

### Alterando o Sistema de Duelos

1. Abra o arquivo `utils/game_mechanics/duel/duel_system.py`
2. Modifique a lógica de cálculo de resultado de duelos:

```python
def calculate_duel_result(attacker, defender, duel_type):
    """Calcula o resultado de um duelo entre dois jogadores"""
    # Sua modificação aqui
    # ...
```

## 📝 Boas Práticas

Ao personalizar o bot, siga estas boas práticas:

1. **Mantenha a Consistência**: Siga o estilo de código existente
2. **Documente seu Código**: Adicione docstrings e comentários explicativos
3. **Escreva Testes**: Crie testes para suas novas funcionalidades
4. **Evite Duplicação**: Reutilize código existente quando possível
5. **Considere a Performance**: Evite operações pesadas em comandos síncronos
6. **Trate Erros**: Implemente tratamento de exceções adequado
7. **Mantenha a Compatibilidade**: Evite quebrar funcionalidades existentes
8. **Atualize a Documentação**: Documente suas alterações neste guia

---

Para mais informações sobre a estrutura do código, consulte o guia de [Estrutura de Código](./Estrutura_Codigo.md).
Para informações sobre testes, consulte o guia de [Testes](./Testes.md).
