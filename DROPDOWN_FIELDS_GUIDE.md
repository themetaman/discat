# Dropdown Custom Fields - Quick Guide

## What Are Dropdown Fields?

Dropdown fields in Discogs have a **predefined list of options** that you create. Unlike text fields (where you can type anything), dropdown fields only accept values from your list.

## Creating a Dropdown Field

1. Go to https://www.discogs.com/settings/collection-fields
2. Click "Add a Field"
3. Fill in:
   - **Field Name**: e.g., "Media Condition"
   - **Type**: Select **"Dropdown"**
   - **Options**: Add each option on a new line:
     ```
     Mint (M)
     Near Mint (NM or M-)
     Very Good Plus (VG+)
     Very Good (VG)
     Good Plus (G+)
     Good (G)
     Fair (F)
     Poor (P)
     ```
4. Click Save

## Important: Exact Match Required

When syncing metadata to a dropdown field, the value **must match exactly**:
- ✅ `"Mint (M)"` - Correct
- ❌ `"Mint"` - Wrong (missing the "(M)")
- ❌ `"mint (m)"` - Wrong (case doesn't match)
- ❌ `"Mint (M) "` - Wrong (extra space)

## The Script Validates For You!

The updated script now:
1. ✅ Reads your dropdown options from Discogs
2. ✅ Checks if each value matches before updating
3. ✅ Shows you which items failed validation
4. ✅ Prevents API errors

Example output:
```
🔄 Syncing to custom field: Media Condition (ID: 123)
   Field type: dropdown
   Dropdown options: ['Mint (M)', 'Near Mint (NM or M-)', 'Very Good Plus (VG+)', 'Very Good (VG)']
   ⚠️  Values will be validated against these options

   [DRY RUN MODE - No changes will be made]
   
   ⚠️  [5/656] VALIDATION FAILED: The Beatles - Abbey Road
      Value 'Excellent' not in dropdown options: ['Mint (M)', 'Near Mint (NM or M-)', 'Very Good Plus (VG+)', 'Very Good (VG)']
```

## Example Dropdown Setups

### Setup 1: Media Condition (Standard Goldmine Grading)
```
Mint (M)
Near Mint (NM or M-)
Very Good Plus (VG+)
Very Good (VG)
Good Plus (G+)
Good (G)
Fair (F)
Poor (P)
```

### Setup 2: Format Type (Simplified)
```
Vinyl
CD
Cassette
Digital
Other
```

### Setup 3: Want to Sell
```
Yes
No
Maybe
```

### Setup 4: Priority
```
High
Medium
Low
```

### Setup 5: Storage Location
```
Shelf A
Shelf B
Shelf C
Box 1
Box 2
Storage Unit
```

## Writing a Dropdown-Safe Extractor

### Example 1: Condition Based on Year

```python
def extract_condition_by_year(item: Dict) -> Optional[str]:
    """
    IMPORTANT: These return values MUST match your dropdown options EXACTLY.
    """
    year = item['basic_information'].get('year')
    if not year:
        return None
    
    # Match these to YOUR dropdown options
    if year >= 2020:
        return "Mint (M)"  # Must be exactly: "Mint (M)"
    elif year >= 2015:
        return "Near Mint (NM or M-)"  # Must be exactly: "Near Mint (NM or M-)"
    elif year >= 2010:
        return "Very Good Plus (VG+)"  # Must be exactly: "Very Good Plus (VG+)"
    else:
        return "Very Good (VG)"  # Must be exactly: "Very Good (VG)"
```

### Example 2: Format Type

```python
def extract_format_type(item: Dict) -> Optional[str]:
    """
    For a dropdown with options: Vinyl, CD, Cassette, Digital, Other
    """
    format_str = ', '.join([f['name'] for f in item['basic_information'].get('formats', [])])
    
    if 'Vinyl' in format_str:
        return 'Vinyl'  # Matches dropdown option
    elif 'CD' in format_str:
        return 'CD'  # Matches dropdown option
    elif 'Cassette' in format_str:
        return 'Cassette'  # Matches dropdown option
    elif 'Digital' in format_str:
        return 'Digital'  # Matches dropdown option
    else:
        return 'Other'  # Matches dropdown option
```

### Example 3: Yes/No Based on Logic

```python
def extract_want_to_sell(item: Dict) -> Optional[str]:
    """
    For a dropdown with options: Yes, No
    Mark duplicates or low-value items to sell.
    """
    # Your logic here
    lowest_price = item.get('detailed_metadata', {}).get('lowest_price')
    
    if lowest_price and float(lowest_price) < 5.0:
        return "Yes"  # Matches dropdown option
    else:
        return "No"  # Matches dropdown option
```

## Common Mistakes and Fixes

### Mistake 1: Wrong Capitalization
```python
# ❌ WRONG
return "vinyl"  # Dropdown has "Vinyl"

# ✅ CORRECT
return "Vinyl"  # Matches exactly
```

### Mistake 2: Missing Punctuation
```python
# ❌ WRONG
return "Near Mint"  # Dropdown has "Near Mint (NM or M-)"

# ✅ CORRECT
return "Near Mint (NM or M-)"  # Matches exactly
```

### Mistake 3: Extra Spaces
```python
# ❌ WRONG
return "Very Good Plus (VG+) "  # Extra space at end

# ✅ CORRECT
return "Very Good Plus (VG+)"  # No extra spaces
```

## Testing Your Extractor

Always test with `dry_run=True` first:

```python
manager.sync_metadata_to_custom_field(
    collection=collection,
    field_name="Media Condition",
    metadata_extractor=extract_condition_by_year,
    dry_run=True  # ← Test mode!
)
```

The script will show you:
- ✅ Which items would be updated successfully
- ❌ Which items failed validation (value not in dropdown)
- 📊 Summary of results

If you see validation failures, fix your extractor function to return only valid options.

## Using the Validation Output

When you see validation failures:

```
❌ Validation failed (not in dropdown options): 45 items
   Fix your metadata_extractor to return only these values: ['Vinyl', 'CD', 'Cassette', 'Digital', 'Other']
```

This tells you:
1. 45 items have values that don't match your dropdown
2. The valid options are: Vinyl, CD, Cassette, Digital, Other
3. Your extractor is returning something else (maybe "LP" or "Album")

Fix your extractor to map all possible values to one of the dropdown options.

## Pro Tip: Check Your Dropdown Options First

Before writing an extractor, run the script once to see your dropdown options:

```python
manager = DiscogsCompleteManager(TOKEN, USERNAME)
fields = manager.get_custom_fields()

# Find your dropdown field
for field in fields:
    if field['name'] == 'Media Condition':
        print(f"Options: {field.get('options', [])}")
```

Then write your extractor to return ONLY those exact values.

## Text Fields vs Dropdown Fields

| Feature | Text Field | Dropdown Field |
|---------|-----------|----------------|
| Can store any value | ✅ Yes | ❌ No - only predefined options |
| Validation needed | ❌ No | ✅ Yes - must match exactly |
| Good for | Free-form notes, prices, URLs | Standardized categories |
| Example | "Bought at Joe's Records for $25" | "Near Mint (NM or M-)" |

## When to Use Dropdown vs Text

**Use Dropdown when:**
- You want standardized values
- You'll filter/sort by this field
- Limited set of options (< 20)
- Examples: Condition, Format, Priority, Yes/No

**Use Text when:**
- Open-ended information
- Unique per item
- Unlimited variety
- Examples: Notes, Purchase Location, Storage Details

## Need Help?

If you're getting validation errors:
1. Check the script output for the exact dropdown options
2. Make sure your extractor returns ONLY those exact values
3. Test with dry_run=True first
4. Copy/paste dropdown options from Discogs to avoid typos
