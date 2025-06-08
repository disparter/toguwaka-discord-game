# Tokugawa Academy Discord Game

Um jogo de RPG narrativo baseado em Discord, ambientado na Academia Tokugawa, onde os jogadores exploram uma história rica com múltiplos caminhos, clubes, romances e desenvolvimento de personagem.

## 🎮 Características Principais

- **Sistema de História Dinâmico**: Narrativa ramificada com múltiplos caminhos e escolhas significativas
- **Sistema de Clubes**: Participe de clubes únicos, cada um com sua própria história e progressão
- **Rotas de Romance**: 7 rotas românticas distintas com personagens memoráveis
- **Sistema de Reputação**: Construa relacionamentos com NPCs, clubes e facções
- **Sistema de Imagens**: Imagens dinâmicas que acompanham a narrativa
- **Sistema de Progressão**: Desenvolvimento de habilidades e poderes únicos

## 📁 Estrutura do Projeto

```
tokugawa-discord-game/
├── data/
│   ├── story_mode/
│   │   ├── chapters/           # Capítulos da história
│   │   ├── npcs/              # Dados dos NPCs
│   │   ├── clubs/             # Dados dos clubes
│   │   ├── reputation/        # Sistema de reputação
│   │   └── shops/             # Sistema de lojas
│   └── assets/
│       └── images/
│           └── story/         # Imagens da história
├── story_mode/                # Código principal
├── tests/                     # Testes
└── docs/                      # Documentação
```

## 🎯 Sistemas Principais

### Sistema de História

A história é gerenciada através do `structured_story.json`, que define:
- Capítulos e suas conexões
- Condições de progressão
- Integração com clubes e romances
- Verificações de habilidades

### Sistema de Clubes

Cada clube segue uma estrutura de 4 fases:
1. **Introdução**: Apresentação do clube e seus membros
2. **Crise**: Conflito ou desafio para o clube
3. **Resolução**: Resolução da crise
4. **Final**: Conclusão da história do clube

### Sistema de Romance

7 rotas românticas distintas, cada uma com:
- Eventos únicos
- Progressão de relacionamento
- Cenas especiais
- Múltiplos finais

### Sistema de Imagens

- Imagens de fundo dinâmicas
- Imagens de personagens
- Imagens de locais
- Sistema de fallback para imagens não encontradas

## 🚀 Começando

1. Clone o repositório
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure o arquivo `.env` com suas credenciais
4. Execute o bot:
   ```bash
   python main.py
   ```

## 📚 Documentação Detalhada

Documentação detalhada está disponível em:
- [Estrutura da História](docs/story_structure.md)
- [Sistema de Clubes](docs/club_system.md)
- [Sistema de Romance](docs/romance_system.md)
- [Guia de Escrita](docs/writing_guide.md)

## 🧪 Testes

Execute os testes com:
```bash
python -m unittest discover tests
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
