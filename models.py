"""
Data models for CRE listing data structures.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ZillowAddress(BaseModel):
    """Zillow address structure."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None


class ZillowLatLong(BaseModel):
    """Zillow lat/long structure."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ZillowListing(BaseModel):
    """Raw Zillow listing data model - matches actual API response."""
    id: str  # Zillow property ID
    price: Optional[str] = None  # Formatted price string
    unformattedPrice: Optional[int] = None  # Numeric price
    beds: Optional[int] = None
    baths: Optional[int] = None
    homeType: Optional[str] = None
    marketingStatus: Optional[str] = None
    homeStatus: Optional[str] = None
    listingSubType: Optional[Dict[str, Any]] = None
    lotAreaValue: Optional[float] = None
    lotAreaUnit: Optional[str] = None
    has3DModel: Optional[bool] = None
    address: Optional[ZillowAddress] = None
    latLong: Optional[ZillowLatLong] = None
    statusText: Optional[str] = None
    imgSrc: Optional[str] = None
    detailUrl: Optional[str] = None
    daysOnZillow: Optional[int] = None
    area: Optional[int] = None  # Square footage
    zestimate: Optional[int] = None
    rentZestimate: Optional[int] = None
    
    def get_full_address(self) -> str:
        """Get formatted full address string."""
        if not self.address:
            return ""
        
        parts = []
        if self.address.street:
            parts.append(self.address.street)
        if self.address.city:
            parts.append(self.address.city)
        if self.address.state:
            parts.append(self.address.state)
        if self.address.zipcode:
            parts.append(self.address.zipcode)
        
        return ", ".join(parts)


class ZillowAPIResponse(BaseModel):
    """Zillow API response model - matches actual API response."""
    success: bool
    totalCount: Optional[int] = None
    currentPage: Optional[str] = None
    totalPages: Optional[int] = None
    regionId: Optional[int] = None
    results: List[ZillowListing] = Field(default_factory=list)  # API uses 'results' not 'data'


class RawListingRecord(BaseModel):
    """Standardized raw listing record from any platform."""
    source_platform: str
    extraction_timestamp: datetime
    listing_id_native: str
    raw_fields: Dict[str, Any]
    metadata: Dict[str, Any]


class ConsolidatedProperty(BaseModel):
    """Consolidated property entity after normalization."""
    property_id: str
    consolidated_data: Dict[str, Any]
    source_listings: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    classification: str  # 'usable', 'flagged', 'discarded'
    discard_reason: Optional[str] = None
    discard_details: Optional[Dict[str, Any]] = None
    last_updated: datetime


class GovernmentRecordsVerification(BaseModel):
    """Government records verification data."""
    property_id: str
    verification_status: str
    government_records: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float


class EnvironmentalContext(BaseModel):
    """Environmental and contextual data for a property."""
    property_id: str
    environmental_context: Dict[str, Any]
    data_sources: Dict[str, str]
    collection_date: datetime
