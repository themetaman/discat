# DisCat 🐱

**Discogs Catalogue Manager**

The purr-fect tool for downloading and managing your Discogs music collection!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

> **Note:** DisCat is a **fork-friendly, minimal-support** project. Feel free to customize it for your needs! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 🎯 What This Does

**Three ways to manage your collection:**

1. **`discogs_gui.py`** - GUI Application (RECOMMENDED) - Point and click interface
2. **`1_download_collection.py`** - Download script with cache support
3. **`2_sync_custom_fields.py`** - Sync metadata to custom fields

## 📦 What You Get

After running the download:
- **discogs_collection_YYYYMMDD_HHMMSS.csv** - Your entire collection with timestamp
- **discogs_collection_YYYYMMDD_HHMMSS.json** - Complete backup with timestamp
- **discogs_collection_full.json** - Latest version for sync script
- **discogs_report.txt** - Beautiful summary report with top formats, years, labels, genres, styles
- **discogs_cache.json** - Cache for faster subsequent downloads

The CSV includes:
- ✅ **Download timestamp** - Know when data was fetched
- ✅ **Folder names** - Electronic, Funk / Soul, etc.
- ✅ All Discogs metadata (genres, styles, credits, tracklist, identifiers)
- ✅ **Marketplace pricing** - Low price, median, # for sale
- ✅ Community stats (have/want counts)
- ✅ Your custom field values
- ✅ Everything in one spreadsheet!

## 🚀 Quick Start (Windows)

### 1. Install Python & Requirements

Download Python from https://python.org (check "Add to PATH" during install)

Open Command Prompt and run:
```cmd
pip install requests
```

### 2. Get Your Discogs Token

1. Go to https://www.discogs.com/settings/developers
2. Click "Generate new token"
3. Copy the token

### 3. Configure DisCat

**All configuration now uses a single `config.env` file!**

#### Option A: GUI Settings (Easiest)
```cmd
python discogs_gui.py
```
1. Go to Settings tab
2. Enter token and username  
3. Click "Save Credentials"
4. Creates/updates `config.env` automatically

**Your credentials now work with BOTH GUI and CLI scripts!**

#### Option B: Create config.env Manually
```cmd
# Copy the example file
cp config.env.example config.env

# Edit config.env with your credentials
DISCOGS_TOKEN=your_actual_token
DISCOGS_USERNAME=your_username
```

#### Option C: Edit Scripts Directly (Old School)
Open `1_download_collection.py` and `2_sync_custom_fields.py`, find:
```python
USER_TOKEN = "YOUR_DISCOGS_TOKEN_HERE"
USERNAME = "YOUR_USERNAME_HERE"
```
Replace with your actual credentials.

> **One Config File, All Tools:** Whether you use GUI or CLI, credentials are shared via `config.env`. No more managing multiple credential files!

### 4. Download Your Collection

```cmd
cd C:\Discogs
python 1_download_collection.py
```

This will:
- Download your collection (fast)
- Get custom field values (slow - 1 API call per item)
- Ask if you want full metadata (very slow - 1 API call per item)
- Export everything to CSV, JSON, and generate report

**For 656 items:** Basic download ~5 minutes, full metadata ~15-20 minutes

### 5. (Optional) Sync Metadata to Custom Fields

First, create custom fields in Discogs:
https://www.discogs.com/settings/collection-fields

Then:
```cmd
python 2_sync_custom_fields.py
```

Edit the script to uncomment the sync you want, run it, review the preview, then confirm.

## 🚀 New Features

### ⚡ Incremental Caching
- **First download:** ~15-20 minutes for full collection
- **Subsequent downloads:** ~2 minutes (only fetches new/changed items!)
- Automatic detection of new and modified items
- Cache stored locally in `discogs_cache.json`

### 📅 Timestamped Exports
- Files named with date/time: `discogs_collection_20260208_143522.csv`
- Download date column in CSV for tracking
- Compare multiple exports to track price changes

### 📁 Folder Support
- Folder names in CSV (Electronic, Funk / Soul, etc.)
- Organize and filter by folder

### 💰 Full Marketplace Data
- Price Low (lowest listing)
- Price Median (average price) 
- Number for Sale
- Community Have/Want counts

