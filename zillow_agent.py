"""
Zillow Agent - Site-specific listing agent for Zillow platform.

This agent collects raw listing data from Zillow using the RapidAPI Zillow scraper.
Preserves platform-native fields without interpretation or validation.
"""
import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

from models import ZillowAPIResponse, ZillowListing, RawListingRecord


# Load environment variables
load_dotenv()


class ZillowAgent:
    """
    Site-specific agent for Zillow listings.
    
    Characteristics:
    - Platform-native field preservation
    - No cross-source assumptions
    - Minimal transformation
    - Source provenance tagging
    """
    
    def __init__(self, api_key: Optional[str] = None, api_host: Optional[str] = None):
        """
        Initialize Zillow agent with RapidAPI credentials.
        
        Args:
            api_key: RapidAPI key (defaults to environment variable)
            api_host: RapidAPI host (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.api_host = api_host or os.getenv('RAPIDAPI_HOST', 'zillow-com-realtime-scraper.p.rapidapi.com')
        self.base_url = f"https://{self.api_host}/api/search"
        
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
    
    def search_listings(
        self,
        location: str,
        page: Optional[int] = None,
        beds: Optional[int] = None,
        baths: Optional[int] = None,
        home_type: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_sqft: Optional[int] = None,
        max_sqft: Optional[int] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_lot_size: Optional[int] = None,
        max_lot_size: Optional[int] = None,
        days_on_zillow: Optional[int] = None,
        list_type: Optional[str] = None,
        max_hoa: Optional[int] = None,
        open_house: Optional[bool] = None,
        three_d_tour: Optional[bool] = None,
        has_pool: Optional[bool] = None,
        waterfront: Optional[bool] = None,
        single_story: Optional[bool] = None,
        basement: Optional[bool] = None,
        city_view: Optional[bool] = None,
        parking_spots: Optional[int] = None
    ) -> ZillowAPIResponse:
        """
        Search for listings on Zillow with various filters.
        
        Args:
            location: Location to search (e.g., "seattle-wa", "newark-nj")
            page: Page number for pagination
            beds: Minimum number of bedrooms
            baths: Minimum number of bathrooms
            home_type: Type of home (e.g., "apartment", "house", "condo")
            min_price: Minimum price
            max_price: Maximum price
            min_sqft: Minimum square footage
            max_sqft: Maximum square footage
            min_year: Minimum year built
            max_year: Maximum year built
            min_lot_size: Minimum lot size
            max_lot_size: Maximum lot size
            days_on_zillow: Maximum days on Zillow
            list_type: Listing type (e.g., "sale", "rent")
            max_hoa: Maximum HOA fee
            open_house: Filter for open houses
            three_d_tour: Filter for 3D tours
            has_pool: Filter for properties with pools
            waterfront: Filter for waterfront properties
            single_story: Filter for single-story homes
            basement: Filter for properties with basements
            city_view: Filter for properties with city views
            parking_spots: Minimum parking spots
            
        Returns:
            ZillowAPIResponse object containing listing data
        """
        # Build query parameters
        querystring = {"location": location}
        
        # Add optional parameters if provided
        optional_params = {
            "page": page,
            "beds": beds,
            "baths": baths,
            "homeType": home_type,
            "minPrice": min_price,
            "maxPrice": max_price,
            "minSqft": min_sqft,
            "maxSqft": max_sqft,
            "minYear": min_year,
            "maxYear": max_year,
            "minLotSize": min_lot_size,
            "maxLotSize": max_lot_size,
            "daysOnZillow": days_on_zillow,
            "listType": list_type,
            "maxHOA": max_hoa,
            "openHouse": open_house,
            "threeDTour": three_d_tour,
            "hasPool": has_pool,
            "waterfront": waterfront,
            "singleStory": single_story,
            "basement": basement,
            "cityView": city_view,
            "parkingSpots": parking_spots
        }
        
        # Add non-None parameters to querystring
        for key, value in optional_params.items():
            if value is not None:
                querystring[key] = str(value).lower() if isinstance(value, bool) else str(value)
        
        # Set up headers
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host
        }
        
        try:
            # Make API request
            response = requests.get(self.base_url, headers=headers, params=querystring)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return ZillowAPIResponse(**data)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Zillow listings: {e}")
            raise
        except Exception as e:
            print(f"Error parsing Zillow response: {e}")
            raise
    
    def convert_to_raw_listing_record(
        self,
        listing: ZillowListing,
        extraction_timestamp: Optional[datetime] = None
    ) -> RawListingRecord:
        """
        Convert a Zillow listing to standardized RawListingRecord format.
        
        Args:
            listing: ZillowListing object
            extraction_timestamp: Timestamp of extraction (defaults to now)
            
        Returns:
            RawListingRecord object
        """
        if extraction_timestamp is None:
            extraction_timestamp = datetime.utcnow()
        
        # Convert the listing to a dict and flatten the address for easier processing
        raw_data = listing.model_dump()
        
        # Add flattened address for easier access
        if listing.address:
            raw_data['address_full'] = listing.get_full_address()
            raw_data['address_street'] = listing.address.street
            raw_data['address_city'] = listing.address.city
            raw_data['address_state'] = listing.address.state
            raw_data['address_zip'] = listing.address.zipcode
        
        # Add flattened coordinates
        if listing.latLong:
            raw_data['latitude'] = listing.latLong.latitude
            raw_data['longitude'] = listing.latLong.longitude
        
        return RawListingRecord(
            source_platform="zillow",
            extraction_timestamp=extraction_timestamp,
            listing_id_native=listing.id,
            raw_fields=raw_data,
            metadata={
                "scraper_version": "1.0",
                "page_url": listing.detailUrl or "",
                "extraction_status": "success",
                "api_source": "rapidapi_zillow_scraper"
            }
        )
    
    def extract_listings(
        self,
        location: str,
        max_pages: int = 1,
        **search_params
    ) -> List[RawListingRecord]:
        """
        Extract listings from Zillow and convert to standardized format.
        
        Args:
            location: Location to search
            max_pages: Maximum number of pages to extract
            **search_params: Additional search parameters
            
        Returns:
            List of RawListingRecord objects
        """
        all_listings = []
        extraction_timestamp = datetime.utcnow()
        
        for page in range(1, max_pages + 1):
            try:
                # Fetch listings for current page
                response = self.search_listings(
                    location=location,
                    page=page,
                    **search_params
                )
                # Convert to raw listing records
                for listing in response.results:
                    raw_record = self.convert_to_raw_listing_record(
                        listing,
                        extraction_timestamp
                    )
                    all_listings.append(raw_record)
                
                # Check if we've reached the last page
                if page >= (response.totalPages or 1):
                    break
                    
            except Exception as e:
                print(f"Error extracting page {page}: {e}")
                # Continue to next page on error
                continue
        
        return all_listings
    
    def save_listings(
        self,
        listings: List[RawListingRecord],
        output_file: str
    ) -> None:
        """
        Save raw listing records to a JSON file.
        
        Args:
            listings: List of RawListingRecord objects
            output_file: Path to output JSON file
        """
        import json
        
        # Convert to dict format
        listings_dict = [listing.model_dump() for listing in listings]
        
        # Serialize datetime objects
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(listings_dict, f, indent=2, default=datetime_handler)
        
        print(f"Saved {len(listings)} listings to {output_file}")


if __name__ == "__main__":
    # Example usage
    agent = ZillowAgent()
    
    # Search for commercial/investment properties in Newark, NJ
    print("Fetching Zillow listings for Newark, NJ...")
    
    listings = agent.extract_listings(
        location="newark-nj",
        max_pages=2,
        min_price=500000,
        max_price=5000000,
        beds=3  # Multifamily properties typically listed with bedroom counts
    )
    
    print(f"\nExtracted {len(listings)} listings")
    
    # Save to file
    if listings:
        agent.save_listings(listings, "zillow_listings_newark.json")
        
        # Print first listing as example
        print("\nExample listing:")
        print(f"Property ID: {listings[0].listing_id_native}")
        print(f"Address: {listings[0].raw_fields.get('address_full')}")
        print(f"Price: {listings[0].raw_fields.get('price')}")
        print(f"Beds/Baths: {listings[0].raw_fields.get('beds')}/{listings[0].raw_fields.get('baths')}")
        print(f"Square Feet: {listings[0].raw_fields.get('area')}")
