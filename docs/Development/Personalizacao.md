# Personalização do Bot Academia Tokugawa

Este guia explica como personalizar e estender o bot Academia Tokugawa, adicionando novos comandos, funcionalidades ou modificando comportamentos existentes.

## 🔍 Índice

- [Adicionando Novos Comandos](#adicionando-novos-comandos)
- [Criando Novos Eventos](#criando-novos-eventos)
- [Adicionando Itens ao Jogo](#adicionando-itens-ao-jogo)
- [Criando Novos Clubes](#criando-novos-clubes)
- [Adicionando Novos Companheiros](#adicionando-novos-companheiros)
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
        "title": "Título do Evento",  # Sempre forneça um título significativo para evitar o problema "Untitled Event"
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

### Adicionando um Evento Aleatório com Diálogos

Para criar eventos aleatórios mais complexos com opções de diálogo e recompensas variadas:

1. Abra o arquivo `data/events/extended_random_events.json` (ou crie-o se não existir)
2. Adicione seu novo evento com opções de diálogo:

```json
{
  "title": "Encontro com o Mestre",
  "description": "Você encontra um mestre misterioso que oferece compartilhar sua sabedoria.",
  "type": "positive",
  "effect": {
    "attribute_check": "intellect",
    "difficulty": 7,
    "rewards": {
      "success": [
        {
          "description": "Você absorve o conhecimento avançado",
          "exp": 100,
          "intellect": 2
        },
        {
          "description": "Você aprende uma técnica secreta",
          "exp": 80,
          "power_stat": 1,
          "tusd": 50
        }
      ],
      "failure": [
        {
          "description": "Você não consegue compreender os ensinamentos",
          "exp": 20
        },
        {
          "description": "O mestre fica desapontado com sua falta de foco",
          "exp": 10,
          "tusd": -10
        }
      ]
    }
  },
  "dialogue_options": [
    {
      "text": "Pedir para aprender técnicas de combate",
      "attribute_bonus": "power_stat",
      "bonus_value": 2,
      "success_text": "O mestre fica impressionado com sua aptidão para o combate!",
      "failure_text": "O mestre nota que você precisa de mais treinamento básico."
    },
    {
      "text": "Pedir para aprender conhecimentos arcanos",
      "attribute_bonus": "intellect",
      "bonus_value": 2,
      "success_text": "Sua mente absorve rapidamente os conhecimentos arcanos!",
      "failure_text": "Os conceitos são muito complexos para seu nível atual."
    },
    {
      "text": "Pedir para aprender técnicas de persuasão",
      "attribute_bonus": "charisma",
      "bonus_value": 2,
      "success_text": "O mestre reconhece seu talento natural para influenciar pessoas!",
      "failure_text": "Você precisa desenvolver mais sua presença pessoal."
    }
  ],
  "category": "training",
  "rarity": "rare"
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

## 👥 Adicionando Novos Companheiros

O sistema de companheiros permite que os jogadores recrutem NPCs que os acompanham em sua jornada. Para adicionar um novo companheiro ao jogo:

### Definindo um Novo Companheiro

1. Abra o arquivo `story_mode/companions.py`
2. Adicione seu novo companheiro ao dicionário `default_companions` na classe `CompanionSystem`:

```python
"novo_companheiro_id": {
    "name": "Nome do Companheiro",
    "type": "student",  # ou "faculty" para professores
    "background": {
        "age": 17,
        "origin": "Origem do Companheiro",
        "personality": "Traços de personalidade"
    },
    "power_type": "tipo_de_poder",  # elemental, psychic, physical, etc.
    "specialization": "especialização",  # fogo, telecinese, força, etc.
    "available_chapters": ["1_5", "2_1", "2_3"],  # Capítulos onde pode ser recrutado
    "affinity_thresholds": {
        "hostile": -50,
        "unfriendly": -20,
        "neutral": 0,
        "friendly": 20,
        "close": 50,
        "trusted": 80
    },
    "story_arc": {
        "title": "Título do Arco Narrativo",
        "description": "Descrição da história pessoal do companheiro",
        "milestones": {
            "25": {
                "exp": 300,
                "tusd": 150,
                "sync_level_increase": 1
            },
            "50": {
                "exp": 600,
                "tusd": 300,
                "special_item": "Nome do Item Especial",
                "sync_level_increase": 1
            },
            "75": {
                "exp": 900,
                "tusd": 450,
                "sync_level_increase": 1
            },
            "100": {
                "exp": 1500,
                "tusd": 750,
                "special_item": "Nome do Item Especial Final",
                "sync_level_increase": 1
            }
        },
        "missions": [
            {
                "id": "id_missao_1",
                "name": "Nome da Missão 1",
                "description": "Descrição da missão",
                "rewards": {
                    "exp": 200,
                    "tusd": 100,
                    "arc_progress": 15
                }
            },
            {
                "id": "id_missao_2",
                "name": "Nome da Missão 2",
                "description": "Descrição da missão",
                "rewards": {
                    "exp": 300,
                    "tusd": 150,
                    "arc_progress": 20
                }
            },
            {
                "id": "id_missao_3",
                "name": "Nome da Missão 3",
                "description": "Descrição da missão",
                "rewards": {
                    "exp": 400,
                    "tusd": 200,
                    "arc_progress": 25,
                    "special_item": "Item Especial da Missão"
                }
            },
            {
                "id": "id_missao_4",
                "name": "Nome da Missão 4",
                "description": "Descrição da missão",
                "rewards": {
                    "exp": 800,
                    "tusd": 400,
                    "arc_progress": 40,
                    "special_item": "Item Especial Final da Missão"
                }
            }
        ]
    },
    "sync_abilities": [
        {
            "id": "id_habilidade_1",
            "name": "Nome da Habilidade 1",
            "description": "Descrição da habilidade de sincronização",
            "required_sync_level": 1,
            "cooldown_hours": 24,
            "effects": {
                "stat_boost": {
                    "atributo_1": 1.5,
                    "atributo_2": 1.3
                }
            }
        },
        {
            "id": "id_habilidade_2",
            "name": "Nome da Habilidade 2",
            "description": "Descrição da habilidade de sincronização",
            "required_sync_level": 2,
            "cooldown_hours": 48,
            "effects": {
                "stat_boost": {
                    "atributo_1": 2.0,
                    "atributo_2": 1.8
                }
            }
        },
        {
            "id": "id_habilidade_3",
            "name": "Nome da Habilidade 3",
            "description": "Descrição da habilidade de sincronização",
            "required_sync_level": 3,
            "cooldown_hours": 72,
            "effects": {
                "power_boost": {
                    "power_id": "tipo_de_poder",
                    "amount": 5
                },
                "special_action": {
                    "type": "attack",
                    "damage_multiplier": 2.5,
                    "area_effect": true
                }
            }
        },
        {
            "id": "id_habilidade_4",
            "name": "Nome da Habilidade 4",
            "description": "Descrição da habilidade de sincronização mais poderosa",
            "required_sync_level": 4,
            "cooldown_hours": 168,
            "effects": {
                "special_action": {
                    "type": "utility",
                    "duration_minutes": 60,
                    "effect_description": "Descrição do efeito especial"
                }
            }
        }
    ]
}
```

### Tipos de Efeitos de Sincronização

Os efeitos de sincronização podem ser de vários tipos:

1. **Aumento de Atributos** (`stat_boost`): Aumenta temporariamente atributos do jogador
   - Exemplo: `{"strength": 2.0, "defense": 1.5}`

2. **Aumento de Poder** (`power_boost`): Aumenta pontos de poder de um tipo específico
   - Exemplo: `{"power_id": "elemental", "amount": 5}`

3. **Ações Especiais** (`special_action`): Efeitos especiais com diferentes tipos
   - Tipo `attack`: Ataques poderosos
     - Exemplo: `{"type": "attack", "damage_multiplier": 3.0, "area_effect": true}`
   - Tipo `heal`: Cura e regeneração
     - Exemplo: `{"type": "heal", "heal_percentage": 100, "revive": true}`
   - Tipo `utility`: Efeitos utilitários diversos
     - Exemplo: `{"type": "utility", "duration_minutes": 30, "see_hidden": true}`

### Adicionando Diálogos para o Companheiro

Para adicionar diálogos específicos para seu companheiro:

1. Crie um arquivo JSON em `data/story_mode/npcs/` com o nome do seu companheiro
2. Adicione diálogos específicos:

```json
{
  "novo_companheiro_id": {
    "dialogues": {
      "greeting": {
        "default": {"text": "Olá! Como posso ajudar?"},
        "friendly": {"text": "Ei, que bom te ver novamente!"},
        "close": {"text": "Meu amigo! Estava esperando por você!"}
      },
      "mission_start": {
        "default": {"text": "Precisamos resolver isso juntos."}
      },
      "mission_complete": {
        "default": {"text": "Conseguimos! Bom trabalho!"}
      },
      "sync_activate": {
        "default": {"text": "Vamos combinar nossos poderes!"}
      }
    }
  }
}
```

### Testando seu Novo Companheiro

Para testar seu novo companheiro:

1. Reinicie o bot para carregar as alterações
2. Use o comando `/companheiros` para ver se seu companheiro aparece nos capítulos especificados
3. Tente recrutar e interagir com o companheiro usando os comandos disponíveis

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
