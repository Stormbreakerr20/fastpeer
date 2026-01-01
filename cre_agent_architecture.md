# CRE Agent Architecture for Listing Intelligence and Verification

## Implementation Design

---

## 1. Architectural Overview

This system replicates and scales the CRE analyst workflow for active listing discovery, screening, and verification.

**Design Emphasis:**

- Clear separation of concerns
- Source-specific trust boundaries
- Progressive validation
- High extensibility for future analytical layers

---

## 2. High-Level System Components

The system is composed of five primary layers:

1. **Site-Specific Listing Agents**
2. **Central Processing and Normalization Node**
3. **Government Records Intelligence Agent**
4. **Environmental and Contextual Data Agent**
5. **Validation and Caching Layer**

Each layer mirrors a distinct analytical responsibility.

---

## 3. Parameter Subset (Overall)

### What We Extract Now

Extract only parameters necessary for active listing discovery, cross-platform consolidation, and government validation readiness.

#### Listing Identity Parameters

- Property address (street, city, state, ZIP)
- Parcel ID (if provided)
- Property type (multifamily, office, retail, industrial, land, mixed-use)
- Listing ID (platform-specific)
- Source platform identifier
- Listing URL

#### Physical Characteristics

- Total square footage
- Lot size (acres or square feet)
- Year built
- Number of units (multifamily)
- Number of bedrooms (per unit for multifamily)
- Number of bathrooms (per unit for multifamily)
- Number of floors/stories
- Any other listing data post-processing after they come from websites

#### Financial Parameters

- Asking price
- Price per square foot
- Price per unit (multifamily)
- Cap rate (if stated)
- NOI (if stated)

#### Temporal Metadata

- Date listed
- Days on market
- Last updated date
- Price change history (dates and amounts)

#### Marketing Context

- Listing description (full text)
- Photo count
- Photo URLs
- Document availability flags (OM, rent roll, financials)

#### Occupancy Indicators

- Occupancy rate (if stated)
- Tenant count (if stated)
- Lease type indicators (triple net, gross, modified)

**Parameters explicitly excluded from Phase-1:**

- Detailed financial projections
- Individual tenant information
- Detailed lease terms
- Cap tables or ownership structures
- Historical renovation details

---

## 4. Site-Specific Listing Agents

### Purpose

Collect raw listing data directly from source platforms without interpretation, validation, or reconciliation.

### Characteristics

- One agent per source platform
- Platform-native field preservation
- No cross-source assumptions
- Minimal transformation
- Source provenance tagging

### Agent Roster

**CREXi Agent**

- Target: https://crexi.com
- Frequency: Daily for active listings
- Output: Raw CREXi listing objects

**LoopNet Agent**

- Target: https://loopnet.com
- Frequency: Daily for active listings
- Output: Raw LoopNet listing objects

**Realtor.com Agent**

- Target: https://realtor.com (commercial section)
- Frequency: Daily for active listings
- Output: Raw Realtor.com listing objects

**Zillow Agent**

- Target: https://zillow.com (commercial/investment properties)
- Frequency: Daily for active listings
- Output: Raw Zillow listing objects

### Output Format (per agent)

```json
{
  "source_platform": "crexi",
  "extraction_timestamp": "2025-12-14T10:30:00Z",
  "listing_id_native": "CRX-12345",
  "raw_fields": {
    "address": "123 Main St",
    "city": "Newark",
    "state": "NJ",
    "zip": "07102",
    "property_type": "Multifamily",
    "price": 2500000,
    "square_feet": 15000,
    ...
  },
  "metadata": {
    "scraper_version": "1.0",
    "page_url": "https://crexi.com/properties/...",
    "extraction_status": "success"
  }
}
```

### Critical Rules

- Never discard fields, even if they seem irrelevant
- Tag every field with source platform
- Capture timestamps for all extractions
- Preserve original data types and formats
- Flag extraction errors without failing silently

---

## 5. Central Processing and Normalization Node

### Role

Acts as the analytical core, converting raw listings into coherent property entities. Replicates how analysts mentally consolidate information across platforms.

### Key Responsibilities

#### 5.1 Identity Resolution

**Address Normalization:**