### 🔄 Master Release Fallback
- Automatically handles merged/deleted releases
- Falls back to master release if specific release 404s
- No more missing metadata errors

## 📋 Files Overview

### Applications

**discogs_gui.py** - GUI Application
- Visual interface with tabs
- Real-time progress tracking
- Preview sync before applying
- All features in one place
- **Use this for 90% of tasks**

**1_download_collection.py** - Download Script
- Command-line interface
- Supports `-c` flag for caching
- Good for automation/scheduling
- All download features

**2_sync_custom_fields.py** - Sync Script  
- Command-line interface
- Preview before syncing
- Validation for dropdowns
- Good for automation

### Output Files

**discogs_collection_YYYYMMDD_HHMMSS.csv**
- Timestamped collection export
- Open in Excel
- All metadata + custom fields
- Perfect for analysis

**discogs_collection_YYYYMMDD_HHMMSS.json**
- Timestamped complete backup
- Includes full tracklist, credits
- Used for comparisons

**discogs_collection_full.json**
- Latest version (no timestamp)
- Used by sync script
- Updated with each download

**discogs_report.txt**
- Summary statistics
- Top 10: formats, years, labels, genres, styles
- Collection overview

**discogs_cache.json**
- Local cache for incremental updates
- Stores all fetched data
- Delete to force full re-download

## 🎓 Common Workflows

### Workflow 1: First Time Setup (GUI)

1. Run `python discogs_gui.py`
2. Go to **Settings** tab → Enter credentials
3. Go to **Download** tab
4. ✅ Check "Use cache"
5. ✅ Check "Include custom field values"
6. ❌ Uncheck "Include full metadata" (for speed)
7. Click "Download Collection"
8. ⏱️ Wait ~5-10 minutes

You get: Basic collection with custom fields

### Workflow 2: Complete Download with All Metadata (GUI)

1. Run `python discogs_gui.py`
2. Go to **Download** tab
3. ✅ Check all options
4. Click "Download Collection"
5. ⏱️ Wait ~15-20 minutes

You get: Everything including genres, styles, credits, pricing

### Workflow 3: Weekly Price Updates (Command Line + Cache)

```cmd
# Monday - full download
python 1_download_collection.py -c

# Friday - incremental update (fast!)
python 1_download_collection.py -c
```

Compare the CSV files to see price changes over the week.

### Workflow 4: Sync Metadata to Custom Fields (GUI)

**Example: Copy release year to "Year" custom field**

1. Create "Year" custom field in Discogs: https://www.discogs.com/settings/collection-fields
2. Run GUI → **Sync Custom Fields** tab
3. Enter field name: `Year`
4. Select: **Year**
5. ✅ Check "Ignore validation errors"
6. Click "Preview Sync"
7. Review changes
8. Click "Execute Sync"

Now your Discogs "Year" field is populated from metadata!

### Workflow 5: Monthly Collection Tracking

```cmd
# First of each month
python 1_download_collection.py -c
```

Keep monthly snapshots:
```
discogs_collection_20260101_120000.csv
discogs_collection_20260201_120000.csv
discogs_collection_20260301_120000.csv
```

Track collection growth and value changes over time!

## 📊 What Metadata Gets Downloaded

### Basic Information
- Artist, Title, Year
- Format, Label, Catalog Number
- Master Release ID
- Date Added, Rating, Folder

### Detailed Metadata (if enrichment enabled)
- **Genres & Styles** - All genre/style tags
- **Country** - Country of release
- **Release Date** - Specific release date
- **Tracklist** - Complete track listing with durations
- **Credits** - All contributors (producers, engineers, etc.)
- **Identifiers** - Barcodes, matrix numbers, etc.
- **Notes** - Release notes from Discogs
- **Companies** - Manufacturing, distribution info

### Community Data
- Have Count - How many users own this
- Want Count - How many users want this
- Lowest Price - Current marketplace price

### Your Data
- **Custom Field Values** - All your custom fields
- **Instance ID** - Your specific copy ID
- **Folder ID** - Which folder it's in

## 🔧 Custom Fields Guide

### Creating Custom Fields

Go to: https://www.discogs.com/settings/collection-fields

**Two Types:**

