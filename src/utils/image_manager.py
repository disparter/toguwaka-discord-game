import json
import os
from typing import Dict, List, Optional

class ImageManager:
    def __init__(self, config_path: str = "data/story_mode/narrative/image_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Carrega a configuração de imagens do arquivo JSON."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_character_image(self, character_id: str, expression: str = "default") -> str:
        """Retorna o caminho da imagem do personagem com a expressão especificada."""
        try:
            if character_id in self.config["image_categories"]["characters"]["professors"]:
                return os.path.join(
                    self.config["image_categories"]["characters"]["base_path"],
                    self.config["image_categories"]["characters"]["professors"][character_id]
                )
            elif character_id in self.config["image_categories"]["characters"]["students"]:
                return os.path.join(
                    self.config["image_categories"]["characters"]["base_path"],
                    self.config["image_categories"]["characters"]["students"][character_id]
                )
            else:
                return os.path.join(
                    self.config["image_categories"]["characters"]["base_path"],
                    self.config["image_categories"]["characters"]["expressions"].get(
                        expression,
                        self.config["fallback_images"]["character"]
                    )
                )
        except KeyError:
            return os.path.join(
                self.config["image_categories"]["characters"]["base_path"],
                self.config["fallback_images"]["character"]
            )
    
    def get_location_image(self, location_id: str, location_type: str = "academy") -> str:
        """Retorna o caminho da imagem do local especificado."""
        try:
            return os.path.join(
                self.config["image_categories"]["locations"]["base_path"],
                self.config["image_categories"]["locations"][location_type][location_id]
            )
        except KeyError:
            return os.path.join(
                self.config["image_categories"]["locations"]["base_path"],
                self.config["fallback_images"]["location"]
            )
    
    def get_romance_image(self, scene_type: str, index: int = 0) -> str:
        """Retorna o caminho da imagem de uma cena romântica."""
        try:
            scenes = self.config["image_categories"]["romance"]["scenes"][scene_type]
            if 0 <= index < len(scenes):
                return os.path.join(
                    self.config["image_categories"]["romance"]["base_path"],
                    scenes[index]
                )
            return os.path.join(
                self.config["image_categories"]["romance"]["base_path"],
                self.config["fallback_images"]["romance"]
            )
        except KeyError:
            return os.path.join(
                self.config["image_categories"]["romance"]["base_path"],
                self.config["fallback_images"]["romance"]
            )
    
    def get_battle_image(self, element: str) -> str:
        """Retorna o caminho da imagem de batalha para o elemento especificado."""
        try:
            return os.path.join(
                self.config["image_categories"]["battle"]["base_path"],
                self.config["image_categories"]["battle"]["elements"][element]
            )
        except KeyError:
            return os.path.join(
                self.config["image_categories"]["battle"]["base_path"],
                self.config["fallback_images"]["battle"]
            )
    
    def get_event_image(self, event_type: str) -> str:
        """Retorna o caminho da imagem de um evento."""
        try:
            return os.path.join(
                self.config["image_categories"]["events"]["base_path"],
                self.config["image_categories"]["events"]["celebrations"][event_type]
            )
        except KeyError:
            return os.path.join(
                self.config["image_categories"]["events"]["base_path"],
                self.config["fallback_images"]["location"]
            )
    
    def get_available_expressions(self) -> List[str]:
        """Retorna a lista de expressões disponíveis."""
        return list(self.config["image_categories"]["characters"]["expressions"].keys())
    
    def get_available_locations(self, location_type: str = "academy") -> List[str]:
        """Retorna a lista de locais disponíveis do tipo especificado."""
        return list(self.config["image_categories"]["locations"][location_type].keys())
    
    def get_available_romance_scenes(self) -> List[str]:
        """Retorna a lista de tipos de cenas românticas disponíveis."""
        return list(self.config["image_categories"]["romance"]["scenes"].keys())
    
    def get_available_elements(self) -> List[str]:
        """Retorna a lista de elementos disponíveis para batalha."""
        return list(self.config["image_categories"]["battle"]["elements"].keys())
    
    def get_available_events(self) -> List[str]:
        """Retorna a lista de eventos disponíveis."""
        return list(self.config["image_categories"]["events"]["celebrations"].keys()) 