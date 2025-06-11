"""
Testes para o sistema de efeitos de itens.
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

class TestItemEffectHandler(unittest.TestCase):
    def setUp(self):
        self.player = {
            'user_id': '123456789',
            'name': 'TestUser',
            'level': 1,
            'exp': 0,
            'hp': 100,
            'max_hp': 100,
            'strength': 10,
            'agility': 10,
            'intelligence': 10
        }
        self.item = {
            'id': 'test_item',
            'name': 'Test Item',
            'type': 'consumable',
            'category': 'support',
            'rarity': 'common',
            'price': 100,
            'effects': {
                'type': 'healing',
                'value': 50
            },
            'usage_limits': {
                'daily': 3,
                'weekly': 10,
                'monthly': 30
            }
        }
        self.usage_records = {
            'daily': [],
            'weekly': [],
            'monthly': []
        }

    def test_apply_effect_with_usage_limit(self):
        """Testa aplicação de efeito com limite de uso."""
        # Simula uso dentro do limite
        self.usage_records['daily'] = [
            {'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()},
            {'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()}
        ]
        
        # Verifica se pode usar o item
        can_use = len(self.usage_records['daily']) < self.item['usage_limits']['daily']
        self.assertTrue(can_use)

        # Aplica o efeito
        if can_use:
            self.usage_records['daily'].append({'timestamp': datetime.now().isoformat()})
            self.player['hp'] = min(self.player['hp'] + self.item['effects']['value'], self.player['max_hp'])

        self.assertEqual(len(self.usage_records['daily']), 3)
        self.assertEqual(self.player['hp'], 150)

    def test_apply_effect_exceeds_usage_limit(self):
        """Testa tentativa de uso além do limite diário."""
        # Simula uso além do limite
        self.usage_records['daily'] = [
            {'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()},
            {'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()},
            {'timestamp': (datetime.now() - timedelta(hours=3)).isoformat()}
        ]
        
        # Verifica se pode usar o item
        can_use = len(self.usage_records['daily']) < self.item['usage_limits']['daily']
        self.assertFalse(can_use)

    def test_handle_healing_effect(self):
        """Testa o efeito de cura."""
        # Simula jogador com HP reduzido
        self.player['hp'] = 50
        
        # Aplica efeito de cura
        heal_amount = self.item['effects']['value']
        self.player['hp'] = min(self.player['hp'] + heal_amount, self.player['max_hp'])
        
        self.assertEqual(self.player['hp'], 100)

    def test_handle_cooldown_reduction(self):
        """Testa o efeito de redução de cooldown."""
        # Simula cooldowns ativos
        cooldowns = {
            'skill1': datetime.now() + timedelta(minutes=30),
            'skill2': datetime.now() + timedelta(minutes=20)
        }
        
        # Aplica redução de 50%
        reduction = 0.5
        for skill, cooldown in cooldowns.items():
            remaining = (cooldown - datetime.now()).total_seconds()
            cooldowns[skill] = datetime.now() + timedelta(seconds=remaining * reduction)
        
        # Verifica se os cooldowns foram reduzidos
        self.assertLess((cooldowns['skill1'] - datetime.now()).total_seconds(), 900)  # Menos de 15 minutos
        self.assertLess((cooldowns['skill2'] - datetime.now()).total_seconds(), 600)  # Menos de 10 minutos

    def test_handle_experience_boost(self):
        """Testa o efeito de boost de experiência."""
        # Simula ganho de experiência
        base_exp = 100
        boost_multiplier = 1.5
        
        # Aplica boost
        boosted_exp = int(base_exp * boost_multiplier)
        self.player['exp'] += boosted_exp
        
        self.assertEqual(self.player['exp'], 150)

class TestItemUsageTracking(unittest.TestCase):
    def setUp(self):
        self.usage_records = {
            'daily': [],
            'weekly': [],
            'monthly': []
        }

    def test_track_item_usage(self):
        """Testa o registro de uso de item."""
        # Registra uso
        self.usage_records['daily'].append({
            'timestamp': datetime.now().isoformat()
        })
        
        self.assertEqual(len(self.usage_records['daily']), 1)

    def test_get_item_usage_count(self):
        """Testa a contagem de uso de item."""
        # Simula usos anteriores
        self.usage_records['daily'] = [
            {'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()},
            {'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()}
        ]
        
        count = len(self.usage_records['daily'])
        self.assertEqual(count, 2)

    def test_clear_expired_usage_records(self):
        """Testa a limpeza de registros expirados."""
        # Simula registros antigos e recentes
        self.usage_records['daily'] = [
            {'timestamp': (datetime.now() - timedelta(days=2)).isoformat()},  # Expirado
            {'timestamp': datetime.now().isoformat()}  # Válido
        ]
        
        # Remove registros expirados
        expired = [record for record in self.usage_records['daily'] 
                  if (datetime.now() - datetime.fromisoformat(record['timestamp'])).days >= 1]
        for record in expired:
            self.usage_records['daily'].remove(record)
        
        self.assertEqual(len(self.usage_records['daily']), 1)

if __name__ == '__main__':
    unittest.main() 