1. **Text Fields** - Free-form text
   - Examples: Purchase Price, Location, Notes
   
2. **Dropdown Fields** - Predefined options
   - Examples: Condition, Format Type, Want to Sell
   - Options must match EXACTLY when syncing

### Example Custom Field Setups

**Collector:**
```
Purchase Date (text)
Purchase Price (text)
Purchase Location (text)
Storage Location (text)
Media Condition (dropdown: Mint, NM, VG+, VG, G)
Sleeve Condition (dropdown: Mint, NM, VG+, VG, G)
```

**DJ:**
```
BPM (text)
Key (text)
Energy (dropdown: High, Medium, Low)
Intro Length (text)
Outro Length (text)
```

**Reseller:**
```
Cost (text)
Target Price (text)
Sold Price (text)
Status (dropdown: Keep, Sell, Sold, Trade)
Platform (dropdown: Discogs, eBay, Local, N/A)
```

### Syncing Metadata to Custom Fields

The sync script includes these extractors:

- `extract_year` - Release year
- `extract_decade` - Calculated decade (1970s, 1980s, etc.)
- `extract_first_genre` - First genre tag
- `extract_format_simple` - Simplified format (Vinyl, CD, Cassette, Digital, Other)

**Creating Your Own Extractor:**

```python
def extract_my_field(item: Dict) -> Optional[str]:
    """Extract whatever you want from metadata."""
    # Access basic info
    year = item['basic_information'].get('year')
    
    # Access detailed metadata
    detailed = item.get('detailed_metadata', {})
    country = detailed.get('country')
    
    # Your logic here
    if country == 'US' and year >= 2000:
        return 'Modern American'
    else:
        return 'Other'
```

### Dropdown Validation

For dropdown fields, values must match EXACTLY:

✅ **Correct:** `"Mint (M)"` matches dropdown option `"Mint (M)"`
❌ **Wrong:** `"Mint"` doesn't match `"Mint (M)"`
❌ **Wrong:** `"mint (m)"` doesn't match `"Mint (M)"` (case-sensitive)

The sync script validates for you and shows which items fail.

## ⚠️ Important Notes

### Rate Limiting

Discogs API limits: **60 requests per minute**

The scripts handle this automatically by:
- Pausing when rate limit gets low
- Conservative sleep times between requests
- Monitoring remaining requests

**Expected times for 656 items:**
- Basic collection: ~5 minutes
- Custom field values: ~15 minutes (1 API call per item)
- Full metadata: ~20 minutes (1 API call per item)

### The Scripts Don't Modify Discogs Metadata

The scripts:
- ✅ Read Discogs metadata (genres, year, etc.)
- ✅ Update your custom fields
- ✅ Update ratings, notes, folders
- ❌ Never modify Discogs metadata (community-maintained)

### File Sizes

For a 656-item collection:
- CSV: ~2-5 MB
- JSON: ~10-50 MB (depends on metadata depth)
- Report: ~5 KB

## 💾 Caching System

### How It Works

The cache stores complete metadata for all items locally:
- First download: Fetches everything (~15-20 min)
- Subsequent downloads: Only fetches new/changed items (~2 min)
- Compares by `instance_id` and `date_added`
- Automatically updates cache after each download

### Cache Benefits

**Speed:** 5-10x faster for subsequent downloads
**Smart:** Only fetches what changed
**Automatic:** No manual management needed
**Safe:** Original data always preserved

### Cache Commands

**GUI:**
- ✅ Check "Use cache" (default: ON)
- Cache saved automatically

**Command Line:**
```cmd
# Use cache (incremental)
python 1_download_collection.py -c

# Force full download (no cache)
python 1_download_collection.py

# Clear cache and re-download
python 1_download_collection.py --clear-cache
```

### When to Clear Cache

- ❌ Cache file corrupted
- ❌ Want to re-fetch all metadata (prices updated)
- ❌ Testing/debugging
- ❌ Major Discogs collection changes

### Cache File Location

`discogs_cache.json` - Same directory as scripts

## 🐛 Troubleshooting

### 429 Too Many Requests Error

**Cause:** Making API requests too fast
**Fix:** Scripts now have smart rate limiting. This should rarely happen.

### 404 Release Not Found Errors

