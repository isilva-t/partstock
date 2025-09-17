"""
OLX API configuration constants - simplified for single category
"""

# Everything goes here
OLX_CATEGORY_ID = 377  # "Peças e Acessórios"
OLX_CITY_ID = 1063945  # Ovar

# Fixed advert template - same for all parts
OLX_ADVERT_BASE = {
    "category_id": 377,
    "advertiser_type": "business",
    "location": {"city_id": 1063945},
    "price": {"currency": "EUR",
              "negotiable": False,
              "trade": False,
              "budget": False},
    "attributes": [{"code": "state", "value": "used"}]
}
