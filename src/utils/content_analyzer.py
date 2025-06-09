import json
import os
import argparse
from typing import Dict, List, Any, Optional, Union, Tuple
from collections import Counter, defaultdict

# Try to import visualization libraries, but provide fallbacks if not available
try:
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    print("Warning: matplotlib, numpy, or seaborn modules not found. Visualization features will be disabled.")

class ContentAnalyzer:
    """
    A utility class for analyzing narrative content and player choices.
    """
    def __init__(self, data_dir: str = "data/story_mode"):
        """
        Initialize the content analyzer.

        Args:
            data_dir: Directory containing story mode data
        """
        self.data_dir = data_dir
        self.player_data = self._load_player_data()
        self.content_data = self._load_content_data()

    def _load_player_data(self) -> Dict[str, Any]:
        """
        Load player data from the database.
        This is a placeholder - in a real implementation, this would load from the actual database.

        Returns:
            Dictionary mapping player IDs to player data
        """
        # Placeholder - in a real implementation, this would load from the database
        player_data_file = os.path.join(self.data_dir, "player_data.json")
        if os.path.exists(player_data_file):
            with open(player_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_content_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load content data from the data directory.

        Returns:
            Dictionary mapping content types to content data
        """
        content_data = {}

        # Load chapters
        chapters_dir = os.path.join(self.data_dir, "chapters")
        if os.path.exists(chapters_dir):
            content_data["chapters"] = {}
            for filename in os.listdir(chapters_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(chapters_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chapter_data = json.load(f)
                        content_data["chapters"].update(chapter_data)

        # Load events
        events_dir = os.path.join(self.data_dir, "events")
        if os.path.exists(events_dir):
            content_data["events"] = {}
            for filename in os.listdir(events_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(events_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        event_data = json.load(f)
                        content_data["events"].update(event_data)

        return content_data

    def analyze_player_choices(self) -> Dict[str, Any]:
        """
        Analyze player choices across all players.

        Returns:
            Dictionary containing analysis results
        """
        results = {
            "chapter_completion": {},
            "choice_distribution": defaultdict(lambda: defaultdict(int)),
            "event_participation": defaultdict(int),
            "player_progression": {
                "levels": defaultdict(int),
                "hierarchy_tiers": defaultdict(int)
            },
            "relationship_affinities": defaultdict(list)
        }

        # Analyze player data
        for player_id, player in self.player_data.items():
            # Skip players without story progress
            if "story_progress" not in player:
                continue

            story_progress = player["story_progress"]

            # Chapter completion
            completed_chapters = story_progress.get("completed_chapters", [])
            for chapter in completed_chapters:
                results["chapter_completion"][chapter] = results["chapter_completion"].get(chapter, 0) + 1

            # Choice distribution
            choices = story_progress.get("choices", {})
            for chapter_id, chapter_choices in choices.items():
                for choice_key, choice_value in chapter_choices.items():
                    results["choice_distribution"][chapter_id][choice_key] += 1

            # Event participation
            completed_events = story_progress.get("completed_events", [])
            for event in completed_events:
                results["event_participation"][event] += 1

            # Player progression
            level = player.get("level", 1)
            results["player_progression"]["levels"][level] += 1

            hierarchy_tier = story_progress.get("hierarchy_tier", 0)
            results["player_progression"]["hierarchy_tiers"][hierarchy_tier] += 1

            # Relationship affinities
            character_relationships = story_progress.get("character_relationships", {})
            for npc, affinity in character_relationships.items():
                results["relationship_affinities"][npc].append(affinity)

        # Convert defaultdicts to regular dicts for JSON serialization
        results["choice_distribution"] = {k: dict(v) for k, v in results["choice_distribution"].items()}
        results["event_participation"] = dict(results["event_participation"])
        results["player_progression"]["levels"] = dict(results["player_progression"]["levels"])
        results["player_progression"]["hierarchy_tiers"] = dict(results["player_progression"]["hierarchy_tiers"])
        results["relationship_affinities"] = dict(results["relationship_affinities"])

        return results

    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """
        Identify bottlenecks in the narrative where players tend to drop off.

        Returns:
            List of bottlenecks with their details
        """
        bottlenecks = []

        # Get chapter completion counts
        chapter_completion = self.analyze_player_choices()["chapter_completion"]

        # Sort chapters by completion count
        sorted_chapters = sorted(chapter_completion.items(), key=lambda x: x[1])

        # Identify potential bottlenecks (chapters with significantly lower completion than previous chapters)
        prev_count = None
        for chapter, count in sorted_chapters:
            if prev_count is not None and count < prev_count * 0.7:  # 30% drop-off threshold
                bottlenecks.append({
                    "chapter_id": chapter,
                    "completion_count": count,
                    "previous_count": prev_count,
                    "drop_off_percentage": round((1 - count / prev_count) * 100, 2)
                })
            prev_count = count

        return bottlenecks

    def generate_choice_heatmap(self, output_file: str = "choice_heatmap.png") -> None:
        """
        Generate a heatmap of player choices.

        Args:
            output_file: Path to the output image file
        """
        if not HAS_VISUALIZATION:
            print("Error: matplotlib, numpy, and seaborn are required for generating heatmaps.")
            return

        # Get choice distribution
        choice_distribution = self.analyze_player_choices()["choice_distribution"]

        # Prepare data for heatmap
        chapters = []
        choices = []
        values = []

        for chapter, chapter_choices in choice_distribution.items():
            for choice, count in chapter_choices.items():
                chapters.append(chapter)
                choices.append(choice)
                values.append(count)

        # Create a pivot table
        unique_chapters = sorted(set(chapters))
        unique_choices = sorted(set(choices))

        data = np.zeros((len(unique_chapters), len(unique_choices)))

        for i, chapter in enumerate(unique_chapters):
            for j, choice in enumerate(unique_choices):
                for c, ch, v in zip(chapters, choices, values):
                    if c == chapter and ch == choice:
                        data[i, j] = v

        # Create heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(data, annot=True, fmt="d", cmap="YlGnBu",
                   xticklabels=unique_choices, yticklabels=unique_chapters)
        plt.title("Player Choice Distribution")
        plt.xlabel("Choices")
        plt.ylabel("Chapters")
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()

        print(f"Choice heatmap saved to {output_file}")

    def generate_progression_chart(self, output_file: str = "progression_chart.png") -> None:
        """
        Generate a chart showing player progression through the story.

        Args:
            output_file: Path to the output image file
        """
        if not HAS_VISUALIZATION:
            print("Error: matplotlib is required for generating charts.")
            return

        # Get chapter completion counts
        chapter_completion = self.analyze_player_choices()["chapter_completion"]

        # Sort chapters by ID (assuming format like "1_1", "1_2", etc.)
        sorted_chapters = sorted(chapter_completion.items(), key=lambda x: x[0])

        # Prepare data for chart
        chapter_ids = [chapter for chapter, _ in sorted_chapters]
        completion_counts = [count for _, count in sorted_chapters]

        # Create chart
        plt.figure(figsize=(12, 6))
        plt.bar(chapter_ids, completion_counts, color='skyblue')
        plt.title("Player Progression Through Chapters")
        plt.xlabel("Chapter ID")
        plt.ylabel("Number of Players")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()

        print(f"Progression chart saved to {output_file}")

    def export_analytics(self, output_file: str) -> None:
        """
        Export analytics data to a JSON file.

        Args:
            output_file: Path to the output JSON file
        """
        analytics = {
            "player_choices": self.analyze_player_choices(),
            "bottlenecks": self.identify_bottlenecks(),
            "visualization_available": HAS_VISUALIZATION
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)

        print(f"Analytics data exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Analyze narrative content and player choices")
    parser.add_argument("--export", type=str, help="Export analytics data to a JSON file")
    parser.add_argument("--heatmap", type=str, help="Generate a choice heatmap and save to the specified file")
    parser.add_argument("--progression", type=str, help="Generate a progression chart and save to the specified file")
    parser.add_argument("--bottlenecks", action="store_true", help="Identify narrative bottlenecks")

    args = parser.parse_args()

    analyzer = ContentAnalyzer()

    if args.export:
        analyzer.export_analytics(args.export)

    if args.heatmap:
        analyzer.generate_choice_heatmap(args.heatmap)

    if args.progression:
        analyzer.generate_progression_chart(args.progression)

    if args.bottlenecks:
        bottlenecks = analyzer.identify_bottlenecks()
        if bottlenecks:
            print("Identified narrative bottlenecks:")
            for bottleneck in bottlenecks:
                print(f"  Chapter {bottleneck['chapter_id']}: {bottleneck['drop_off_percentage']}% drop-off")
        else:
            print("No significant bottlenecks identified.")

if __name__ == "__main__":
    main()
