import json
import os
from typing import Dict, List, Optional
from .image_manager import ImageManager

class NarrativeManager:
    def __init__(self, narrative_path: str = "data/story_mode/narrative"):
        self.narrative_path = narrative_path
        self.image_manager = ImageManager()
        self.chapters = self._load_chapters()
        
    def _load_chapters(self) -> Dict:
        """Carrega todos os capítulos da narrativa."""
        chapters = {}
        chapters_dir = os.path.join(self.narrative_path, "chapters")
        for filename in os.listdir(chapters_dir):
            if filename.endswith(".json"):
                chapter_id = filename[:-5]  # Remove .json
                with open(os.path.join(chapters_dir, filename), 'r', encoding='utf-8') as f:
                    chapters[chapter_id] = json.load(f)
        return chapters
    
    def get_chapter(self, chapter_id: str) -> Optional[Dict]:
        """Retorna um capítulo específico."""
        return self.chapters.get(chapter_id)
    
    def get_scene(self, chapter_id: str, scene_id: str) -> Optional[Dict]:
        """Retorna uma cena específica de um capítulo."""
        chapter = self.get_chapter(chapter_id)
        if not chapter:
            return None
        
        for scene in chapter.get("scenes", []):
            if scene.get("scene_id") == scene_id:
                return self._process_scene_images(scene)
        return None
    
    def _process_scene_images(self, scene: Dict) -> Dict:
        """Processa as imagens de uma cena usando o ImageManager."""
        processed_scene = scene.copy()
        
        # Processa o background
        if "background" in processed_scene:
            processed_scene["background"] = self.image_manager.get_location_image(
                processed_scene["background"].replace(".png", "")
            )
        
        # Processa as imagens dos personagens
        if "characters" in processed_scene:
            for character in processed_scene["characters"]:
                if "image" in character:
                    character["image"] = self.image_manager.get_character_image(
                        character["id"],
                        character.get("expression", "default")
                    )
        
        return processed_scene
    
    def get_next_scene(self, chapter_id: str, current_scene_id: str, choice_index: int) -> Optional[Dict]:
        """Retorna a próxima cena baseada na escolha do jogador."""
        scene = self.get_scene(chapter_id, current_scene_id)
        if not scene or "choices" not in scene:
            return None
        
        choice = scene["choices"][choice_index]
        if "next_scene" in choice:
            return self.get_scene(chapter_id, choice["next_scene"])
        return None
    
    def get_available_choices(self, chapter_id: str, scene_id: str) -> List[Dict]:
        """Retorna as escolhas disponíveis em uma cena."""
        scene = self.get_scene(chapter_id, scene_id)
        if not scene or "choices" not in scene:
            return []
        return scene["choices"]
    
    def get_character_dialogue(self, chapter_id: str, scene_id: str) -> List[Dict]:
        """Retorna o diálogo de uma cena."""
        scene = self.get_scene(chapter_id, scene_id)
        if not scene or "dialogue" not in scene:
            return []
        return scene["dialogue"]
    
    def get_scene_effects(self, chapter_id: str, scene_id: str, choice_index: int) -> Dict:
        """Retorna os efeitos de uma escolha específica."""
        scene = self.get_scene(chapter_id, scene_id)
        if not scene or "choices" not in scene:
            return {}
        
        choice = scene["choices"][choice_index]
        return choice.get("effects", {})
    
    def get_romance_scene(self, scene_type: str, index: int = 0) -> Dict:
        """Retorna uma cena romântica específica."""
        return {
            "background": self.image_manager.get_romance_image(scene_type, index),
            "type": scene_type,
            "index": index
        }
    
    def get_battle_scene(self, element: str) -> Dict:
        """Retorna uma cena de batalha específica."""
        return {
            "background": self.image_manager.get_battle_image(element),
            "element": element
        }
    
    def get_event_scene(self, event_type: str) -> Dict:
        """Retorna uma cena de evento específica."""
        return {
            "background": self.image_manager.get_event_image(event_type),
            "type": event_type
        } 