"""
Implementation of the duel narrator.
This class is responsible for generating narrative descriptions of duels.
"""
import random
from typing import Dict, Any
from src.utils.game_mechanics.duel.duel_narrator_interface import IDuelNarrator

class DuelNarrator(IDuelNarrator):
    """Narrator for duel-related narrations."""
    
    # Intro templates based on duel type
    INTROS = {
        "physical": [
            "{winner_name} e {loser_name} começaram uma batalha física intensa!",
            "O ginásio da Academia Tokugawa tremeu com o confronto entre {winner_name} e {loser_name}!"
        ],
        "mental": [
            "Um duelo de mentes brilhantes entre {winner_name} e {loser_name} teve início!",
            "A tensão era palpável enquanto {winner_name} e {loser_name} se enfrentavam em um desafio mental!"
        ],
        "strategic": [
            "Um jogo de estratégia e tática começou entre {winner_name} e {loser_name}!",
            "Como um jogo de xadrez, {winner_name} e {loser_name} planejavam cada movimento cuidadosamente!"
        ],
        "social": [
            "O debate entre {winner_name} e {loser_name} atraiu uma multidão de espectadores!",
            "A influência social estava em jogo enquanto {winner_name} e {loser_name} mediam forças!"
        ],
        "elemental": [
            "Os elementos da natureza se agitaram quando {winner_name} e {loser_name} iniciaram seu duelo elemental!",
            "O ar carregado de energia elemental enquanto {winner_name} e {loser_name} se preparavam para o confronto!"
        ]
    }
    
    # Middle part templates based on win margin
    HIGH_MARGIN_MIDDLES = [
        "{winner_name} demonstrou clara superioridade durante todo o duelo.",
        "A vitória de {winner_name} nunca esteve em dúvida, dominando o confronto."
    ]
    
    LOW_MARGIN_MIDDLES = [
        "Foi uma disputa acirrada, com ambos os lados mostrando grande habilidade.",
        "{winner_name} e {loser_name} estavam muito equilibrados, mas no final a vitória pendeu para um lado."
    ]
    
    # Conclusion templates
    CONCLUSIONS = [
        "No final, {winner_name} emergiu vitorioso, conquistando {exp_reward} de experiência e {tusd_reward} TUSD!",
        "A vitória foi de {winner_name}, que ganhou {exp_reward} de experiência e {tusd_reward} TUSD pelo seu desempenho!"
    ]
    
    @staticmethod
    def generate_narration(duel_result: Dict[str, Any]) -> str:
        """Generate a narrative description of a duel.
        
        Args:
            duel_result (Dict[str, Any]): The result of the duel
            
        Returns:
            str: A narrative description of the duel
        """
        winner = duel_result["winner"]
        loser = duel_result["loser"]
        duel_type = duel_result["duel_type"]
        
        # Format the template variables
        template_vars = {
            "winner_name": winner["name"],
            "loser_name": loser["name"],
            "exp_reward": duel_result["exp_reward"],
            "tusd_reward": duel_result["tusd_reward"]
        }
        
        # Select intro based on duel type
        intros = DuelNarrator.INTROS.get(duel_type, DuelNarrator.INTROS["physical"])
        intro = random.choice(intros).format(**template_vars)
        
        # Select middle part based on win margin
        if duel_result["win_margin"] > 20:
            middle = random.choice(DuelNarrator.HIGH_MARGIN_MIDDLES).format(**template_vars)
        else:
            middle = random.choice(DuelNarrator.LOW_MARGIN_MIDDLES).format(**template_vars)
        
        # Select conclusion
        conclusion = random.choice(DuelNarrator.CONCLUSIONS).format(**template_vars)
        
        # Combine parts
        narration = f"{intro}\n\n{middle}\n\n{conclusion}"
        
        return narration