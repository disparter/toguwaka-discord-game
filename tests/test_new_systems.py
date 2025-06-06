import unittest
import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story_mode.story_mode import StoryMode
from story_mode.seasonal_events import Season
from story_mode.companions import Companion, CompanionSystem

class TestNewSystems(unittest.TestCase):
    """
    Test class for the new seasonal events and companion systems.
    """
    
    def setUp(self):
        """Set up the test environment."""
        self.story_mode = StoryMode()
        
        # Create a test player
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 10,
            "exp": 1000,
            "tusd": 500,
            "club_id": "science_club",
            "power_type": "elemental",
            "story_progress": {
                "current_year": 1,
                "current_chapter": 3,
                "completed_chapters": ["1_1", "1_2"],
                "hierarchy_tier": 2,
                "hierarchy_points": 25,
                "special_items": [],
                "character_relationships": {},
                "faction_reputation": {
                    "academy_administration": 10,
                    "student_council": 15
                },
                "powers": {
                    "elemental": {
                        "level": 2,
                        "power_points": 10,
                        "unlocked_skills": [],
                        "completed_rituals": [],
                        "completed_challenges": []
                    }
                }
            }
        }
        
    def test_seasonal_events(self):
        """Test the seasonal events system."""
        print("\n=== Testing Seasonal Events System ===")
        
        # Get current season
        current_season = Season.get_current_season()
        print(f"Current season: {current_season.value}")
        
        # Get available seasonal events
        events = self.story_mode.get_current_season_events(self.player_data)
        
        # Print available events
        print("\nAvailable seasonal events:")
        for event_type, event_list in events.items():
            print(f"\n{event_type.upper()}:")
            for event in event_list:
                print(f"  - {event['name']}: {event['description']}")
        
        # Test participating in a seasonal event
        if events["seasonal_events"]:
            event_id = events["seasonal_events"][0]["id"]
            print(f"\nParticipating in event: {event_id}")
            result = self.story_mode.participate_in_seasonal_event(self.player_data, event_id)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Success: {result['message']}")
                print(f"Rewards: {result['event_info']['rewards']}")
                
                # Update player data
                self.player_data = result["player_data"]
        
        # Test participating in a festival mini-game
        if events["academy_festivals"]:
            festival_id = events["academy_festivals"][0]["id"]
            festival = events["academy_festivals"][0]
            
            if festival["mini_games"]:
                mini_game_id = festival["mini_games"][0]["id"]
                print(f"\nParticipating in mini-game: {mini_game_id} at festival: {festival_id}")
                result = self.story_mode.participate_in_mini_game(self.player_data, festival_id, mini_game_id)
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"Success: {result['message']}")
                    print(f"Mini-game info: {result['mini_game_info']}")
                    
                    # Update player data
                    self.player_data = result["player_data"]
        
        # Get seasonal event status
        status = self.story_mode.get_seasonal_event_status(self.player_data)
        print("\nSeasonal event status:")
        print(f"Current season: {status['current_season']}")
        print(f"Participated events: {len(status['participated_events'])}")
        print(f"Mini-games: {len(status['mini_games'])}")
        print(f"Challenges: {len(status['challenges'])}")
        print(f"Weather events: {len(status['weather_events'])}")
        
    def test_companions(self):
        """Test the companion system."""
        print("\n=== Testing Companion System ===")
        
        # Get current chapter
        chapter_id = self.story_mode.progress_manager.get_current_chapter(self.player_data)
        print(f"Current chapter: {chapter_id}")
        
        # Get available companions
        companions = self.story_mode.get_available_companions(self.player_data, chapter_id)
        
        # Print available companions
        print("\nAvailable companions:")
        for companion in companions:
            print(f"  - {companion['name']} ({companion['power_type']}, {companion['specialization']})")
        
        # Test recruiting a companion
        if companions:
            companion_id = companions[0]["id"]
            print(f"\nRecruiting companion: {companion_id}")
            result = self.story_mode.recruit_companion(self.player_data, companion_id)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Success: {result['message']}")
                
                # Update player data
                self.player_data = result["player_data"]
                
                # Test activating the companion
                print(f"\nActivating companion: {companion_id}")
                result = self.story_mode.activate_companion(self.player_data, companion_id)
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"Success: {result['message']}")
                    
                    # Update player data
                    self.player_data = result["player_data"]
                    
                    # Test advancing companion arc
                    print(f"\nAdvancing companion arc: {companion_id}")
                    result = self.story_mode.advance_companion_arc(self.player_data, companion_id, 25)
                    
                    if "error" in result:
                        print(f"Error: {result['error']}")
                    else:
                        print(f"Success: Advanced from {result['previous_progress']} to {result['new_progress']}")
                        if result["milestone_rewards"]:
                            print(f"Milestone rewards: {result['milestone_rewards']}")
                        
                        # Update player data
                        self.player_data = result["player_data"]
                        
                        # Test completing a companion mission
                        companion_status = self.story_mode.get_companion_status(self.player_data, companion_id)
                        
                        if companion_status["available_missions"]:
                            mission_id = companion_status["available_missions"][0]["id"]
                            print(f"\nCompleting companion mission: {mission_id}")
                            result = self.story_mode.complete_companion_mission(self.player_data, companion_id, mission_id)
                            
                            if "error" in result:
                                print(f"Error: {result['error']}")
                            else:
                                print(f"Success: Completed mission '{result['mission_name']}'")
                                print(f"Rewards: {result['rewards']}")
                                
                                # Update player data
                                self.player_data = result["player_data"]
        
        # Get recruited companions
        recruited = self.story_mode.get_recruited_companions(self.player_data)
        print("\nRecruited companions:")
        for companion in recruited:
            print(f"  - {companion['name']} ({companion['power_type']}, {companion['specialization']})")
            print(f"    Active: {companion['active']}, Arc progress: {companion['arc_progress']}, Sync level: {companion['sync_level']}")
        
        # Get active companion
        active = self.story_mode.get_active_companion(self.player_data)
        if active:
            print("\nActive companion:")
            print(f"  - {active['name']} ({active['power_type']}, {active['specialization']})")
            print(f"    Arc progress: {active['arc_progress']}, Sync level: {active['sync_level']}")
            
            # Print available sync abilities
            print("\nAvailable sync abilities:")
            for ability in active["available_sync_abilities"]:
                print(f"  - {ability['name']}: {ability['description']}")
                print(f"    On cooldown: {ability['on_cooldown']}")
                
    def test_integration(self):
        """Test the integration of the new systems with the StoryMode class."""
        print("\n=== Testing Integration with StoryMode ===")
        
        # Start the story
        result = self.story_mode.start_story(self.player_data)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return
            
        # Update player data
        self.player_data = result["player_data"]
        
        # Check for available companions
        if "available_companions" in result:
            print("\nAvailable companions from start_story:")
            for companion in result["available_companions"]:
                print(f"  - {companion['name']} ({companion['power_type']}, {companion['specialization']})")
                
        # Check for available seasonal events
        if "available_seasonal_events" in result:
            print("\nAvailable seasonal events from start_story:")
            for event_type, event_list in result["available_seasonal_events"].items():
                print(f"\n{event_type.upper()}:")
                for event in event_list:
                    print(f"  - {event['name']}: {event['description']}")
                    
        # Process a choice
        if "chapter_data" in result and "choices" in result["chapter_data"] and result["chapter_data"]["choices"]:
            print("\nProcessing a choice...")
            choice_result = self.story_mode.process_choice(self.player_data, 0)
            
            if "error" in choice_result:
                print(f"Error: {choice_result['error']}")
            else:
                print("Choice processed successfully")
                
                # Check for available companions
                if "available_companions" in choice_result:
                    print("\nAvailable companions from process_choice:")
                    for companion in choice_result["available_companions"]:
                        print(f"  - {companion['name']} ({companion['power_type']}, {companion['specialization']})")
                        
                # Check for available seasonal events
                if "available_seasonal_events" in choice_result:
                    print("\nAvailable seasonal events from process_choice:")
                    for event_type, event_list in choice_result["available_seasonal_events"].items():
                        print(f"\n{event_type.upper()}:")
                        for event in event_list:
                            print(f"  - {event['name']}: {event['description']}")

if __name__ == "__main__":
    # Run the tests
    unittest.main()