"""
Factory for loading and managing scrapers from configuration.
"""
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any
from app.scrapers.generic_scraper import GenericScraper
from app.scrapers.rss_scraper import RSSScraper

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory for creating scrapers from YAML configuration."""
    
    @staticmethod
    def load_config(config_path: str = 'config/sources.yaml') -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            config_file = Path(config_path)
            
            if not config_file.exists():
                logger.warning(f"Config file not found: {config_path}, using defaults")
                return {'data_sources': {'news_scrapers': [], 'stock_apis': []}}
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"✅ Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {'data_sources': {'news_scrapers': [], 'stock_apis': []}}
    
    @staticmethod
    def create_scrapers(config_path: str = 'config/sources.yaml') -> List[GenericScraper]:
        """
        Create scraper instances from configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            List of scraper instances
        """
        scrapers = []
        config = ScraperFactory.load_config(config_path)
        
        news_scrapers = config.get('data_sources', {}).get('news_scrapers', [])
        
        for scraper_config in news_scrapers:
            try:
                if not scraper_config.get('enabled', False):
                    logger.info(f"⏸️ Skipping disabled scraper: {scraper_config['name']}")
                    continue
                
                scraper_type = scraper_config.get('type', 'html')
                
                if scraper_type == 'rss':
                    scraper = RSSScraper(scraper_config)
                else:
                    scraper = GenericScraper(scraper_config)
                
                scrapers.append(scraper)
                
                logger.info(f"✅ Loaded scraper: {scraper_config['name']} ({scraper_type})")
                
            except Exception as e:
                logger.error(f"❌ Failed to create scraper for {scraper_config.get('name', 'unknown')}: {e}")
                continue
        
        logger.info(f"📊 Loaded {len(scrapers)}/{len(news_scrapers)} scrapers from config")
        return scrapers
    
    @staticmethod
    def get_api_configs(config_path: str = 'config/sources.yaml') -> List[Dict[str, Any]]:
        """
        Get stock API configurations.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            List of API configuration dictionaries
        """
        config = ScraperFactory.load_config(config_path)
        stock_apis = config.get('data_sources', {}).get('stock_apis', [])
        
        # Filter enabled APIs and sort by priority
        enabled_apis = [api for api in stock_apis if api.get('enabled', False)]
        enabled_apis.sort(key=lambda x: x.get('priority', 999))
        
        logger.info(f"📡 Loaded {len(enabled_apis)}/{len(stock_apis)} stock APIs from config")
        
        return enabled_apis
    
    @staticmethod
    def test_all_scrapers(config_path: str = 'config/sources.yaml') -> Dict[str, Any]:
        """
        Test all configured scrapers to verify selectors work.
        Useful for validating configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dictionary with test results for each scraper
        """
        scrapers = ScraperFactory.create_scrapers(config_path)
        results = {}
        
        for scraper in scrapers:
            logger.info(f"🧪 Testing scraper: {scraper.name}")
            results[scraper.name] = scraper.test_selectors()
        
        return results


# Convenience function for quick loading
def load_scrapers() -> List[GenericScraper]:
    """Load all enabled scrapers from default config location."""
    return ScraperFactory.create_scrapers()


def load_api_configs() -> List[Dict[str, Any]]:
    """Load all enabled API configs from default location."""
    return ScraperFactory.get_api_configs()
