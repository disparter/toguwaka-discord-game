import unittest
from unittest.mock import MagicMock
from datetime import datetime

class TestClubBusinessLogic(unittest.TestCase):
    def setUp(self):
        self.player = {
            'user_id': 1,
            'name': 'Jogador',
            'level': 10,
            'club_id': 'CLUB_A',
            'reputation': 100,
            'season_rewards': [],
        }
        self.club = {
            'club_id': 'CLUB_A',
            'name': 'Clube Alpha',
            'reputation': 1000,
            'members': [1, 2, 3],
            'created_at': datetime(2023, 1, 1),
        }
        self.exchange = {
            'id': 1,
            'required_items': ['item1', 'item2'],
            'reward': 'item3',
        }

    def test_join_club_success(self):
        """Deve permitir entrar em clube se não for membro de outro."""
        player = self.player.copy()
        player['club_id'] = None
        club = self.club.copy()
        can_join = player['club_id'] is None
        if can_join:
            player['club_id'] = club['club_id']
        self.assertEqual(player['club_id'], 'CLUB_A')

    def test_join_club_already_member(self):
        """Não deve permitir entrar em clube se já for membro de outro."""
        player = self.player.copy()
        player['club_id'] = 'CLUB_B'
        can_join = player['club_id'] is None
        self.assertFalse(can_join)

    def test_club_ranking(self):
        """Deve ordenar clubes por reputação para ranking."""
        clubs = [
            {'club_id': 'A', 'reputation': 100},
            {'club_id': 'B', 'reputation': 300},
            {'club_id': 'C', 'reputation': 200},
        ]
        ranking = sorted(clubs, key=lambda c: c['reputation'], reverse=True)
        self.assertEqual([c['club_id'] for c in ranking], ['B', 'C', 'A'])

    def test_seasonal_reward_eligibility(self):
        """Deve permitir receber recompensa sazonal se ainda não recebeu."""
        player = self.player.copy()
        season = '2024Q2'
        eligible = season not in player['season_rewards']
        if eligible:
            player['season_rewards'].append(season)
        self.assertIn(season, player['season_rewards'])

    def test_seasonal_reward_already_received(self):
        """Não deve permitir receber recompensa sazonal repetida."""
        player = self.player.copy()
        season = '2024Q2'
        player['season_rewards'] = [season]
        eligible = season not in player['season_rewards']
        self.assertFalse(eligible)

    def test_exchange_items_success(self):
        """Deve permitir troca se jogador possui todos os itens requeridos."""
        player = self.player.copy()
        player['inventory'] = {'item1': {}, 'item2': {}}
        exchange = self.exchange.copy()
        can_exchange = all(item in player['inventory'] for item in exchange['required_items'])
        if can_exchange:
            for item in exchange['required_items']:
                del player['inventory'][item]
            player['inventory'][exchange['reward']] = {}
        self.assertIn('item3', player['inventory'])
        self.assertNotIn('item1', player['inventory'])

    def test_exchange_items_missing(self):
        """Não deve permitir troca se faltar item requerido."""
        player = self.player.copy()
        player['inventory'] = {'item1': {}}
        exchange = self.exchange.copy()
        can_exchange = all(item in player['inventory'] for item in exchange['required_items'])
        self.assertFalse(can_exchange)

    def test_apply_effect_with_usage_limit(self):
        """Deve aplicar o efeito do item com limite de uso."""
        self.player['hp'] = 100
        self.item = {
            'effects': {
                'value': 50,
            },
        }
        self.player['max_hp'] = 100
        self.player['hp'] = min(self.player['hp'] + self.item['effects']['value'], self.player['max_hp'])
        self.assertEqual(self.player['hp'], 100)

if __name__ == '__main__':
    unittest.main() 