import httpx
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.config import settings

class OLXConfigClient:
    """Fetch OLX configuration data using client_credentials"""
    
    def __init__(self):
        self.base_url = "https://www.olx.pt/api/partner"
        self.auth_url = "https://www.olx.pt/api/open/oauth/token"
        self.client_id = settings.OLX_CLIENT_ID
        self.client_secret = settings.OLX_CLIENT_SECRET
        
        # Simple token caching (in memory for testing)
        self._token = None
        self._token_expires = None

    async def get_access_token(self) -> str:
        """Get client_credentials token for config data"""
        if self._token and self._token_expires > datetime.now():
            return self._token
            
        print("🔑 Getting new OLX access token...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.auth_url, 
                    json={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "v2 read"
                    },
                    headers={
                        "User-Agent": "PartStock/1.0"
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                self._token = data["access_token"]
                expires_in = data["expires_in"]
                self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                
                print(f"✅ Token obtained, expires in {expires_in} seconds")
                return self._token
                
            except httpx.HTTPStatusError as e:
                print(f"❌ Auth error: {e.response.status_code}")
                print(f"Response: {e.response.text}")
                raise
            except Exception as e:
                print(f"❌ Network error: {e}")
                raise

    async def api_request(self, endpoint: str, params: Dict = None) -> Dict[Any, Any]:
        """Make authenticated API request"""
        token = await self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Version": "2.0",
            "Accept": "application/json",
            "User-Agent": "PartStock/1.0"
        }
        
        url = f"{self.base_url}{endpoint}"
        print(f"📡 Requesting: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                result = response.json()
                
                # Handle wrapped responses - return the data array if it exists
                if isinstance(result, dict) and "data" in result:
                    return result["data"]
                
                return result
                
            except httpx.HTTPStatusError as e:
                print(f"❌ API error: {e.response.status_code}")
                print(f"Response: {e.response.text}")
                raise
            except Exception as e:
                print(f"❌ Request error: {e}")
                raise

    async def fetch_categories(self, save_to_file: bool = True) -> List[Dict]:
        """Fetch all OLX categories"""
        print("\n📂 Fetching OLX categories...")
        
        categories = await self.api_request("/categories")
        print(f"✅ Found {len(categories)} categories")
        
        if save_to_file:
            self._save_json_data(categories, "olx_categories.json")
            
        return categories

    async def fetch_cities(self, save_to_file: bool = True) -> List[Dict]:
        """Fetch all cities"""
        print("\n🏙️  Fetching OLX cities...")
        
        cities = await self.api_request("/cities", params={"limit": 5000})
        print(f"✅ Found {len(cities)} cities")
        
        if save_to_file:
            self._save_json_data(cities, "olx_cities.json")
            
        return cities

    async def fetch_languages(self, save_to_file: bool = True) -> List[Dict]:
        """Fetch supported languages"""
        print("\n🌍 Fetching supported languages...")
        
        languages = await self.api_request("/languages")
        print(f"✅ Found {len(languages)} languages")
        
        if save_to_file:
            self._save_json_data(languages, "olx_languages.json")
            
        return languages

    async def fetch_currencies(self, save_to_file: bool = True) -> List[Dict]:
        """Fetch supported currencies"""
        print("\n💰 Fetching supported currencies...")
        
        currencies = await self.api_request("/currencies")
        print(f"✅ Found {len(currencies)} currencies")
        
        if save_to_file:
            self._save_json_data(currencies, "olx_currencies.json")
            
        return currencies

    async def find_auto_parts_categories(self, categories: List[Dict] = None) -> List[Dict]:
        """Find categories related to auto parts"""
        if not categories:
            categories = await self.fetch_categories(save_to_file=False)
            
        print("\n🔍 Searching for auto parts categories...")
        
        # Keywords that might indicate auto parts categories
        auto_keywords = [
            'auto', 'car', 'vehicle', 'parts', 'peças', 'automóvel', 
            'motor', 'engine', 'chassis', 'electrical', 'elétrica',
            'brake', 'travão', 'suspension', 'suspensão', 'carros',
            'motos', 'acessórios'
        ]
        
        auto_categories = []
        for cat in categories:
            if not isinstance(cat, dict):
                continue
                
            name_lower = cat['name'].lower()
            if any(keyword in name_lower for keyword in auto_keywords):
                auto_categories.append(cat)
        
        print(f"✅ Found {len(auto_categories)} potential auto parts categories")
        
        # Print them for review
        for cat in auto_categories:
            parent_info = f" (parent: {cat['parent_id']})" if cat.get('parent_id') else ""
            leaf_info = " [LEAF]" if cat.get('is_leaf') else ""
            print(f"  - {cat['id']}: {cat['name']}{parent_info}{leaf_info}")
            
        self._save_json_data(auto_categories, "olx_auto_categories.json")
        return auto_categories

    async def fetch_category_attributes(self, category_id: int, save_to_file: bool = True) -> List[Dict]:
        """Fetch required attributes for a specific category"""
        print(f"\n📋 Fetching attributes for category {category_id}...")
        
        try:
            attributes = await self.api_request(f"/categories/{category_id}/attributes")
            print(f"✅ Found {len(attributes)} attributes")
            
            # Show required attributes
            required_attrs = [attr for attr in attributes if attr.get('validation', {}).get('required')]
            print(f"📌 {len(required_attrs)} required attributes:")
            for attr in required_attrs:
                print(f"  - {attr['code']}: {attr['label']}")
            
            if save_to_file:
                self._save_json_data(attributes, f"olx_category_{category_id}_attributes.json")
                
            return attributes
            
        except Exception as e:
            print(f"❌ Could not fetch attributes for category {category_id}: {e}")
            return []

    def _save_json_data(self, data: Any, filename: str):
        """Save data to JSON file"""
        output_dir = Path("data/olx_config")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved to: {filepath}")

    def find_city_by_name(self, cities: List[Dict], city_name: str) -> List[Dict]:
        """Find cities matching name"""
        matches = [
            city for city in cities 
            if city_name.lower() in city['name'].lower()
        ]
        return matches

    async def analyze_config_data(self):
        """Comprehensive analysis of OLX config data"""
        print("🚀 Starting OLX configuration analysis...\n")
        
        try:
            # Fetch all config data
            categories = await self.fetch_categories()
            cities = await self.fetch_cities()
            languages = await self.fetch_languages()
            currencies = await self.fetch_currencies()
            
            # Find auto-related categories
            auto_categories = await self.find_auto_parts_categories(categories)
            
            # Check your default city
            if hasattr(settings, 'OLX_DEFAULT_CITY_ID'):
                print(f"\n🏠 Checking your default city ID: {settings.OLX_DEFAULT_CITY_ID}")
                your_city = next(
                    (city for city in cities if city['id'] == int(settings.OLX_DEFAULT_CITY_ID)), 
                    None
                )
                if your_city:
                    print(f"✅ Your city: {your_city['name']} (region: {your_city.get('region_id')})")
                else:
                    print("❌ Your default city ID not found!")
            
            # Analyze a few promising auto categories
            print("\n🔬 Analyzing key auto parts categories...")
            for cat in auto_categories[:3]:  # Check first 3
                if cat.get('is_leaf'):  # Only leaf categories can have adverts
                    await self.fetch_category_attributes(cat['id'])
            
            print("\n✅ Configuration analysis complete!")
            print("📁 Check 'data/olx_config/' directory for saved files")
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            raise
