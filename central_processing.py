"""
Central Processing and Normalization Node.

This module handles:
- Identity resolution across platforms
- Data consolidation and conflict resolution
- Property classification (usable, flagged, discarded)
- Address normalization
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
from models import RawListingRecord, ConsolidatedProperty


class AddressNormalizer:
    """Normalize and standardize addresses for matching."""
    
    # Common street suffix abbreviations
    STREET_SUFFIXES = {
        'ST': 'STREET',
        'AVE': 'AVENUE',
        'BLVD': 'BOULEVARD',
        'DR': 'DRIVE',
        'RD': 'ROAD',
        'LN': 'LANE',
        'CT': 'COURT',
        'PL': 'PLACE',
        'TER': 'TERRACE',
        'WAY': 'WAY',
        'CIR': 'CIRCLE',
        'PKWY': 'PARKWAY'
    }
    
    # Directional abbreviations
    DIRECTIONALS = {
        'N': 'NORTH',
        'S': 'SOUTH',
        'E': 'EAST',
        'W': 'WEST',
        'NE': 'NORTHEAST',
        'NW': 'NORTHWEST',
        'SE': 'SOUTHEAST',
        'SW': 'SOUTHWEST'
    }
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """
        Normalize an address string for matching.
        
        Args:
            address: Raw address string
            
        Returns:
            Normalized address string
        """
        if not address:
            return ""
        
        # Convert to uppercase
        addr = address.upper().strip()
        
        # Remove extra whitespace
        addr = re.sub(r'\s+', ' ', addr)
        
        # Remove punctuation except hyphens
        addr = re.sub(r'[^\w\s\-]', '', addr)
        
        # Expand street suffixes
        for abbr, full in AddressNormalizer.STREET_SUFFIXES.items():
            addr = re.sub(rf'\b{abbr}\b', full, addr)
        
        # Expand directionals
        for abbr, full in AddressNormalizer.DIRECTIONALS.items():
            addr = re.sub(rf'\b{abbr}\b', full, addr)
        
        # Remove leading zeros from street numbers
        addr = re.sub(r'\b0+(\d+)\b', r'\1', addr)
        
        # Normalize unit designations
        addr = re.sub(r'\b(UNIT|APT|SUITE|STE|#)\s*', 'UNIT ', addr)
        
        return addr.strip()
    
    @staticmethod
    def extract_address_components(address: str) -> Dict[str, str]:
        """
        Extract components from an address string.
        
        Args:
            address: Address string (e.g., "123 Main Street, Seattle, WA 98101")
            
        Returns:
            Dictionary with address components
        """
        parts = [p.strip() for p in address.split(',')]
        
        components = {
            'full_address': address,
            'street': '',
            'city': '',
            'state': '',
            'zip': ''
        }
        
        if len(parts) >= 1:
            components['street'] = parts[0]
        if len(parts) >= 2:
            components['city'] = parts[1]
        if len(parts) >= 3:
            # Try to extract state and ZIP
            state_zip = parts[2].strip()
            state_zip_match = re.match(r'([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?', state_zip)
            if state_zip_match:
                components['state'] = state_zip_match.group(1)
                if state_zip_match.group(2):
                    components['zip'] = state_zip_match.group(2)
        
        return components


class PropertyMatcher:
    """Match properties across different listing platforms."""
    
    @staticmethod
    def calculate_match_score(
        listing1: Dict[str, Any],
        listing2: Dict[str, Any]
    ) -> float:
        """
        Calculate match confidence score between two listings.
        
        Match Score = 
          (Address Match × 0.40) +
          (City/State/ZIP Match × 0.20) +
          (Property Type Match × 0.15) +
          (Size Match × 0.15) +
          (Price Range Match × 0.10)
        
        Args:
            listing1: First listing dict
            listing2: Second listing dict
            
        Returns:
            Match score between 0 and 1
        """
        score = 0.0
        
        # Address match (40%)
        # Handle both old ('address') and new ('address_full') field names
        addr1 = AddressNormalizer.normalize_address(
            listing1.get('address_full') or listing1.get('address', '')
        )
        addr2 = AddressNormalizer.normalize_address(
            listing2.get('address_full') or listing2.get('address', '')
        )
        
        if addr1 and addr2:
            # Simple string similarity (can be enhanced with fuzzy matching)
            if addr1 == addr2:
                score += 0.40
            elif addr1 in addr2 or addr2 in addr1:
                score += 0.30
        
        # City/State/ZIP match (20%)
        # Try new structure first (address_city, address_state, address_zip)
        # Fall back to extracting from full address
        city1 = listing1.get('address_city') or ''
        city2 = listing2.get('address_city') or ''
        state1 = listing1.get('address_state') or ''
        state2 = listing2.get('address_state') or ''
        zip1 = listing1.get('address_zip') or ''
        zip2 = listing2.get('address_zip') or ''
        
        # If not found, extract from full address
        if not city1 or not state1:
            comp1 = AddressNormalizer.extract_address_components(
                listing1.get('address_full') or listing1.get('address', '')
            )
            city1 = city1 or comp1['city']
            state1 = state1 or comp1['state']
            zip1 = zip1 or comp1['zip']
        
        if not city2 or not state2:
            comp2 = AddressNormalizer.extract_address_components(
                listing2.get('address_full') or listing2.get('address', '')
            )
            city2 = city2 or comp2['city']
            state2 = state2 or comp2['state']
            zip2 = zip2 or comp2['zip']
        
        location_match = 0
        if city1 and city2 and city1.upper() == city2.upper():
            location_match += 0.07
        if state1 and state2 and state1.upper() == state2.upper():
            location_match += 0.07
        if zip1 and zip2 and zip1 == zip2:
            location_match += 0.06
        score += location_match
        
        # Property type match (15%)
        # Note: This is simplified - actual implementation should map various property types
        type1 = listing1.get('homeType') or listing1.get('property_type', '')
        type2 = listing2.get('homeType') or listing2.get('property_type', '')
        type1 = type1.upper() if type1 else ''
        type2 = type2.upper() if type2 else ''
        if type1 and type2 and type1 == type2:
            score += 0.15
        
        # Size match (15%)
        size1 = listing1.get('area') or listing1.get('square_feet') or listing1.get('sqft')
        size2 = listing2.get('area') or listing2.get('square_feet') or listing2.get('sqft')
        
        if size1 and size2:
            try:
                size1, size2 = float(size1), float(size2)
                variance = abs(size1 - size2) / max(size1, size2)
                if variance < 0.05:  # Within 5%
                    score += 0.15
                elif variance < 0.10:  # Within 10%
                    score += 0.10
                elif variance < 0.15:  # Within 15%
                    score += 0.05
            except (ValueError, ZeroDivisionError):
                pass
        
        # Price range match (10%)
        # Handle both unformattedPrice (new) and price (old)
        price1 = listing1.get('unformattedPrice') or listing1.get('price')
        price2 = listing2.get('unformattedPrice') or listing2.get('price')
        
        if price1 and price2:
            try:
                price1, price2 = float(price1), float(price2)
                variance = abs(price1 - price2) / max(price1, price2)
                if variance < 0.05:  # Within 5%
                    score += 0.10
                elif variance < 0.20:  # Within 20%
                    score += 0.05
            except (ValueError, ZeroDivisionError):
                pass
        
        return score
    
    @staticmethod
    def is_match(
        listing1: Dict[str, Any],
        listing2: Dict[str, Any],
        threshold: float = 0.70
    ) -> Tuple[bool, float]:
        """
        Determine if two listings represent the same property.
        
        Args:
            listing1: First listing
            listing2: Second listing
            threshold: Minimum score to consider a match
            
        Returns:
            Tuple of (is_match, score)
        """
        score = PropertyMatcher.calculate_match_score(listing1, listing2)
        return (score >= threshold, score)


class DataConsolidator:
    """Consolidate data from multiple listings of the same property."""
    
    @staticmethod
    def get_field_precedence(
        field_name: str,
        listings: List[Dict[str, Any]]
    ) -> Any:
        """
        Determine the best value for a field based on precedence rules.
        
        Priority order:
        1. Most recently updated listing
        2. Listing with most complete data
        3. Platform with highest historical accuracy (could be configurable)
        
        Args:
            field_name: Name of the field
            listings: List of listing dicts
            
        Returns:
            Best value for the field
        """
        # Filter listings that have this field
        candidates = [l for l in listings if field_name in l.get('raw_fields', {})]
        
        if not candidates:
            return None
        
        # Sort by extraction timestamp (most recent first)
        sorted_listings = sorted(
            candidates,
            key=lambda x: x.get('extraction_timestamp', datetime.min),
            reverse=True
        )
        
        # Return value from most recent listing
        return sorted_listings[0].get('raw_fields', {}).get(field_name)
    
    @staticmethod
    def detect_conflicts(
        field_name: str,
        listings: List[Dict[str, Any]],
        variance_threshold: float = 0.05
    ) -> Optional[Dict[str, Any]]:
        """
        Detect conflicts in a field across listings.
        
        Args:
            field_name: Field to check
            listings: List of listing dicts
            variance_threshold: Acceptable variance for numeric fields
            
        Returns:
            Conflict dict if conflict exists, None otherwise
        """
        values = []
        for listing in listings:
            val = listing.get('raw_fields', {}).get(field_name)
            if val is not None:
                values.append({
                    'source': listing.get('source_platform'),
                    'value': val
                })
        
        if len(values) <= 1:
            return None
        
        # Check for conflicts
        first_val = values[0]['value']
        
        # For numeric values, check variance
        if isinstance(first_val, (int, float)):
            max_val = max(v['value'] for v in values)
            min_val = min(v['value'] for v in values)
            
            if max_val > 0:
                variance = (max_val - min_val) / max_val
                
                if variance > variance_threshold:
                    return {
                        'field': field_name,
                        'values': values,
                        'variance_percent': variance * 100
                    }
        
        # For string values, check exact match
        else:
            unique_vals = set(str(v['value']) for v in values)
            if len(unique_vals) > 1:
                return {
                    'field': field_name,
                    'values': values,
                    'variance_percent': None
                }
        
        return None


class PropertyClassifier:
    """Classify consolidated properties as usable, flagged, or discarded."""
    
    # Investment mandate criteria (configurable)
    ALLOWED_PROPERTY_TYPES = ['MULTIFAMILY', 'OFFICE', 'RETAIL', 'INDUSTRIAL', 'MIXED-USE']
    MIN_PRICE = 100000
    MAX_PRICE = 50000000
    MAX_DAYS_ON_MARKET = 365
    
    @staticmethod
    def classify_property(consolidated_data: Dict[str, Any]) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        Classify a consolidated property.
        
        Args:
            consolidated_data: Consolidated property data
            
        Returns:
            Tuple of (classification, discard_reason, discard_details)
            classification: 'usable', 'flagged', or 'discarded'
        """
        # Check for critical missing fields
        required_fields = ['address']
        missing_fields = [f for f in required_fields if not consolidated_data.get(f)]
        
        if missing_fields:
            return ('discarded', 'missing_critical_fields', {
                'reason_category': 'incomplete_data',
                'explanation': f"Missing required fields: {', '.join(missing_fields)}",
                'discarded_date': datetime.utcnow().isoformat()
            })
        
        # Check property type (if available)
        # Handle both homeType (new Zillow format) and property_type (generic)
        prop_type = consolidated_data.get('homeType') or consolidated_data.get('property_type', '')
        prop_type = prop_type.upper() if prop_type else ''
        
        # Map Zillow homeType to our standard types
        zillow_type_mapping = {
            'SINGLE_FAMILY': 'SINGLE_FAMILY',  # Usually not CRE, but keep for now
            'MULTI_FAMILY': 'MULTIFAMILY',
            'APARTMENT': 'MULTIFAMILY',
            'CONDO': 'CONDO',
            'TOWNHOUSE': 'TOWNHOUSE',
            'LOT': 'LAND',
            'FARM': 'LAND',
        }
        
        # Apply mapping if it's a Zillow type
        if prop_type in zillow_type_mapping:
            prop_type = zillow_type_mapping[prop_type]
        
        # For now, accept all property types - we can filter later
        # Commercial properties often show up as SINGLE_FAMILY on Zillow
        # if prop_type and prop_type not in PropertyClassifier.ALLOWED_PROPERTY_TYPES:
        #     return ('discarded', 'outside_investment_mandate', {
        #         'reason_category': 'asset_class_mismatch',
        #         'explanation': f"Property type '{prop_type}' outside mandate (focus: {', '.join(PropertyClassifier.ALLOWED_PROPERTY_TYPES)})",
        #         'discarded_date': datetime.utcnow().isoformat()
        #     })
        
        # Check price range - handle both unformattedPrice (new) and price (old)
        price = consolidated_data.get('unformattedPrice') or consolidated_data.get('price')
        if price:
            try:
                # If it's a string, try to extract number
                if isinstance(price, str):
                    # Remove currency symbols and commas
                    import re
                    price = re.sub(r'[^\d.]', '', price)
                
                price = float(price)
                if price < PropertyClassifier.MIN_PRICE or price > PropertyClassifier.MAX_PRICE:
                    return ('discarded', 'outside_investment_mandate', {
                        'reason_category': 'price_out_of_range',
                        'explanation': f"Price ${price:,.0f} outside range (${PropertyClassifier.MIN_PRICE:,.0f} - ${PropertyClassifier.MAX_PRICE:,.0f})",
                        'discarded_date': datetime.utcnow().isoformat()
                    })
            except (ValueError, TypeError):
                pass
        
        # Check days on market
        days_on_market = consolidated_data.get('daysOnZillow') or consolidated_data.get('days_on_market')
        if days_on_market:
            try:
                days_on_market = int(days_on_market)
                if days_on_market > PropertyClassifier.MAX_DAYS_ON_MARKET:
                    return ('flagged', None, None)
            except (ValueError, TypeError):
                pass
        
        # Default to usable
        return ('usable', None, None)


