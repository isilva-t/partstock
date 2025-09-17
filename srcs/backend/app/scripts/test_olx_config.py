"""
Script to test OLX API configuration fetching
Run with: python -m app.scripts.test_olx_config
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.integrations.olx.config_client import OLXConfigClient

async def main():
    """Test OLX configuration fetching"""
    
    print("🧪 Testing OLX API Configuration Fetching")
    print("=" * 50)
    
    client = OLXConfigClient()
    
    try:
        # Run comprehensive analysis
        await client.analyze_config_data()
        
        print("\n🎯 Quick Reference:")
        print("- Review saved JSON files in data/olx_config/")
        print("- Look for your component categories in olx_auto_categories.json")
        print("- Check required attributes for relevant categories")
        print("- Verify your city ID is valid")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Configuration test completed successfully!")
    else:
        print("\n💔 Configuration test failed!")
        sys.exit(1)
