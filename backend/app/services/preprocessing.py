from bs4 import BeautifulSoup
import re
import spacy
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Load spaCy model for NER
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

# Indian stock ticker patterns
TICKER_PATTERNS = [
    r'\b([A-Z]{2,5})\.NS\b',  # NSE format (e.g., INFY.NS)
    r'\b([A-Z]{2,5})\.BO\b',  # BSE format (e.g., INFY.BO)
    r'\b([A-Z]{3,5})\b(?=\s+(?:stock|shares|traded|trading))',  # Context-based
]

# Common Indian defense stocks
DEFENSE_TICKERS = {
    "HAL": "Hindustan Aeronautics Limited",
    "BEL": "Bharat Electronics Limited",
    "BDL": "Bharat Dynamics Limited",
    "MDL": "Mazagon Dock Shipbuilders",
    "GRSE": "Garden Reach Shipbuilders",
    "BEML": "BEML Limited"
}

# Financial keywords
FINANCIAL_KEYWORDS = [
    "earnings", "revenue", "profit", "loss", "growth", "quarter", "Q1", "Q2", "Q3", "Q4",
    "FY", "market cap", "shares", "stock", "trading", "volume", "bullish", "bearish",
    "analyst", "rating", "upgrade", "downgrade", "buy", "sell", "hold", "target price",
    "dividend", "EPS", "P/E", "valuation", "IPO", "merger", "acquisition", "contract",
    "order", "defense", "sector", "index", "NSE", "BSE", "Sensex", "Nifty"
]


class PreprocessingService:
    """Service for preprocessing text data."""
    
    def __init__(self):
        """Initialize preprocessing service."""
        self.max_chunk_size = 512  # tokens
    
    def clean_html(self, html_content: str) -> str:
        """Remove HTML tags and clean text."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=' ')
            
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return html_content
    
    def chunk_text(self, text: str, max_words: int = 400) -> List[str]:
        """
        Split long text into chunks.
        
        Args:
            text: Text to chunk
            max_words: Maximum words per chunk
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        return chunks
    
    def extract_tickers(self, text: str) -> List[str]:
        """
        Extract stock ticker symbols from text.
        
        Args:
            text: Text to extract tickers from
            
        Returns:
            List of unique ticker symbols
        """
        tickers = set()
        
        # Check for known defense tickers
        for ticker in DEFENSE_TICKERS.keys():
            if re.search(r'\b' + ticker + r'\b', text, re.IGNORECASE):
                tickers.add(ticker)
        
        # Extract using patterns
        for pattern in TICKER_PATTERNS:
            matches = re.findall(pattern, text)
            tickers.update(matches)
        
        # Use NER if available
        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    # Check if organization name matches known ticker
                    org_name = ent.text.upper()
                    for ticker, full_name in DEFENSE_TICKERS.items():
                        if ticker in org_name or org_name in full_name.upper():
                            tickers.add(ticker)
        
        return list(tickers)
    
    def extract_financial_keywords(self, text: str) -> List[str]:
        """
        Extract financial keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of found keywords
        """
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in FINANCIAL_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def extract_metadata(self, text: str, source: str = "") -> Dict[str, Any]:
        """
        Extract comprehensive metadata from text.
        
        Args:
            text: Text to process
            source: Source of the text
            
        Returns:
            Metadata dictionary
        """
        return {
            "tickers": self.extract_tickers(text),
            "keywords": self.extract_financial_keywords(text),
            "source": source,
            "word_count": len(text.split()),
            "has_financial_content": len(self.extract_financial_keywords(text)) > 0
        }
    
    def process_article(self, raw_html: str, source: str = "", url: str = "") -> Dict[str, Any]:
        """
        Complete preprocessing pipeline for an article.
        
        Args:
            raw_html: Raw HTML content
            source: Source name
            url: Article URL
            
        Returns:
            Processed article with chunks and metadata
        """
        # Clean HTML
        clean_text = self.clean_html(raw_html)
        
        # Extract metadata
        metadata = self.extract_metadata(clean_text, source)
        metadata["url"] = url
        
        # Chunk if needed
        if len(clean_text.split()) > 400:
            chunks = self.chunk_text(clean_text)
        else:
            chunks = [clean_text]
        
        return {
            "clean_text": clean_text,
            "chunks": chunks,
            "metadata": metadata
        }


# Global instance
preprocessing_service = PreprocessingService()
