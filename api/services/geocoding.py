"""
Geocoding service for address lookups.
"""
import requests
from django.conf import settings


class GeocodingService:
    """Service for geocoding operations."""
    
    def __init__(self):
        self.provider = getattr(settings, 'GEOCODING_PROVIDER', 'locationiq')
        self.api_key = getattr(settings, 'GEOCODING_API_KEY', '')
    
    def forward_geocode(self, address):
        """Convert address to coordinates."""
        if self.provider == 'locationiq':
            return self._locationiq_forward(address)
        elif self.provider == 'geoapify':
            return self._geoapify_forward(address)
        elif self.provider == 'nominatim':
            return self._nominatim_forward(address)
        else:
            raise ValueError(f"Unknown geocoding provider: {self.provider}")
    
    def reverse_geocode(self, latitude, longitude):
        """Convert coordinates to address."""
        if self.provider == 'locationiq':
            return self._locationiq_reverse(latitude, longitude)
        elif self.provider == 'geoapify':
            return self._geoapify_reverse(latitude, longitude)
        elif self.provider == 'nominatim':
            return self._nominatim_reverse(latitude, longitude)
        else:
            raise ValueError(f"Unknown geocoding provider: {self.provider}")
    
    def autocomplete(self, query):
        """Address autocomplete."""
        if self.provider == 'locationiq':
            return self._locationiq_autocomplete(query)
        elif self.provider == 'geoapify':
            return self._geoapify_autocomplete(query)
        else:
            # Nominatim doesn't have autocomplete, use forward geocode
            return self._nominatim_forward(query)
    
    def radius_search(self, latitude, longitude, radius_km):
        """Search within radius (placeholder - would need specific API support)."""
        # This would typically use a specialized API like Geoapify Isolines
        # For now, return basic info
        return {
            'center': {'latitude': latitude, 'longitude': longitude},
            'radius_km': radius_km
        }
    
    # LocationIQ implementations
    def _locationiq_forward(self, address):
        """LocationIQ forward geocoding."""
        url = 'https://us1.locationiq.com/v1/search.php'
        params = {
            'key': self.api_key,
            'q': address,
            'format': 'json',
            'limit': 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return {
                'latitude': float(data[0]['lat']),
                'longitude': float(data[0]['lon']),
                'address': data[0].get('display_name', address)
            }
        return {'error': 'No results found'}
    
    def _locationiq_reverse(self, latitude, longitude):
        """LocationIQ reverse geocoding."""
        url = 'https://us1.locationiq.com/v1/reverse.php'
        params = {
            'key': self.api_key,
            'lat': latitude,
            'lon': longitude,
            'format': 'json'
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            'address': data.get('display_name', ''),
            'latitude': latitude,
            'longitude': longitude
        }
    
    def _locationiq_autocomplete(self, query):
        """LocationIQ autocomplete."""
        url = 'https://us1.locationiq.com/v1/autocomplete.php'
        params = {
            'key': self.api_key,
            'q': query,
            'format': 'json',
            'limit': 10
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return [{
            'address': item.get('display_name', ''),
            'latitude': float(item['lat']),
            'longitude': float(item['lon'])
        } for item in data]
    
    # Geoapify implementations
    def _geoapify_forward(self, address):
        """Geoapify forward geocoding."""
        url = 'https://api.geoapify.com/v1/geocode/search'
        params = {
            'text': address,
            'apiKey': self.api_key,
            'limit': 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('features'):
            feature = data['features'][0]
            coords = feature['geometry']['coordinates']
            return {
                'latitude': coords[1],
                'longitude': coords[0],
                'address': feature['properties'].get('formatted', address)
            }
        return {'error': 'No results found'}
    
    def _geoapify_reverse(self, latitude, longitude):
        """Geoapify reverse geocoding."""
        url = 'https://api.geoapify.com/v1/geocode/reverse'
        params = {
            'lat': latitude,
            'lon': longitude,
            'apiKey': self.api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('features'):
            feature = data['features'][0]
            return {
                'address': feature['properties'].get('formatted', ''),
                'latitude': latitude,
                'longitude': longitude
            }
        return {'error': 'No results found'}
    
    def _geoapify_autocomplete(self, query):
        """Geoapify autocomplete."""
        url = 'https://api.geoapify.com/v1/geocode/autocomplete'
        params = {
            'text': query,
            'apiKey': self.api_key,
            'limit': 10
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return [{
            'address': feature['properties'].get('formatted', ''),
            'latitude': feature['geometry']['coordinates'][1],
            'longitude': feature['geometry']['coordinates'][0]
        } for feature in data.get('features', [])]
    
    # Nominatim implementations
    def _nominatim_forward(self, address):
        """Nominatim forward geocoding."""
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        headers = {'User-Agent': 'Installation-System/1.0'}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return {
                'latitude': float(data[0]['lat']),
                'longitude': float(data[0]['lon']),
                'address': data[0].get('display_name', address)
            }
        return {'error': 'No results found'}
    
    def _nominatim_reverse(self, latitude, longitude):
        """Nominatim reverse geocoding."""
        url = 'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json'
        }
        headers = {'User-Agent': 'Installation-System/1.0'}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return {
            'address': data.get('display_name', ''),
            'latitude': latitude,
            'longitude': longitude
        }
