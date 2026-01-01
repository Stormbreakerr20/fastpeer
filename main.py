"""
Example usage of the CRE Agent system with Zillow integration.

This script demonstrates:
1. Extracting listings from Zillow
2. Processing and normalizing the data
3. Classifying properties
4. Saving results
"""
import json
from datetime import datetime
from zillow_agent import ZillowAgent
from central_processing import CentralProcessingNode
from models import ConsolidatedProperty


def save_consolidated_properties(properties: list, filename: str):
    """Save consolidated properties to JSON file."""
    properties_dict = []
    
    for prop in properties:
        prop_dict = prop.model_dump()
        # Convert datetime objects
        if isinstance(prop_dict.get('last_updated'), datetime):
            prop_dict['last_updated'] = prop_dict['last_updated'].isoformat()
        
        # Convert source listings timestamps
        for source in prop_dict.get('source_listings', []):
            if 'extracted' in source and isinstance(source['extracted'], datetime):
                source['extracted'] = source['extracted'].isoformat()
        
        properties_dict.append(prop_dict)
    
    with open(filename, 'w') as f:
        json.dump(properties_dict, f, indent=2)
    
    print(f"\nSaved {len(properties)} consolidated properties to {filename}")


def print_summary(properties: list):
    """Print summary statistics of processed properties."""
    total = len(properties)
    usable = sum(1 for p in properties if p.classification == 'usable')
    flagged = sum(1 for p in properties if p.classification == 'flagged')
    discarded = sum(1 for p in properties if p.classification == 'discarded')
    
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    print(f"Total Properties: {total}")
    print(f"Usable: {usable} ({usable/total*100:.1f}%)")
    print(f"Flagged: {flagged} ({flagged/total*100:.1f}%)")
    print(f"Discarded: {discarded} ({discarded/total*100:.1f}%)")
    print("="*60)
    
    # Print discard reasons
    if discarded > 0:
        print("\nDiscard Reasons:")
        discard_reasons = {}
        for prop in properties:
            if prop.classification == 'discarded' and prop.discard_reason:
                reason = prop.discard_reason
                discard_reasons[reason] = discard_reasons.get(reason, 0) + 1
        
        for reason, count in discard_reasons.items():
            print(f"  - {reason}: {count}")
    
    # Print conflicts summary
    total_conflicts = sum(len(p.conflicts) for p in properties)
    if total_conflicts > 0:
        print(f"\nTotal Conflicts Detected: {total_conflicts}")
        
        # Most common conflict fields
        conflict_fields = {}
        for prop in properties:
            for conflict in prop.conflicts:
                field = conflict.get('field')
                conflict_fields[field] = conflict_fields.get(field, 0) + 1
        
        print("Most Common Conflict Fields:")
        for field, count in sorted(conflict_fields.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {field}: {count}")


def print_sample_properties(properties: list, max_samples: int = 3):
    """Print sample properties."""
    print("\n" + "="*60)
    print("SAMPLE USABLE PROPERTIES")
    print("="*60)
    
    usable_props = [p for p in properties if p.classification == 'usable']
    
    for i, prop in enumerate(usable_props[:max_samples], 1):
        print(f"\n{i}. Property ID: {prop.property_id}")
        
        # Get address - handle both formats
        address = prop.consolidated_data.get('address') or prop.consolidated_data.get('address_full', 'N/A')
        print(f"   Address: {address}")
        
        # Get price - handle both formats
        price = prop.consolidated_data.get('unformattedPrice') or prop.consolidated_data.get('price', 0)
        if isinstance(price, str):
            import re
            price = re.sub(r'[^\d.]', '', price)
            price = float(price) if price else 0
        print(f"   Price: ${float(price):,.0f}")
        
        print(f"   Beds/Baths: {prop.consolidated_data.get('beds', 'N/A')}/{prop.consolidated_data.get('baths', 'N/A')}")
        print(f"   Area: {prop.consolidated_data.get('area', 'N/A')} sq ft")
        
        if prop.conflicts:
            print(f"   Conflicts: {len(prop.conflicts)}")
            for conflict in prop.conflicts[:2]:
                print(f"     - {conflict.get('field')}: {conflict.get('variance_percent', 'N/A'):.1f}% variance")
        
        print(f"   Sources: {', '.join([s['platform'] for s in prop.source_listings])}")


def main():
    """Main execution function."""
    print("="*60)
    print("CRE AGENT - ZILLOW INTEGRATION DEMO")
    print("="*60)
    
    # Initialize agents
    print("\n1. Initializing Zillow Agent...")
    zillow_agent = ZillowAgent()
    
    print("2. Initializing Central Processing Node...")
    processor = CentralProcessingNode()
    
    # Extract listings from Zillow
    print("\n3. Extracting listings from Zillow...")
    print("   Location: London, UK")
    
    raw_listings = zillow_agent.extract_listings(
        location="london",
    )
    
    print(f"\n   Extracted {len(raw_listings)} raw listings")
    
    if not raw_listings:
        print("\n   No listings found. Exiting.")
        return
    
    # Save raw listings
    print("\n4. Saving raw listings...")
    zillow_agent.save_listings(raw_listings, "data/raw_listings_zillow.json")
    
    # Process listings
    print("\n5. Processing and normalizing listings...")
    consolidated_properties = processor.process_listings(raw_listings)
    
    print(f"   Created {len(consolidated_properties)} consolidated property records")
    
    # Save consolidated properties
    print("\n6. Saving consolidated properties...")
    save_consolidated_properties(
        consolidated_properties,
        "data/consolidated_properties.json"
    )
    
    # Print summary
    print_summary(consolidated_properties)
    
    # Print sample properties
    print_sample_properties(consolidated_properties)
    
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print("\nOutput files:")
    print("  - data/raw_listings_zillow.json")
    print("  - data/consolidated_properties.json")


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    import os
    os.makedirs("data", exist_ok=True)
    
    # Run main function
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
