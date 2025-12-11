"""
Device Parser Utility
Extracts device information from User-Agent strings
"""
from user_agents import parse
from typing import Dict, Optional
from loguru import logger


class DeviceParser:
    """Parse User-Agent strings to extract device information"""
    
    @staticmethod
    def parse_user_agent(user_agent_string: Optional[str]) -> Dict[str, str]:
        """
        Parse user agent string and extract device information
        
        Args:
            user_agent_string: Raw User-Agent header value
            
        Returns:
            Dict with device_type, os, browser, device_name
        """
        if not user_agent_string:
            return {
                'device_type': 'Unknown',
                'os': 'Unknown',
                'browser': 'Unknown',
                'device_name': 'Unknown Device'
            }
        
        try:
            ua = parse(user_agent_string)
            
            # Determine device type
            if ua.is_mobile:
                device_type = 'Mobile'
            elif ua.is_tablet:
                device_type = 'Tablet'
            elif ua.is_pc:
                device_type = 'Desktop'
            elif ua.is_bot:
                device_type = 'Bot'
            else:
                device_type = 'Unknown'
            
            # Get OS with version
            os_name = ua.os.family if ua.os.family else 'Unknown'
            os_version = ua.os.version_string if ua.os.version_string else ''
            os_full = f"{os_name} {os_version}".strip() if os_version else os_name
            
            # Get browser with version
            browser_name = ua.browser.family if ua.browser.family else 'Unknown'
            browser_version = '.'.join(str(v) for v in ua.browser.version[:2] if v is not None) if ua.browser.version else ''
            browser_full = f"{browser_name} {browser_version}".strip() if browser_version else browser_name
            
            # Generate friendly device name
            device_name = DeviceParser._generate_device_name(ua, device_type)
            
            return {
                'device_type': device_type,
                'os': os_full,
                'browser': browser_full,
                'device_name': device_name
            }
            
        except Exception as e:
            logger.error(f"[DEVICE_PARSER] Error parsing user agent: {e}")
            return {
                'device_type': 'Unknown',
                'os': 'Unknown',
                'browser': 'Unknown',
                'device_name': 'Unknown Device'
            }
    
    @staticmethod
    def _generate_device_name(ua, device_type: str) -> str:
        """Generate a friendly device name"""
        try:
            # For mobile devices, try to get device brand/model
            if device_type == 'Mobile':
                brand = ua.device.brand if ua.device.brand else ''
                model = ua.device.model if ua.device.model else ''
                
                if brand and model:
                    return f"{brand} {model}"
                elif model:
                    return model
                elif brand:
                    return f"{brand} Phone"
                else:
                    # Use OS as fallback
                    os_name = ua.os.family if ua.os.family else 'Mobile'
                    return f"{os_name} Phone"
            
            # For tablets
            elif device_type == 'Tablet':
                brand = ua.device.brand if ua.device.brand else ''
                model = ua.device.model if ua.device.model else ''
                
                if brand and model:
                    return f"{brand} {model}"
                elif model:
                    return model
                else:
                    os_name = ua.os.family if ua.os.family else 'Tablet'
                    return f"{os_name} Tablet"
            
            # For desktop/PC
            elif device_type == 'Desktop':
                os_name = ua.os.family if ua.os.family else 'Desktop'
                if 'Windows' in os_name:
                    return 'Windows PC'
                elif 'Mac' in os_name or 'OS X' in os_name:
                    return 'Mac'
                elif 'Linux' in os_name:
                    return 'Linux PC'
                elif 'Chrome OS' in os_name:
                    return 'Chromebook'
                else:
                    return f"{os_name} Computer"
            
            # For bots
            elif device_type == 'Bot':
                browser = ua.browser.family if ua.browser.family else 'Bot'
                return f"{browser} Bot"
            
            else:
                return 'Unknown Device'
                
        except Exception as e:
            logger.error(f"[DEVICE_PARSER] Error generating device name: {e}")
            return 'Unknown Device'


# Example usage and testing
if __name__ == "__main__":
    test_user_agents = [
        # iPhone
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        # Android
        "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
        # Windows PC
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        # Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        # iPad
        "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    ]
    
    for ua_string in test_user_agents:
        result = DeviceParser.parse_user_agent(ua_string)
        print(f"\nUA: {ua_string[:80]}...")
        print(f"Result: {result}")
