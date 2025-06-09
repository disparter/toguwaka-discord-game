import re
import unicodedata

def normalize_club_name(name: str) -> str:
    """Normalize club name for comparison by removing accents, converting to lowercase, and replacing special characters with spaces."""
    # Remove accents
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Replace hyphens and special characters with spaces
    name = re.sub(r'[^a-zA-Z0-9 ]', ' ', name)
    # Convert to lowercase and remove extra spaces
    return ' '.join(name.lower().split()) 