class CentralProcessingNode:
    """
    Central processing and normalization node.
    
    Handles:
    - Address normalization
    - Cross-platform matching
    - Data consolidation
    - Property classification
    """
    
    def __init__(self):
        self.address_normalizer = AddressNormalizer()
        self.property_matcher = PropertyMatcher()
        self.data_consolidator = DataConsolidator()
        self.property_classifier = PropertyClassifier()
    
    def process_listings(
        self,
        raw_listings: List[RawListingRecord]
    ) -> List[ConsolidatedProperty]:
        """
        Process raw listings into consolidated properties.
        
        Args:
            raw_listings: List of raw listing records
            
        Returns:
            List of consolidated property records
        """
        # Convert to dict format for easier processing
        listings_dict = [
            {
                'source_platform': l.source_platform,
                'extraction_timestamp': l.extraction_timestamp,
                'listing_id': l.listing_id_native,
                'raw_fields': l.raw_fields,
                'metadata': l.metadata
            }
            for l in raw_listings
        ]
        
        # Group listings by property (simple approach - can be enhanced)
        property_groups = self._group_listings(listings_dict)
        
        # Consolidate each group
        consolidated_properties = []
        for group_id, group_listings in enumerate(property_groups):
            consolidated = self._consolidate_group(group_id, group_listings)
            consolidated_properties.append(consolidated)
        
        return consolidated_properties
    
    def _group_listings(
        self,
        listings: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Group listings that represent the same property.
        
        Args:
            listings: List of listing dicts
            
        Returns:
            List of listing groups
        """
        groups = []
        processed = set()
        
        for i, listing1 in enumerate(listings):
            if i in processed:
                continue
            
            # Start new group
            group = [listing1]
            processed.add(i)
            
            # Find matches
            for j, listing2 in enumerate(listings[i+1:], start=i+1):
                if j in processed:
                    continue
                
                is_match, score = self.property_matcher.is_match(
                    listing1['raw_fields'],
                    listing2['raw_fields']
                )
                
                if is_match:
                    group.append(listing2)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _consolidate_group(
        self,
        group_id: int,
        group_listings: List[Dict[str, Any]]
    ) -> ConsolidatedProperty:
        """
        Consolidate a group of listings into a single property.
        
        Args:
            group_id: Unique identifier for the group
            group_listings: List of listings in the group
            
        Returns:
            ConsolidatedProperty object
        """
        # Extract common fields - handle both old and new field names
        common_fields = [
            'address', 'address_full', 'address_street', 'address_city', 'address_state', 'address_zip',
            'price', 'unformattedPrice', 'beds', 'baths', 'area', 
            'latitude', 'longitude', 'homeType', 'homeStatus', 'daysOnZillow'
        ]
        
        consolidated_data = {}
        conflicts = []
        
        for field in common_fields:
            # Get best value
            value = self.data_consolidator.get_field_precedence(field, group_listings)
            if value is not None:
                consolidated_data[field] = value
            
            # Check for conflicts
            conflict = self.data_consolidator.detect_conflicts(field, group_listings)
            if conflict:
                conflicts.append(conflict)
        
        # Ensure we have a standard address field for classification
        if 'address_full' in consolidated_data and 'address' not in consolidated_data:
            consolidated_data['address'] = consolidated_data['address_full']
        elif 'address' not in consolidated_data and 'address_street' in consolidated_data:
            # Build address from components
            parts = []
            for f in ['address_street', 'address_city', 'address_state', 'address_zip']:
                if f in consolidated_data and consolidated_data[f]:
                    parts.append(str(consolidated_data[f]))
            if parts:
                consolidated_data['address'] = ', '.join(parts)
        
        # Classify property
        classification, discard_reason, discard_details = self.property_classifier.classify_property(
            consolidated_data
        )
        
        # Create source listings summary
        source_listings = [
            {
                'platform': l['source_platform'],
                'listing_id': l['listing_id'],
                'extracted': l['extraction_timestamp'].isoformat()
            }
            for l in group_listings
        ]
        
        # Generate property ID
        property_id = f"PROP-{group_id:06d}"
        
        return ConsolidatedProperty(
            property_id=property_id,
            consolidated_data=consolidated_data,
            source_listings=source_listings,
            conflicts=conflicts,
            classification=classification,
            discard_reason=discard_reason,
            discard_details=discard_details,
            last_updated=datetime.utcnow()
        )


if __name__ == "__main__":
    # Example usage
    processor = CentralProcessingNode()
    
    # Test address normalization
    test_addresses = [
        "123 Main St, Seattle, WA 98101",
        "123 Main Street, Seattle, WA 98101",
        "0123 N Main St., Seattle, Washington 98101"
    ]
    
    print("Address Normalization:")
    for addr in test_addresses:
        normalized = AddressNormalizer.normalize_address(addr)
        print(f"  {addr}")
        print(f"  -> {normalized}\n")
