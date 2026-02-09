# Working with Discogs Custom Fields

## What Are Custom Fields?

Discogs allows you to create **custom fields** for your collection at:
https://www.discogs.com/settings/collection-fields

These fields let you track additional information beyond what Discogs provides by default.

## Types of Custom Fields

### 1. Text Fields
Free-form text entry. Examples:
- Purchase Price
- Purchase Location
- Storage Location  
- Personal Notes
- Loan Status

### 2. Dropdown Fields
Predefined options you can select from. Examples:
- Media Condition (Mint, Near Mint, VG+, etc.)
- Sleeve Condition
- Want to Sell (Yes/No)
- Priority (High/Medium/Low)

## Creating Custom Fields in Discogs

1. Go to https://www.discogs.com/settings/collection-fields
2. Click "Add a Field"
3. Fill in:
   - **Field Name**: What you want to call it
   - **Type**: Text or Dropdown
   - **Options** (for dropdown): List your choices
   - **Public**: Whether others can see this field
4. Click Save

## How Custom Fields Work with the API

### What Gets Stored in Discogs
✅ Custom field **values** are stored per collection item  
✅ You can read and write these values via API  
✅ Values sync across web, mobile, and API

### What Gets Stored Locally (CSV)
✅ All Discogs metadata (genres, styles, credits, etc.)  
✅ Custom field values  
✅ ANY additional columns you add in Excel  

## Workflow 1: Manual Entry in Discogs, Export to Excel

**Best for:** Tracking info you enter as you add items

1. Add items to Discogs collection via web or mobile
2. Fill in custom fields manually
3. Run the custom fields manager script:
   ```bash
   python discogs_custom_fields_manager.py
   ```
4. Open `my_collection_with_custom_fields.csv` in Excel
5. Add any extra columns you want (Excel-only)
6. Use Excel for analysis, sorting, filtering

**Pros:**
- Simple workflow
- Custom fields visible in Discogs web/mobile
- Easy to enter on-the-go

**Cons:**
- Manual data entry

## Workflow 2: Auto-Populate from Metadata

**Best for:** Syncing Discogs metadata to custom fields

Example: Copy release year to a "Year" custom field

1. Create custom field "Year" in Discogs
2. Edit the script to map metadata → custom field:
   ```python
   def get_year(item):
       return item['basic_information'].get('year')
   
   manager.bulk_update_from_metadata(
       field_name="Year",
       metadata_extractor=get_year,
       dry_run=False  # Set to False to actually update
   )
   ```
3. Run the script
4. Your Discogs collection now has Year populated!

**Why would you do this?**
- Make metadata searchable/filterable in Discogs mobile app
- Create dropdown fields from Discogs genres
- Normalize data for better sorting

## Workflow 3: Hybrid Approach

**Best for:** Most users

1. Create custom fields for data you'll enter manually:
   - Purchase Price
   - Storage Location
   - Personal Notes

2. Create custom fields for auto-populated data:
   - Genre (from Discogs metadata)
   - Decade (calculated from year)
   - Format Type (simplified from Discogs format)

3. Use Excel for complex analysis:
   - Add calculated columns
   - Create pivot tables
   - Track value over time

## Example Custom Field Setups

### Setup 1: Collector Basics
```
Text Fields:
- Purchase Date
- Purchase Price  
- Purchase Location
- Storage Location

Dropdown Fields:
- Media Condition (Mint, NM, VG+, VG, G, Poor)
- Sleeve Condition (Mint, NM, VG+, VG, G, Poor)
```

### Setup 2: DJ/Radio
```
Text Fields:
- BPM
- Key
- Intro Length
- Outro Length

Dropdown Fields:
- Energy (High, Medium, Low)
- Explicit (Yes, No)
- Radio Edit (Yes, No)
```

### Setup 3: Reseller
```
Text Fields:
- Cost
- Target Price
- Sold Price
- Sold Date

Dropdown Fields:
- Status (Keep, Sell, Sold, Trade)
- Listing Platform (Discogs, eBay, Local, N/A)
```

### Setup 4: Archiver/Digitizer
```
Text Fields:
- Digital Copy Location
- Rip Quality
- Rip Date

Dropdown Fields:
- Digitized (Yes, No, In Progress)
- Format (FLAC, MP3 320, WAV, etc.)
- Backed Up (Yes, No)
```

## Common Use Cases

### Use Case: Track Collection Value

1. Create text field "Purchase Price"
2. Enter prices as you add items
3. Export to Excel
4. Sum the column in Excel
5. Compare to Discogs estimated value

