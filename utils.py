"""
Utility functions for the CRE Agent system.
"""
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger('cre_agent')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
    
    return logger


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to check/create
    """
    os.makedirs(directory, exist_ok=True)


def save_json(data: Any, filepath: str, pretty: bool = True) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filepath: Output file path
        pretty: Whether to pretty-print the JSON
    """
    ensure_directory_exists(os.path.dirname(filepath))
    
    with open(filepath, 'w') as f:
        if pretty:
            json.dump(data, f, indent=2, default=str)
        else:
            json.dump(data, f, default=str)


def load_json(filepath: str) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Input file path
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def format_currency(amount: Optional[float], currency: str = 'USD') -> str:
    """
    Format a number as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if amount is None:
        return 'N/A'
    
    if currency == 'USD':
        return f'${amount:,.0f}'
    else:
        return f'{amount:,.0f} {currency}'


def format_area(sqft: Optional[float]) -> str:
    """
    Format square footage.
    
    Args:
        sqft: Square footage
        
    Returns:
        Formatted area string
    """
    if sqft is None:
        return 'N/A'
    return f'{sqft:,.0f} sq ft'


def format_percentage(value: Optional[float], decimals: int = 1) -> str:
    """
    Format a number as a percentage.
    
    Args:
        value: Value to format (0-1 range)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return 'N/A'
    return f'{value * 100:.{decimals}f}%'


def parse_location_string(location: str) -> Dict[str, str]:
    """
    Parse a location string into components.
    
    Args:
        location: Location string (e.g., "newark-nj", "seattle-wa")
        
    Returns:
        Dictionary with city and state components
    """
    parts = location.lower().split('-')
    
    if len(parts) >= 2:
        state = parts[-1].upper()
        city = ' '.join(parts[:-1]).title()
        return {'city': city, 'state': state}
    else:
        return {'city': location.title(), 'state': ''}


def calculate_price_per_sqft(price: Optional[float], sqft: Optional[float]) -> Optional[float]:
    """
    Calculate price per square foot.
    
    Args:
        price: Property price
        sqft: Square footage
        
    Returns:
        Price per square foot, or None if calculation not possible
    """
    if price and sqft and sqft > 0:
        return price / sqft
    return None


def calculate_price_per_unit(price: Optional[float], units: Optional[int]) -> Optional[float]:
    """
    Calculate price per unit (for multifamily).
    
    Args:
        price: Property price
        units: Number of units
        
    Returns:
        Price per unit, or None if calculation not possible
    """
    if price and units and units > 0:
        return price / units
    return None


def get_days_difference(date1: datetime, date2: datetime) -> int:
    """
    Calculate days between two dates.
    
    Args:
        date1: First date
        date2: Second date
        
    Returns:
        Number of days difference
    """
    return abs((date2 - date1).days)


def is_recent_listing(days_on_market: int, threshold: int = 30) -> bool:
    """
    Check if a listing is recent.
    
    Args:
        days_on_market: Days the listing has been on market
        threshold: Threshold for "recent" in days
        
    Returns:
        True if listing is recent
    """
    return days_on_market <= threshold


def is_stale_listing(days_on_market: int, threshold: int = 180) -> bool:
    """
    Check if a listing is stale.
    
    Args:
        days_on_market: Days the listing has been on market
        threshold: Threshold for "stale" in days
        
    Returns:
        True if listing is stale
    """
    return days_on_market >= threshold


def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> bool:
    """
    Validate geographic coordinates.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        
    Returns:
        True if coordinates are valid
    """
    if latitude is None or longitude is None:
        return False
    
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def extract_numbers_from_string(text: str) -> List[float]:
    """
    Extract all numbers from a string.
    
    Args:
        text: Input text
        
    Returns:
        List of numbers found in the text
    """
    import re
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches]


def clean_string(text: Optional[str]) -> str:
    """
    Clean and normalize a string.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ''
    
    # Remove extra whitespace
    import re
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def batch_list(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split a list into batches.
    
    Args:
        items: List to batch
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def merge_dicts(dict1: Dict, dict2: Dict, prefer_dict2: bool = True) -> Dict:
    """
    Merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        prefer_dict2: If True, values from dict2 override dict1
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, prefer_dict2)
        elif prefer_dict2 or key not in result:
            result[key] = value
    
    return result


def get_nested_value(data: Dict, key_path: str, default: Any = None) -> Any:
    """
    Get a value from a nested dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated path (e.g., "address.street")
        default: Default value if key not found
        
    Returns:
        Value at the key path, or default
    """
    keys = key_path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def calculate_variance(value1: float, value2: float) -> float:
    """
    Calculate percentage variance between two values.
    
    Args:
        value1: First value
        value2: Second value
        
    Returns:
        Variance as a decimal (0.1 = 10%)
    """
    if value1 == 0 and value2 == 0:
        return 0.0
    
    max_val = max(abs(value1), abs(value2))
    if max_val == 0:
        return 0.0
    
    return abs(value1 - value2) / max_val


class ProgressTracker:
    """Simple progress tracker for batch operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, increment: int = 1) -> None:
        """Update progress."""
        self.current += increment
        self._print_progress()
    
    def _print_progress(self) -> None:
        """Print current progress."""
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        bar_length = 40
        filled = int(bar_length * self.current / self.total) if self.total > 0 else 0
        bar = '=' * filled + '-' * (bar_length - filled)
        
        print(f'\r{self.description}: [{bar}] {percentage:.1f}% ({self.current}/{self.total})', end='')
        
        if self.current >= self.total:
            print()  # New line when complete


if __name__ == "__main__":
    # Test utilities
    print("Testing utility functions...")
    
    print(f"\nCurrency: {format_currency(1500000)}")
    print(f"Area: {format_area(2500)}")
    print(f"Percentage: {format_percentage(0.156)}")
    print(f"Location: {parse_location_string('newark-nj')}")
    print(f"Price/sqft: ${calculate_price_per_sqft(1500000, 2500):.2f}")
    
    # Test progress tracker
    print("\nProgress tracker test:")
    tracker = ProgressTracker(10, "Loading")
    for i in range(10):
        import time
        time.sleep(0.1)
        tracker.update()