**Cause:** Release has been merged into master release
**Fix:** Scripts automatically fall back to master release. You'll see:
```
⚠️  Release 404, trying master 123456...
✅ Got data from master release
```

### Cache Shows Old Data

**Cause:** Using cached data, no new changes detected
**Fix:** This is normal! If you want fresh data:
```cmd
python 1_download_collection.py --clear-cache
```

### Missing Folder Names in CSV

**Cause:** Using old version without folder support
**Fix:** Re-download with latest version

### Sync Validation Failures

**Cause:** Trying to sync values not in dropdown options
**Fix:** 
- Check "Ignore validation errors" to skip failed items
- Or adjust your extractor to return valid dropdown values

### Script is Slow

**Cause:** Rate limiting is working correctly
**Fix:** This is normal. For large collections:
- Basic download: 5-10 minutes
- With custom fields: 15-30 minutes
- Full metadata: 20-40 minutes

### Missing Metadata in CSV

**Cause:** Skipped full metadata enrichment
**Fix:** Re-run download script and say 'yes' to enrichment

### Can't Open CSV in Excel

**Cause:** Some fields contain JSON data (tracklist, credits)
**Fix:** 
- Excel might show these as text - this is normal
- Use JSON file for programmatic access to this data
- Or add `json.loads()` in Python to parse these fields

## 💡 Pro Tips

### 1. Regular Backups

Run the download script monthly:
```cmd
python 1_download_collection.py
```

Save the JSON file with a date:
```cmd
rename discogs_collection_full.json discogs_backup_2026-02-08.json
```

### 2. Excel Power Features

After opening CSV in Excel:

**Conditional Formatting:**
- Highlight items over $50
- Color-code by condition
- Flag missing data

**Pivot Tables:**
- Count by format
- Total value by year
- Collection growth over time

**Filters:**
- Show only items to sell
- Find specific location
- Filter by genre/decade

### 3. Custom Analysis Columns

Add columns in Excel:
- Age: `=YEAR(TODAY()) - [year]`
- Value/Item: `=[lowest_price]` (already have this)
- Profit: `=[sold_price] - [purchase_price]`

### 4. Find Duplicates

Sort by artist + title to spot duplicates, then:
- Keep best condition
- Mark others to sell
- Or keep different pressings

### 5. Track Collection Value

- Export monthly
- Compare `lowest_price` column
- Track which items are appreciating
- Identify good selling opportunities

## 📚 Additional Resources

### Discogs Resources
- Custom Fields: https://www.discogs.com/settings/collection-fields
- API Documentation: https://www.discogs.com/developers
- Collection Management: https://www.discogs.com/my/collection

### Python Resources
- Install Python: https://www.python.org/downloads/
- VS Code Editor: https://code.visualstudio.com/

## 🆘 Getting Help

If you run into issues:

1. Check the error message - it usually tells you what's wrong
2. Verify your token is correct
3. Make sure username matches exactly
4. Check file paths (Windows vs Linux)
5. Try with a smaller test folder first

Common fixes:
- Token expired: Generate new one
- Username wrong: Check exact spelling
- File not found: Check working directory
- Rate limit: Script will pause automatically

## 📄 License

These scripts are provided as-is for personal use with your Discogs collection.

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

DisCat is **fork-friendly and minimal-support**. See [CONTRIBUTING.md](CONTRIBUTING.md).

- ✅ Forks encouraged - customize for your needs!
- ✅ Pull requests welcome - bug fixes and improvements
- ⚠️ Limited support - maintainer has limited time
- 📚 Documentation first - read docs before opening issues

## 🐛 Issues & Support

**Before opening an issue:**
1. Check [existing issues](../../issues)
2. Read the documentation (especially troubleshooting sections)
3. Try the latest version
4. Consider forking and fixing it yourself!

**This is a minimal-support project** - responses may be slow or not come at all.

## 🌟 Star History

If DisCat helps you organize your collection, consider giving it a star! ⭐

## 🐱 About DisCat

DisCat was created to make Discogs collection management easier. It's designed to be:
- Simple and hackable
- Fork-friendly
- Cross-platform (Windows/Mac/Linux)
- Well-documented

Happy collecting! 🎵