### Use Case: Know What's Where

1. Create text field "Location"
2. Enter shelf/box locations
3. When you want to play something:
   - Search in Discogs mobile app
   - See the location in custom field
   - Go grab it!

### Use Case: Flag Items to Sell

1. Create dropdown "Status" with options: Keep, Sell, Sold
2. Mark duplicates or unwanted items as "Sell"
3. Filter in Discogs or export to Excel
4. List them on marketplace

### Use Case: Track Condition

1. Create two dropdowns:
   - Media Condition
   - Sleeve Condition
2. Grade items as you inspect them
3. Export to Excel
4. Sort by condition to find items needing upgrades

## Syncing Metadata to Custom Fields

The custom fields manager can auto-populate fields from Discogs metadata.

### Example: Sync First Genre

```python
def get_first_genre(item):
    # Need to fetch detailed release info
    sync = DiscogsLibrarySync(manager.user_token, manager.username)
    details = sync.get_release_details(item['basic_information']['id'])
    genres = details.get('genres', [])
    return genres[0] if genres else None

manager.bulk_update_from_metadata(
    field_name="Genre",
    metadata_extractor=get_first_genre,
    dry_run=False
)
```

### Example: Calculate Decade

```python
def get_decade(item):
    year = item['basic_information'].get('year')
    if year:
        return f"{(year // 10) * 10}s"
    return None

manager.bulk_update_from_metadata(
    field_name="Decade",
    metadata_extractor=get_decade,
    dry_run=False
)
```

### Example: Simplify Format

```python
def get_simple_format(item):
    format_str = ', '.join([f['name'] for f in item['basic_information'].get('formats', [])])
    
    if 'Vinyl' in format_str:
        return 'Vinyl'
    elif 'CD' in format_str:
        return 'CD'
    elif 'Cassette' in format_str:
        return 'Cassette'
    elif 'Digital' in format_str:
        return 'Digital'
    else:
        return 'Other'

manager.bulk_update_from_metadata(
    field_name="Format Type",
    metadata_extractor=get_simple_format,
    dry_run=False
)
```

## Important Notes

### Rate Limiting
- The API has rate limits (60 requests/minute)
- The script includes automatic delays
- Large collections (1000+ items) may take 30-60 minutes

### Dry Run Mode
Always test with `dry_run=True` first:
```python
manager.bulk_update_from_metadata(
    field_name="Year",
    metadata_extractor=get_year,
    dry_run=True  # Shows what would change
)
```

Once you confirm it looks right:
```python
manager.bulk_update_from_metadata(
    field_name="Year", 
    metadata_extractor=get_year,
    dry_run=False  # Actually makes the changes
)
```

### Field IDs
Each custom field has an ID number. The script automatically looks these up by name, so you don't need to worry about them.

### Backup Your Data
Before bulk operations:
1. Export your collection from Discogs website
2. Or run the export script first to have a backup

## Combining with the Basic Sync Script

You can use both scripts together:

**discogs_library_sync.py** - For:
- Getting full metadata
- Exporting to work offline
- Analysis in Excel

**discogs_custom_fields_manager.py** - For:
- Reading your custom field values
- Bulk updating custom fields
- Syncing metadata → custom fields

## Excel Power User Tips

After exporting with custom fields:

1. **Conditional Formatting**
   - Highlight items over a certain price
   - Color-code by condition
   - Flag missing data

2. **Pivot Tables**
   - Purchases by year
   - Collection value by format
   - Condition distribution

3. **Formulas**
   - Calculate age: `=YEAR(TODAY()) - [Year]`
   - Calculate profit: `=[Sold Price] - [Purchase Price]`
   - Track ROI: `=([Sold Price]/[Purchase Price])-1`

4. **Filters**
   - Show only items to sell
   - Find items in specific location
   - View by condition

## Troubleshooting

### "Field not found" error
- Check spelling (case-sensitive!)
- Make sure field exists at https://www.discogs.com/settings/collection-fields
- Run `get_custom_fields()` to see available field names

### Updates not showing in Discogs
- Clear browser cache
- Check API returned success
- Verify you're looking at right folder
- Wait a minute and refresh

### Script is slow
- This is normal for large collections
- API has rate limits
- Be patient or reduce batch size

### Can't see custom fields in export
- Make sure you're using `get_collection_with_custom_fields()`
- Basic collection endpoint doesn't include custom field values
- Need to fetch individual instances
