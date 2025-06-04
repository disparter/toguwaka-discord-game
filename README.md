# Academia Tokugawa Discord Bot

Um bot de Discord que implementa um jogo interativo baseado no universo da Academia Tokugawa, onde estudantes com superpoderes competem em clubes, disputas políticas e combates táticos dentro de uma escola de elite.

## 🎮 Sobre o Jogo

Em Academia Tokugawa, os jogadores assumem o papel de alunos com superpoderes, buscando conquistar prestígio, reputação e poder dentro da escola. O jogo inclui:

- Criação de personagem com nome, poder e nível de força (1-5 estrelas)
- Afiliação a clubes com diferentes especialidades
- Sistema de atributos: Destreza, Intelecto, Carisma, Poder
- Treinamento para melhorar atributos e ganhar experiência
- Duelos entre jogadores com diferentes tipos de confrontos
- Eventos aleatórios que afetam os jogadores
- Sistema de economia com moeda escolar (TUSD)
- Loja para comprar itens e mercado para negociar entre jogadores
- Técnicas especiais que podem ser aprendidas e utilizadas

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Um token de bot do Discord

### Configuração

1. Clone este repositório:
```bash
git clone https://github.com/seu-usuario/tokugawa-discord-game.git
cd tokugawa-discord-game
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o arquivo `.env` com seu token do Discord e outras opções:
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

   **Importante sobre Intents Privilegiados:**
   - O bot usa intents privilegiados para acessar informações de membros e conteúdo de mensagens
   - Você precisa habilitá-los no [Portal do Desenvolvedor Discord](https://discord.com/developers/applications/):
     1. Acesse o portal e selecione seu aplicativo/bot
     2. Vá para as configurações de "Bot"
     3. Ative "SERVER MEMBERS INTENT" e "MESSAGE CONTENT INTENT" na seção "Privileged Gateway Intents"
   - Alternativamente, defina `USE_PRIVILEGED_INTENTS=False` no arquivo `.env` para executar o bot com funcionalidade limitada

   **Sobre o Guild ID (ID do Servidor):**
   - Configurar o GUILD_ID permite que os comandos do bot sejam registrados diretamente em um servidor específico
   - Isso faz com que os comandos apareçam instantaneamente, sem o atraso de até 1 hora da sincronização global
   - Para obter o ID do seu servidor:
     1. Ative o "Modo Desenvolvedor" nas configurações do Discord (Configurações > Avançado > Modo Desenvolvedor)
     2. Clique com o botão direito no nome do servidor e selecione "Copiar ID"
     3. Cole o ID copiado no campo `GUILD_ID` do arquivo `.env`
   - Se você deixar o campo `GUILD_ID` vazio, os comandos serão registrados globalmente (pode levar até 1 hora para aparecerem)

4. Execute o bot:
```bash
python bot.py
```

## 🎲 Como Jogar

### Adicionando o Bot ao Discord

1. Crie uma aplicação no [Portal do Desenvolvedor Discord](https://discord.com/developers/applications/):
   - Clique em "New Application" e dê um nome para sua aplicação
   - Vá para a seção "Bot" e clique em "Add Bot"
   - Copie o token do bot e adicione-o ao seu arquivo `.env`

2. Configure as permissões e gere o link de convite:
   - Na seção "OAuth2" > "URL Generator", selecione os seguintes escopos:
     - `bot`
     - `applications.commands`
   - Nas permissões do bot, selecione:
     - "Send Messages"
     - "Embed Links"
     - "Read Message History"
     - "Add Reactions"
     - "Use Slash Commands"
     - "Read Messages/View Channels"

3. Use o link gerado para convidar o bot para seu servidor:
   - Abra o link em seu navegador
   - Selecione o servidor onde deseja adicionar o bot
   - Confirme as permissões e complete o processo de autorização
   - O bot aparecerá na lista de membros do servidor

### Começando a Jogar

1. Certifique-se de que o bot esteja online (execute `python bot.py` se ainda não estiver rodando)
2. Vá para qualquer canal de texto onde o bot tenha permissões
3. Digite `/registro ingressar` para criar seu personagem e começar a jogar
4. Siga as instruções do bot para configurar seu personagem, escolher seu poder e clube
5. Use o comando `/ajuda` para ver a lista completa de comandos disponíveis

### Dicas para Jogar

- O bot responde apenas em canais de texto onde ele tem permissão para enviar mensagens
- Todos os comandos são slash commands e começam com `/`
- Você pode interagir com outros jogadores através de duelos usando `/atividade duelar @usuário`
- Treine regularmente com `/atividade treinar` para melhorar seus atributos e subir de nível
- Explore a academia com `/atividade explorar` para encontrar eventos aleatórios e ganhar recompensas

### Solução de Problemas

- **O bot não responde aos comandos:**
  - Verifique se o bot está online e conectado ao Discord
  - Certifique-se de que o bot tem permissões para ler e enviar mensagens no canal
  - Confirme que está usando os comandos de barra (slash commands) que começam com `/`

- **Erro de Intents Privilegiados:**
  - Verifique se você habilitou os intents privilegiados no Portal do Desenvolvedor Discord
  - Ou defina `USE_PRIVILEGED_INTENTS=False` no arquivo `.env` para executar com funcionalidade limitada

- **Problemas de Permissão:**
  - O bot precisa ter permissões adequadas no servidor e no canal
  - Tente dar ao bot o papel de administrador temporariamente para testar
  - Verifique se o bot tem permissão para enviar mensagens com embeds

- **Comandos não funcionam como esperado:**
  - Use `/ajuda` para ver a sintaxe correta dos comandos
  - Alguns comandos requerem menções a outros usuários ou parâmetros específicos
  - Certifique-se de que o bot tem todas as permissões necessárias

## 📋 Comandos

### Comandos de Barra (Slash Commands)

- `/ping` - Verifica se o bot está funcionando (responde com "Pong!")

### Registro e Informações

- `/registro ingressar` - Crie seu personagem e ingresse na Academia Tokugawa
- `/status status` - Veja seu perfil e estatísticas
- `/status inventario` - Veja seus itens e técnicas
- `/status top` - Veja o ranking dos melhores alunos
- `/ajuda` - Exibe a lista de comandos disponíveis

### Atividades

- `/atividade treinar` - Treine para ganhar experiência e melhorar atributos
- `/atividade duelar @usuário [tipo]` - Desafie outro aluno para um duelo (tipos: physical, mental, strategic, social)
- `/atividade explorar` - Explore a academia em busca de eventos aleatórios
- `/atividade evento` - Participe do evento atual

### Clubes

- `/clube info` - Veja informações sobre seu clube
- `/clube lista` - Veja a lista de todos os clubes

### Economia

- `/economia loja` - Acesse a loja da academia
- `/economia comprar <id>` - Compre um item da loja
- `/economia mercado` - Acesse o mercado de itens entre jogadores
- `/economia vender <id> <preço>` - Venda um item no mercado
- `/economia comprar_mercado <id>` - Compre um item do mercado
- `/economia usar <id>` - Use um item do seu inventário

## 🏫 Clubes

A Academia Tokugawa possui diversos clubes, cada um com suas especialidades:

1. **Clube das Chamas** - Mestres do fogo e das artes marciais explosivas
2. **Ilusionistas Mentais** - Especialistas em poderes psíquicos e manipulação mental
3. **Conselho Político** - Líderes estrategistas que controlam a política estudantil
4. **Elementalistas** - Dominam os elementos da natureza com precisão científica
5. **Clube de Combate** - Focados em aperfeiçoar técnicas de luta e duelos táticos

## 🛠️ Tecnologias Utilizadas

- [Python](https://www.python.org/) - Linguagem de programação
- [discord.py](https://discordpy.readthedocs.io/) - API para interação com o Discord
- [SQLite](https://www.sqlite.org/) - Banco de dados para armazenamento de dados dos jogadores

## 📝 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## 🎮 Divirta-se!

Esperamos que você se divirta jogando Academia Tokugawa! Se tiver alguma dúvida ou sugestão, não hesite em entrar em contato.
