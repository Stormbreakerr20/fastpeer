"""
Test script for Zillow Agent functionality.

Run this to verify your API key is working and test basic functionality.
"""
from zillow_agent import ZillowAgent
from central_processing import AddressNormalizer, PropertyMatcher


def test_api_connection():
    """Test basic API connection."""
    print("Testing Zillow API connection...")
    try:
        agent = ZillowAgent()
        print("✓ ZillowAgent initialized successfully")
        return agent
    except Exception as e:
        print(f"✗ Failed to initialize ZillowAgent: {e}")
        return None


def test_simple_search(agent):
    """Test a simple search query."""
    print("\nTesting simple search (Seattle, WA)...")
    try:
        response = agent.search_listings(location="seattle-wa")
        print(f"✓ Search successful")
        print(f"  - Total count: {response.totalCount}")
        print(f"  - Current page count: {response.currentPageCount}")
        print(f"  - Total pages: {response.totalPages}")
        
        if response.data:
            sample = response.data[0]
            print(f"\nSample listing:")
            print(f"  - Address: {sample.address}")
            print(f"  - Price: {sample.priceFormatted}")
            print(f"  - Beds/Baths: {sample.beds}/{sample.baths}")
            print(f"  - Area: {sample.area} sq ft")
        
        return True
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return False


def test_filtered_search(agent):
    """Test search with filters."""
    print("\nTesting filtered search...")
    try:
        response = agent.search_listings(
            location="newark-nj",
            min_price=500000,
            max_price=2000000,
            beds=3
        )
        print(f"✓ Filtered search successful")
        print(f"  - Results: {response.currentPageCount}")
        return True
    except Exception as e:
        print(f"✗ Filtered search failed: {e}")
        return False


def test_address_normalization():
    """Test address normalization."""
    print("\nTesting address normalization...")
    
    test_cases = [
        ("123 Main St", "123 MAIN STREET"),
        ("456 N Oak Ave", "456 NORTH OAK AVENUE"),
        ("789 SW 1st Blvd, Apt 5", "789 SOUTHWEST 1ST BOULEVARD UNIT 5"),
        ("0100 Park Pl", "100 PARK PLACE")
    ]
    
    all_passed = True
    for input_addr, expected in test_cases:
        result = AddressNormalizer.normalize_address(input_addr)
        passed = expected in result or result in expected
        
        status = "✓" if passed else "✗"
        print(f"  {status} '{input_addr}' -> '{result}'")
        
        if not passed:
            print(f"     Expected: '{expected}'")
            all_passed = False
    
    return all_passed


def test_property_matching():
    """Test property matching logic."""
    print("\nTesting property matching...")
    
    listing1 = {
        "address": "123 Main Street, Seattle, WA 98101",
        "price": 1000000,
        "area": 2000
    }
    
    listing2 = {
        "address": "123 Main St, Seattle, WA 98101",
        "price": 1050000,
        "area": 2050
    }
    
    is_match, score = PropertyMatcher.is_match(listing1, listing2)
    
    print(f"  Match score: {score:.2f}")
    print(f"  Is match: {is_match}")
    
    if score > 0.7:
        print(f"  ✓ Match detection working (score > 0.7)")
        return True
    else:
        print(f"  ✗ Match detection may need tuning (score <= 0.7)")
        return False


def test_raw_listing_conversion(agent):
    """Test conversion to raw listing record."""
    print("\nTesting raw listing conversion...")
    try:
        response = agent.search_listings(location="seattle-wa")
        
        if not response.data:
            print("  ✗ No listings to convert")
            return False
        
        raw_record = agent.convert_to_raw_listing_record(response.data[0])
        
        print(f"  ✓ Conversion successful")
        print(f"  - Platform: {raw_record.source_platform}")
        print(f"  - Listing ID: {raw_record.listing_id_native}")
        print(f"  - Fields: {len(raw_record.raw_fields)} extracted")
        
        return True
    except Exception as e:
        print(f"  ✗ Conversion failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("ZILLOW AGENT TEST SUITE")
    print("="*60)
    
    results = {}
    
    # Test API connection
    agent = test_api_connection()
    results['API Connection'] = agent is not None
    
    if agent:
        # Test searches
        results['Simple Search'] = test_simple_search(agent)
        results['Filtered Search'] = test_filtered_search(agent)
        results['Raw Listing Conversion'] = test_raw_listing_conversion(agent)
    
    # Test processing functions
    results['Address Normalization'] = test_address_normalization()
    results['Property Matching'] = test_property_matching()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
