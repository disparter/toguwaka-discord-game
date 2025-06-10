import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_script')

# Import the functions we want to test
from src.utils.persistence.db_provider import get_top_players, get_top_players_by_reputation

async def test_get_top_players():
    """Test the get_top_players function."""
    try:
        logger.info("Testing get_top_players function...")
        players = await get_top_players(5)
        logger.info(f"Successfully retrieved {len(players)} top players")
        return True
    except Exception as e:
        logger.error(f"Error testing get_top_players: {e}")
        return False

async def test_get_top_players_by_reputation():
    """Test the get_top_players_by_reputation function."""
    try:
        logger.info("Testing get_top_players_by_reputation function...")
        players = await get_top_players_by_reputation(5)
        logger.info(f"Successfully retrieved {len(players)} top players by reputation")
        return True
    except Exception as e:
        logger.error(f"Error testing get_top_players_by_reputation: {e}")
        return False

async def main():
    """Run all tests."""
    test_results = []
    
    # Test get_top_players
    result = await test_get_top_players()
    test_results.append(("get_top_players", result))
    
    # Test get_top_players_by_reputation
    result = await test_get_top_players_by_reputation()
    test_results.append(("get_top_players_by_reputation", result))
    
    # Print summary
    logger.info("Test Results:")
    all_passed = True
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("All tests passed!")
    else:
        logger.error("Some tests failed.")

if __name__ == "__main__":
    asyncio.run(main())