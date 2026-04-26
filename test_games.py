#!/usr/bin/env python3
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_games_only():
    try:
        print("🔍 Testing games system only...")
        
        # Test games system import
        from handlers.users.games_system import games_system, FALLBACK_GAMES
        print("✅ Games system imported")
        
        # Test games data
        print(f"📊 Total games: {len(FALLBACK_GAMES)}")
        print(f"🎮 First game: {FALLBACK_GAMES[0]['name']}")
        print(f"🌐 First game URL: {FALLBACK_GAMES[0]['url']}")
        
        # Test games retrieval
        games, has_next, has_prev, page = await games_system.get_games(page=0)
        print(f"✅ Games retrieval works: {len(games)} games")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_games_only())
    if result:
        print("🎉 Games system test PASSED!")
    else:
        print("❌ Games system test FAILED!")