- Standardize street abbreviations (St → Street, Ave → Avenue)
- Remove leading zeros from unit numbers
- Normalize directional indicators (N, S, E, W)
- Handle suite/unit designations consistently

**Cross-Platform Matching:**

Calculate match confidence score:

```
Match Score = 
  (Address Match × 0.40) +
  (City/State/ZIP Match × 0.20) +
  (Property Type Match × 0.15) +
  (Size Match × 0.15) +
  (Price Range Match × 0.10)

Threshold:
- > 0.85: Automatic match
- 0.70-0.85: Manual review flag
- < 0.70: Separate properties
```

**Shadow Property Grouping:**

- Group all listings matching same property
- Preserve all source listings in group
- Track discrepancies across sources

#### 5.2 Data Consolidation

**Field-Level Precedence Rules:**

Priority order for conflicting data:

1. Most recently updated listing
2. Platform with highest historical accuracy
3. Listing with most complete data
4. Direct broker listing over aggregator

**Conflict Retention:**

- Document all discrepancies
- Never discard conflicting values
- Flag properties with material conflicts (>20% price variance, >15% size variance)

**Temporal Prioritization:**

- Use most recent data for volatile fields (price, status)
- Use most complete data for static fields (year built, address)

#### 5.3 Usability Classification

Classify each consolidated property:

**Usable:**

- Coherent property identity
- Within investment mandate
- Recent listing activity
- Minimal unresolved conflicts

**Flagged:**

- Minor conflicts requiring review
- Stagnant listing (>180 days on market)
- Incomplete critical fields
- Unusual pricing patterns

**Discarded:**

- Incoherent property identity (missing address, inconsistent property type)
- Outside investment mandate (wrong asset class, size, or geography)
- Duplicate of existing property (shadow listing already consolidated)
- Internally contradictory data (irreconcilable conflicts across sources)

Only "Usable" properties advance to government verification.

**Discard Retention:**

- All discarded properties retained in database with discard reason
- Available for user review upon request
- Useful for pattern analysis and platform credibility scoring

### Output Format

```json
{
  "property_id": "PROP-NJ-12345",
  "consolidated_data": {
    "address": "123 Main Street",
    "city": "Newark",
    "state": "NJ",
    "zip": "07102",
    ...
  },
  "source_listings": [
    {"platform": "crexi", "listing_id": "CRX-12345", "extracted": "2025-12-14"},
    {"platform": "loopnet", "listing_id": "LN-98765", "extracted": "2025-12-13"}
  ],
  "conflicts": [
    {
      "field": "price",
      "values": [
        {"source": "crexi", "value": 2500000},
        {"source": "loopnet", "value": 2450000}
      ],
      "variance_percent": 2.0
    }
  ],
  "classification": "usable",
  "discard_reason": null,
  "last_updated": "2025-12-14T11:00:00Z"
}
```

**For Discarded Properties:**

```json
{
  "property_id": "PROP-NJ-12346",
  "classification": "discarded",
  "discard_reason": "outside_investment_mandate",
  "discard_details": {
    "reason_category": "asset_class_mismatch",
    "explanation": "Property type 'Land' outside mandate (focus: Multifamily, Office, Retail)",
    "discarded_date": "2025-12-14T11:00:00Z"
  },
  "source_listings": [
    {"platform": "loopnet", "listing_id": "LN-11111", "extracted": "2025-12-14"}
  ]
}
```

---

## 6. Government Records Intelligence Agent

### Scope

Perform authoritative verification using government and quasi-government sources. This is the transition from "marketing claims" to "legal facts."

### Data Collection Hierarchy

**Tier 1 - County Level (Primary Authority):**

Access via individual county websites and offices:

