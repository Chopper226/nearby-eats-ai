import time
import requests

from config import GOOGLE_MAPS_API_KEY

# Google Maps
class GoogleMapsSearcher:
    """Google Maps 搜尋"""
    
    @staticmethod
    def get_coordinates(location: str):
        """取得座標"""
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": location,
                "key": GOOGLE_MAPS_API_KEY,
                "language": "zh-TW"
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data["status"] == "OK":
                loc = data["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
        except:
            pass
        return None, None
    
    @staticmethod
    def search_restaurants(lat: float, lng: float, keyword: str = "餐廳", radius: int = 1000, max_results: int = 5):
        """搜尋餐廳"""
        try:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": "restaurant",
                "key": GOOGLE_MAPS_API_KEY,
                "language": "zh-TW"
            }
            
            if keyword:
                params["keyword"] = keyword
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data["status"] == "OK":
                restaurants = []
                for place in data.get("results", [])[:max_results]:
                    restaurant = {
                        "name": place.get("name", "未知"),
                        "address": place.get("vicinity", "地址不明"),
                        "rating": place.get("rating"),
                        "price_level": place.get("price_level"),
                        "types": place.get("types", []),
                        "open_now": place.get("opening_hours", {}).get("open_now"),
                        "source": "google_maps",
                        "place_id": place.get("place_id", "")
                    }
                    restaurants.append(restaurant)
                return restaurants
        except:
            pass
        return []