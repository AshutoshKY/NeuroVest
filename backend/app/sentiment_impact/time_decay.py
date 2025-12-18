"""
Time Decay Calculator
Calculates how sentiment impact decays over time
"""

from datetime import datetime, timedelta
import math


def calculate_time_decay(
    published_at: datetime,
    current_time: datetime = None,
    half_life_hours: float = 24.0
) -> float:
    """
    Calculate time decay factor using exponential decay
    
    Formula: decay = 0.5^(hours_elapsed / half_life)
    
    Args:
        published_at: When news was published
        current_time: Current time (default: now)
        half_life_hours: Hours for impact to decay to 50%
        
    Returns:
        Decay factor (0.0-1.0)
        - 1.0 = just published
        - 0.5 = published half_life_hours ago
        - 0.25 = published 2*half_life_hours ago
        
    Example:
        News from 24h ago with half_life=24h → 0.5
        News from 48h ago with half_life=24h → 0.25
        News from 1h ago with half_life=24h → 0.97
    """
    
    if current_time is None:
        current_time = datetime.utcnow()
    
    # Ensure both are timezone-aware or both naive
    if published_at.tzinfo is not None and current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=published_at.tzinfo)
    elif published_at.tzinfo is None and current_time.tzinfo is not None:
        published_at = published_at.replace(tzinfo=current_time.tzinfo)
    
    # Calculate hours elapsed
    time_diff = current_time - published_at
    hours_elapsed = time_diff.total_seconds() / 3600
    
    # Handle negative time (future news - shouldn't happen but handle gracefully)
    if hours_elapsed < 0:
        return 1.0
    
    # Calculate exponential decay
    decay_factor = math.pow(0.5, hours_elapsed / half_life_hours)
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, decay_factor))


def get_decay_half_life(impact_level: str) -> float:
    """
    Get appropriate half-life based on impact level
    
    Major news: 48h half-life (decays slower)
    Moderate news: 24h half-life
    Minor news: 12h half-life (decays faster)
    """
    
    half_lives = {
        "major": 48.0,
        "moderate": 24.0,
        "minor": 12.0
    }
    
    return half_lives.get(impact_level, 24.0)