- **County Assessor Offices** - Property tax assessments, parcel data, ownership records
  - Example: Essex County NJ Assessor (https://www.essexcountynj.org)
  - Example: Hudson County NJ Tax Board (https://www.hudsoncountynj.org)
- **County Recorder/Clerk Offices** - Deed records, mortgages, liens, chain of title
  - Example: Essex County NJ Clerk (https://www.essexclerk.com)
  - Typically accessed via county government websites

Data collected:

- Parcel identifiers and geometry
- Legal ownership records
- Tax assessments and classifications
- Deed records and chain of title
- Mortgage and lien records
- County recorder documents (PDFs)

**Tier 2 - Municipal Level:**

Access via municipal websites and code libraries:

- **eCode360** (https://ecode360.com) - Municipal code library and zoning ordinances
- **Municipal Planning/Zoning Departments** - Direct access to local zoning boards
- **Municipal Building Departments** - Permits, violations, certificates of occupancy

Data collected:

- Zoning classifications and overlay districts
- Land use designations
- Building permits and violations
- Certificate of occupancy records
- Variance and special use permits

**Tier 3 - State Level (NJ-Specific):**

Access via New Jersey state databases:

- **NJ Property Records** - State parcel database aggregator
  - NJGIN (NJ Geographic Information Network): https://njgin.nj.gov
- **NJ Division of Taxation** - State tax assessment validation
  - https://www.state.nj.us/treasury/taxation
- **NJ DEP Site Remediation** - Environmental compliance and contamination records
  - https://www.nj.gov/dep/srp

Data collected:

- State parcel database cross-checks
- State tax assessment validation
- Environmental compliance records
- Known contaminated sites
- Deed transfer records

**Tier 4 - Consolidated Services:**

Commercial aggregators combining government data from multiple jurisdictions:

- **CoreLogic** (https://corelogic.com) - Comprehensive property data aggregator, combines county assessor, recorder, and MLS data across US
- **DataTree** (https://datatree.com) - Property research platform with nationwide parcel, ownership, and transaction data
- **ATTOM Data** (https://attomdata.com) - Property data solutions aggregating tax assessor, deed, and foreclosure records

These services provide standardized access to Tier 1-3 data but are not primary sources of truth.

### Verification Requirements

For each usable property, confirm:

- Parcel exists and matches reported address
- Ownership matches or explains listing authority
- Tax assessment aligns with property characteristics
- Zoning permits reported use
- No undisclosed liens or encumbrances
- Deed chain shows clear title path

### Document Handling

Treat documents as first-class data artifacts:

- Store full PDFs (deeds, mortgages, assessments)
- Extract structured data from documents
- OCR text for searchability
- Link documents to property records
- Version control for updated documents

### Discrepancy Management

**Minor Discrepancies (acceptable):**

- Square footage variance <10%
- Year built ±1 year
- Lot size variance <5%

**Material Discrepancies (flag for review):**

- Ownership mismatch
- Zoning incompatible with listed use
- Unreported liens or encumbrances
- Square footage variance >10%
- Tax assessment dramatically different from listing price

**Disqualifying Discrepancies:**

- Parcel does not exist
- Property not owned by listing entity
- Active code violations
- Zoning prohibits listed use

### Output Format

```json
{
  "property_id": "PROP-NJ-12345",
  "verification_status": "verified",
  "government_records": {
    "parcel": {
      "parcel_id": "123-45-678",
      "source": "Essex County Assessor",
      "verified_date": "2025-12-14"
    },
    "ownership": {
      "owner_name": "ABC Property Holdings LLC",
      "deed_date": "2020-03-15",
      "deed_book": "1234",
      "deed_page": "567"
    },
    "tax_assessment": {
      "assessed_value": 2300000,
      "tax_year": 2024,
      "property_class": "4A - Commercial"
    },
    "zoning": {
      "zone": "C-2",
      "description": "General Commercial",
      "source": "Newark Municipal Code via eCode360",
      "verified_date": "2025-12-14"
    }
  },
  "documents": [
    {
      "type": "deed",
      "filename": "deed_123-45-678_2020.pdf",
      "storage_path": "s3://docs/deeds/...",
      "ocr_completed": true
    }
  ],
  "discrepancies": [
    {
      "field": "square_feet",
      "listing_value": 15000,
      "government_value": 14200,
      "variance_percent": 5.6,
      "severity": "minor"
    }
  ],
  "confidence_score": 0.92
}
```

---

## 7. Environmental and Contextual Data Agent

### Purpose

Enrich verified properties with contextual risk and quality signals for future scoring and modeling phases. Does not influence Phase-1 eligibility.

### Data Domains

**Traffic and Transportation:**

- Road traffic density (Google Maps API: https://developers.google.com/maps)
- Distance to major highways
- Public transit access
- Average commute times

**Environmental Factors:**

- Air quality indices (EPA EnviroFacts: https://enviro.epa.gov)
- Noise exposure levels
- Flood hazard zones (FEMA: https://msc.fema.gov)
- Superfund sites proximity
- Hazardous waste facilities

**Demographics and Economics:**

- Population density (US Census: https://data.census.gov)
- Median household income
- Employment rates
- Educational attainment levels

**Distance Matrices:**

- Distance to commercial centers
- Distance to schools
- Distance to hospitals
- Distance to retail anchors
- Distance to parks and recreation

### Data Collection Strategy

**API Integrations:**

- Google Maps Distance Matrix API
- EPA EnviroFacts API
- US Census Bureau API
- FEMA National Flood Hazard Layer

**Calculation Methods:**

- Straight-line distance for preliminary screening
- Driving distance/time for detailed analysis
- Walking distance for urban properties

### Output Format

```json
{
  "property_id": "PROP-NJ-12345",
  "environmental_context": {
    "traffic": {
      "road_traffic_score": 7.2,
      "nearest_highway": "I-280",
      "highway_distance_miles": 0.8
    },
    "environmental": {
      "air_quality_index": 52,
      "flood_zone": "X (minimal risk)",
      "noise_level_db": 65,
      "superfund_within_1mi": false
    },
    "demographics": {
      "population_density_sq_mi": 12500,
      "median_income": 68000,
      "unemployment_rate": 4.2
    },
    "distances": {
      "downtown_miles": 2.3,
      "nearest_transit_miles": 0.4,
      "nearest_school_miles": 0.6,
      "nearest_hospital_miles": 1.2
    }
  },
  "data_sources": {
    "traffic": "Google Maps API",
    "air_quality": "EPA EnviroFacts",
    "flood": "FEMA NFHL",
    "demographics": "US Census Bureau"
  },
  "collection_date": "2025-12-14"
}
```

---

## 8. Validation and Caching Layer

### Purpose

Differentiate between immutable, semi-mutable, and volatile data to balance freshness with efficiency.

### Caching Strategy

**Immutable Data (cache indefinitely):**

- Deed records
- Historical sale transactions
- Parcel geometry
- Year built
- Original construction details

**Semi-Mutable Data (cache 30-90 days):**

- Tax assessments (refresh annually)
- Ownership records (refresh quarterly)
- Zoning classifications (refresh quarterly)
- Environmental data (refresh quarterly)

**Volatile Data (cache 1-7 days or never):**

- Listing price (refresh daily)
- Listing status (refresh daily)
- Days on market (refresh daily)
- Broker contact info (refresh weekly)

### Cache Invalidation Rules

**Trigger immediate refresh:**

- Property sale transaction detected
- Ownership change recorded
- Zoning change notification
- Material discrepancy flagged

**Scheduled refresh:**

- Tax assessment: January annually
- Demographics: Census data release
- Environmental: Quarterly
- Distance data: Semi-annually

### NJ-Specific Validation Layer

For New Jersey properties, additional validation pass using consolidated state-level sources:

**Data Sources:**

- NJ Property Records (state parcel database)
- NJ DEP Site Remediation (environmental)
- NJ Transit proximity data

**Validation Checks:**

- Cross-check county assessor with state records
- Verify environmental compliance
- Confirm transit-oriented development status
- Validate consistency across data sources

**Confidence Amplification:**

- Properties passing NJ-specific validation receive higher confidence scores
- State-level imagery for visual verification
- Enhanced due diligence readiness flag

### Output Format

```json
{
  "property_id": "PROP-NJ-12345",
  "cache_metadata": {
    "immutable_cached": true,
    "semi_mutable_last_refresh": "2024-12-01",
    "volatile_last_refresh": "2025-12-14",
    "next_scheduled_refresh": "2025-12-15"
  },
  "nj_validation": {
    "state_records_checked": true,
    "consistency_score": 0.94,
    "confidence_amplified": true,
    "validation_date": "2025-12-14"
  }
}
```

---
