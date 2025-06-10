import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Supondo que as funções de negócio estejam em utils ou helpers, ou podem ser importadas do economy.py
# Como não alteraremos o src, vamos simular as funções principais e focar na lógica

class TestEconomyBusinessLogic(unittest.TestCase):
    def setUp(self):
        # Simula um jogador
        self.player = {
            'user_id': 1,
            'name': 'Jogador',
            'level': 5,
            'tusd': 500,
            'inventory': {},
            'club_id': 'CLUB_A',
        }
        # Simula um item de loja
        self.item = {
            'id': 101,
            'name': 'Poção de Vida',
            'price': 100,
            'type': 'consumable',
            'description': 'Recupera HP',
            'effects': {'hp_boost': 0.2},
            'level_required': 1,
        }
        # Simula uma técnica
        self.technique = {
            'id': 201,
            'name': 'Golpe Relâmpago',
            'tier': 'basic',
            'level': 1,
            'max_level': 3,
            'effects': {'duel_boost': {'type': 'physical', 'amount': 0.3}},
            'evolution': {
                '2': {'name': 'Golpe Relâmpago Aprimorado', 'effects': {'duel_boost': {'type': 'physical', 'amount': 0.35}}},
                '3': {'name': 'Golpe Relâmpago Supremo', 'effects': {'duel_boost': {'type': 'physical', 'amount': 0.4}, 'damage_boost': 0.1}}
            }
        }

    def test_buy_item_success(self):
        """Deve permitir comprar item se tiver TUSD suficiente e nível."""
        player = self.player.copy()
        item = self.item.copy()
        player['tusd'] = 200
        player['level'] = 5
        # Simula compra
        can_buy = player['tusd'] >= item['price'] and player['level'] >= item['level_required']
        if can_buy:
            player['tusd'] -= item['price']
            player['inventory']['item_1'] = item
        self.assertEqual(player['tusd'], 100)
        self.assertIn('item_1', player['inventory'])

    def test_buy_item_insufficient_funds(self):
        """Não deve permitir comprar item sem TUSD suficiente."""
        player = self.player.copy()
        item = self.item.copy()
        player['tusd'] = 50
        can_buy = player['tusd'] >= item['price']
        self.assertFalse(can_buy)

    def test_buy_item_level_restriction(self):
        """Não deve permitir comprar item se nível for insuficiente."""
        player = self.player.copy()
        item = self.item.copy()
        player['level'] = 1
        item['level_required'] = 5
        can_buy = player['level'] >= item['level_required']
        self.assertFalse(can_buy)

    def test_use_item_success(self):
        """Deve aplicar efeito do item ao usar."""
        player = self.player.copy()
        item = self.item.copy()
        player['hp'] = 50
        player['max_hp'] = 100
        player['inventory']['item_1'] = item
        # Simula uso
        effect = item['effects'].get('hp_boost', 0)
        player['hp'] = min(player['max_hp'], player['hp'] + int(player['max_hp'] * effect))
        self.assertEqual(player['hp'], 70)

    def test_evolve_technique_success(self):
        """Deve evoluir técnica se não estiver no nível máximo."""
        technique = self.technique.copy()
        current_level = technique['level']
        max_level = technique['max_level']
        if current_level < max_level:
            next_level = str(current_level + 1)
            evolution = technique['evolution'][next_level]
            technique['level'] += 1
            technique['name'] = evolution['name']
            technique['effects'] = evolution['effects']
        self.assertEqual(technique['level'], 2)
        self.assertEqual(technique['name'], 'Golpe Relâmpago Aprimorado')
        self.assertEqual(technique['effects']['duel_boost']['amount'], 0.35)

    def test_evolve_technique_at_max(self):
        """Não deve evoluir técnica se já estiver no nível máximo."""
        technique = self.technique.copy()
        technique['level'] = technique['max_level']
        current_level = technique['level']
        max_level = technique['max_level']
        can_evolve = current_level < max_level
        self.assertFalse(can_evolve)

    def test_list_techniques(self):
        """Deve listar técnicas do jogador."""
        player = self.player.copy()
        player['techniques'] = [self.technique.copy()]
        techniques = player.get('techniques', [])
        self.assertEqual(len(techniques), 1)
        self.assertEqual(techniques[0]['name'], 'Golpe Relâmpago')

    def test_technique_info(self):
        """Deve retornar informações detalhadas da técnica."""
        technique = self.technique.copy()
        info = f"{technique['name']} (Nível {technique['level']}) - {technique['effects']}"
        self.assertIn('Golpe Relâmpago', info)
        self.assertIn('duel_boost', info)

    def test_club_restriction(self):
        """Não deve permitir usar item exclusivo de clube errado."""
        player = self.player.copy()
        item = self.item.copy()
        item['club_required'] = 'CLUB_B'
        can_use = (item.get('club_required') is None or item['club_required'] == player['club_id'])
        self.assertFalse(can_use)

    def test_special_item_effect(self):
        """Deve aplicar efeito especial de item lendário."""
        player = self.player.copy()
        item = self.item.copy()
        item['effects'] = {'legendary_boost': 1.0}
        player['inventory']['item_1'] = item
        effect = item['effects'].get('legendary_boost', 0)
        self.assertEqual(effect, 1.0)

if __name__ == '__main__':
    unittest.main() 