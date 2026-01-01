"""
Configuration settings for the CRE Agent system.

Modify these settings to customize the system behavior.
"""
from typing import List


class InvestmentMandateConfig:
    """Investment criteria for property classification."""
    
    # Allowed property types
    ALLOWED_PROPERTY_TYPES: List[str] = [
        'MULTIFAMILY',
        'OFFICE',
        'RETAIL',
        'INDUSTRIAL',
        'MIXED-USE'
    ]
    
    # Price range (in USD)
    MIN_PRICE: int = 100_000
    MAX_PRICE: int = 50_000_000
    
    # Market activity thresholds
    MAX_DAYS_ON_MARKET: int = 365
    MIN_DAYS_ON_MARKET: int = 0
    
    # Size thresholds (square feet)
    MIN_SQUARE_FEET: int = 0
    MAX_SQUARE_FEET: int = 1_000_000
    
    # Geographic constraints
    ALLOWED_STATES: List[str] = []  # Empty = all states allowed
    EXCLUDED_STATES: List[str] = []
    
    # Target cities (if specified, only these cities will be considered)
    TARGET_CITIES: List[str] = []  # Empty = all cities allowed


class PropertyMatchingConfig:
    """Configuration for cross-platform property matching."""
    
    # Match score weights (must sum to 1.0)
    ADDRESS_WEIGHT: float = 0.40
    LOCATION_WEIGHT: float = 0.20
    PROPERTY_TYPE_WEIGHT: float = 0.15
    SIZE_WEIGHT: float = 0.15
    PRICE_WEIGHT: float = 0.10
    
    # Match thresholds
    AUTO_MATCH_THRESHOLD: float = 0.85  # Automatic match
    MANUAL_REVIEW_THRESHOLD: float = 0.70  # Requires review
    # Below manual review = separate properties
    
    # Variance tolerances for numeric fields
    SIZE_VARIANCE_THRESHOLD: float = 0.15  # 15%
    PRICE_VARIANCE_THRESHOLD: float = 0.20  # 20%
    LOT_SIZE_VARIANCE_THRESHOLD: float = 0.10  # 10%


class DataConsolidationConfig:
    """Configuration for data consolidation and conflict resolution."""
    
    # Platform precedence (higher = higher priority)
    PLATFORM_PRECEDENCE = {
        'crexi': 4,
        'loopnet': 3,
        'realtor': 2,
        'zillow': 1
    }
    
    # Variance thresholds for conflict detection
    NUMERIC_VARIANCE_THRESHOLD: float = 0.05  # 5%
    
    # Fields that are considered volatile (update frequently)
    VOLATILE_FIELDS: List[str] = [
        'price',
        'status',
        'daysOnMarket',
        'daysOnZillow'
    ]
    
    # Fields that are considered immutable
    IMMUTABLE_FIELDS: List[str] = [
        'yearBuilt',
        'parcelId',
        'lotSize'
    ]


class ZillowAgentConfig:
    """Configuration specific to Zillow agent."""
    
    # Default search parameters
    DEFAULT_MAX_PAGES: int = 5
    DEFAULT_RESULTS_PER_PAGE: int = 40
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    DELAY_BETWEEN_REQUESTS: float = 1.0  # seconds
    
    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 5.0  # seconds
    
    # Data extraction settings
    EXTRACT_ALL_FIELDS: bool = True
    PRESERVE_URLS: bool = True
    DOWNLOAD_IMAGES: bool = False  # Set to True to download property images


class CacheConfig:
    """Configuration for caching layer."""
    
    # Cache durations (in days)
    IMMUTABLE_CACHE_DAYS: int = 365  # 1 year
    SEMI_MUTABLE_CACHE_DAYS: int = 90  # 3 months
    VOLATILE_CACHE_DAYS: int = 1  # 1 day
    
    # Cache invalidation triggers
    INVALIDATE_ON_PRICE_CHANGE: bool = True
    INVALIDATE_ON_STATUS_CHANGE: bool = True
    INVALIDATE_ON_OWNERSHIP_CHANGE: bool = True


class OutputConfig:
    """Configuration for output formatting and storage."""
    
    # Output directories
    RAW_LISTINGS_DIR: str = "data/raw"
    CONSOLIDATED_DIR: str = "data/consolidated"
    VERIFIED_DIR: str = "data/verified"
    REPORTS_DIR: str = "data/reports"
    
    # File formats
    USE_JSON: bool = True
    USE_CSV: bool = False
    PRETTY_PRINT_JSON: bool = True
    JSON_INDENT: int = 2
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE: bool = True
    LOG_FILE: str = "data/logs/cre_agent.log"
    
    # Report generation
    GENERATE_SUMMARY_REPORT: bool = True
    GENERATE_CONFLICT_REPORT: bool = True
    GENERATE_DISCARD_REPORT: bool = True


class GovernmentRecordsConfig:
    """Configuration for government records verification (future)."""
    
    # Data sources to use
    USE_COUNTY_ASSESSOR: bool = True
    USE_COUNTY_RECORDER: bool = True
    USE_STATE_RECORDS: bool = True
    USE_COMMERCIAL_AGGREGATORS: bool = False
    
    # Verification thresholds
    MIN_VERIFICATION_CONFIDENCE: float = 0.80
    
    # Discrepancy tolerances
    MINOR_DISCREPANCY_THRESHOLD: float = 0.10  # 10%
    MATERIAL_DISCREPANCY_THRESHOLD: float = 0.20  # 20%


# Convenience function to export all configs as dict
def get_all_configs() -> dict:
    """Get all configuration settings as a dictionary."""
    return {
        'investment_mandate': {
            k: v for k, v in vars(InvestmentMandateConfig).items()
            if not k.startswith('_')
        },
        'property_matching': {
            k: v for k, v in vars(PropertyMatchingConfig).items()
            if not k.startswith('_')
        },
        'data_consolidation': {
            k: v for k, v in vars(DataConsolidationConfig).items()
            if not k.startswith('_')
        },
        'zillow_agent': {
            k: v for k, v in vars(ZillowAgentConfig).items()
            if not k.startswith('_')
        },
        'cache': {
            k: v for k, v in vars(CacheConfig).items()
            if not k.startswith('_')
        },
        'output': {
            k: v for k, v in vars(OutputConfig).items()
            if not k.startswith('_')
        },
        'government_records': {
            k: v for k, v in vars(GovernmentRecordsConfig).items()
            if not k.startswith('_')
        }
    }


if __name__ == "__main__":
    # Print current configuration
    import json
    configs = get_all_configs()
    print(json.dumps(configs, indent=2, default=str))
