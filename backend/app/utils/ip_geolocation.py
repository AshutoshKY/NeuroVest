"""
IP Geolocation Utility
Get location information from IP addresses using GeoIP2
"""
import geoip2.database
import geoip2.errors
from typing import Dict, Optional
from pathlib import Path
from loguru import logger
import ipaddress


class IPGeolocation:
    """Get geolocation data from IP addresses"""
    
    # Path to GeoLite2 database
    DB_PATH = Path(__file__).parent.parent / 'data' / 'GeoLite2-City.mmdb'
    
    _reader = None
    
    @classmethod
    def _get_reader(cls):
        """Lazy load the GeoIP2 reader"""
        if cls._reader is None:
            try:
                if cls.DB_PATH.exists():
                    cls._reader = geoip2.database.Reader(str(cls.DB_PATH))
                    logger.info(f"[GEOIP] Loaded GeoIP database from {cls.DB_PATH}")
                else:
                    logger.warning(f"[GEOIP] GeoIP database not found at {cls.DB_PATH}")
            except Exception as e:
                logger.error(f"[GEOIP] Failed to load GeoIP database: {e}")
        return cls._reader
    
    @classmethod
    def get_location(cls, ip_address: str) -> Dict[str, Optional[str]]:
        """
        Get location information from IP address
        
        Args:
            ip_address: IP address string (IPv4 or IPv6)
            
        Returns:
            Dict with city, region, country, lat, lon
        """
        default_response = {
            'city': None,
            'region': None,
            'country': None,
            'lat': None,
            'lon': None,
            'is_private': False
        }
        
        if not ip_address:
            return default_response
        
        # Check if IP is private/local
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
                logger.debug(f"[GEOIP] Private/local IP detected: {ip_address}")
                return {
                    **default_response,
                    'city': 'Local Network',
                    'country': 'Local',
                    'is_private': True
                }
        except ValueError:
            logger.warning(f"[GEOIP] Invalid IP address format: {ip_address}")
            return default_response
        
        # Try to get location from GeoIP database
        reader = cls._get_reader()
        if not reader:
            logger.debug(f"[GEOIP] GeoIP reader not available, using fallback")
            return cls._fallback_lookup(ip_address)
        
        try:
            response = reader.city(ip_address)
            
            city = response.city.name if response.city.name else None
            region = response.subdivisions.most_specific.name if response.subdivisions.most_specific.name else None
            country = response.country.name if response.country.name else None
            lat = response.location.latitude if response.location.latitude else None
            lon = response.location.longitude if response.location.longitude else None
            
            logger.debug(f"[GEOIP] Location for {ip_address}: {city}, {country}")
            
            return {
                'city': city,
                'region': region,
                'country': country,
                'lat': lat,
                'lon': lon,
                'is_private': False
            }
            
        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"[GEOIP] IP address not found in database: {ip_address}")
            return cls._fallback_lookup(ip_address)
        except Exception as e:
            logger.error(f"[GEOIP] Error looking up IP {ip_address}: {e}")
            return cls._fallback_lookup(ip_address)
    
    @classmethod
    def _fallback_lookup(cls, ip_address: str) -> Dict[str, Optional[str]]:
        """
        Fallback to free IP-API service if GeoIP database fails
        Only used as last resort to avoid external dependencies
        """
        try:
            import requests
            url = f"http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city,lat,lon"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    logger.debug(f"[GEOIP] Fallback lookup successful for {ip_address}")
                    return {
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'country': data.get('country'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'is_private': False
                    }
        except Exception as e:
            logger.error(f"[GEOIP] Fallback lookup failed: {e}")
        
        return {
            'city': None,
            'region': None,
            'country': None,
            'lat': None,
            'lon': None,
            'is_private': False
        }
    
    @classmethod
    def format_location(cls, location_data: Dict) -> str:
        """
        Format location data into a human-readable string
        
        Args:
            location_data: Dict from get_location()
            
        Returns:
            Formatted location string (e.g., "San Francisco, CA, United States")
        """
        if location_data.get('is_private'):
            return "Local Network"
        
        parts = []
        if location_data.get('city'):
            parts.append(location_data['city'])
        if location_data.get('region'):
            parts.append(location_data['region'])
        if location_data.get('country'):
            parts.append(location_data['country'])
        
        if parts:
            return ", ".join(parts)
        return "Unknown Location"
    
    @classmethod
    def close(cls):
        """Close the GeoIP reader"""
        if cls._reader:
            cls._reader.close()
            cls._reader = None


# Example usage and testing
if __name__ == "__main__":
    test_ips = [
        "8.8.8.8",  # Google DNS
        "1.1.1.1",  # Cloudflare DNS
        "127.0.0.1",  # Localhost
        "192.168.1.1",  # Private IP
        "2001:4860:4860::8888",  # Google DNS IPv6
    ]
    
    geoip = IPGeolocation()
    
    for ip in test_ips:
        location = geoip.get_location(ip)
        formatted = geoip.format_location(location)
        print(f"\nIP: {ip}")
        print(f"Location: {formatted}")
        print(f"Details: {location}")
    
    geoip.close()
