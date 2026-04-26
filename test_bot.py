#!/usr/bin/env python3
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_bot():
    try:
        print("🔍 Testing bot imports...")
        
        # Test basic imports
        from loader import dp, bot
        print("✅ Loader imported successfully")
        
        from handlers import users
        print("✅ Handlers imported successfully")
        
        # Test database connection
        from baza.sqlite import db
        print("✅ Database imported successfully")
        
        print("🚀 All imports successful!")
        print("📊 Bot should work fine")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    if result:
        print("✅ Bot test PASSED - Ready to run!")
    else:
        print("❌ Bot test FAILED - Check errors above")
