# DisCat 🐱 - Caching Guide

**Speed Up Your Downloads with Smart Caching**

## 🚀 What is Caching?

Caching stores your collection data locally so subsequent downloads only fetch **new or changed items**.

**Result:** Downloads go from 15-20 minutes to just 2 minutes! ⚡

---

## How It Works

### First Download (No Cache)
```
📚 Downloading 656 items...
🔍 Getting custom field values... (656 API calls)
🔄 Enriching with metadata... (656 API calls)
⏱️ Time: ~15-20 minutes
```

### Second Download (With Cache)
```
📦 Loaded cache: 656 items

📊 Analyzing changes:
  New items: 5
  Changed items: 2
  Unchanged items: 649

🔍 Getting custom field values for 7 items... (7 API calls)
🔄 Enriching 7 items... (7 API calls)
⏱️ Time: ~2 minutes! 🚀
```

---

## Using Cache

### GUI

**Enable (default):**
```
☑️ Check "Use cache (only fetch new/changed items)"
```

**Disable:**
```
☐ Uncheck "Use cache"
```

### Command Line

**With cache (fast):**
```cmd
python 1_download_collection.py -c
```

**Without cache (full download):**
```cmd
python 1_download_collection.py
```

**Clear cache:**
```cmd
python 1_download_collection.py --clear-cache
```

---

## What Gets Cached?

Everything:
- ✅ Basic metadata (artist, title, year, format)
- ✅ Custom field values
- ✅ Full metadata (genres, styles, credits, tracklist)
- ✅ Community stats (have/want counts)
- ✅ Marketplace pricing
- ✅ Everything!

---

## Cache Detection

The cache compares:
1. **instance_id** - Unique ID for each item in your collection
2. **date_added** - Timestamp when added/modified in Discogs

If either changed → Item is re-fetched
If both match → Cached data is used

---

## Speed Comparison

| Scenario | Without Cache | With Cache |
|----------|---------------|------------|
| **No changes** | 15-20 min | **30 sec** ⚡ |
| **5 new items** | 15-20 min | **2 min** ⚡ |
| **50 new items** | 15-20 min | **5 min** ⚡ |
| **Everything changed** | 15-20 min | 15-20 min |

---

## Cache File

**Location:** `discogs_cache.json` (same directory as scripts)

**Size:** ~10-50 MB for 656 items (depends on metadata depth)

**Format:**
```json
{
  "items": {
    "123456": { /* full item data */ },
    "789012": { /* full item data */ },
    ...
  },
  "last_updated": "2026-02-08T13:50:50.123456"
}
```

---

## When to Use Cache

### ✅ Use Cache When:
- Regular updates (weekly/monthly)
- Tracking price changes
- Checking for new additions
- Normal collection management
- **Most of the time!**

### ❌ Don't Use Cache When:
- First download ever
- Testing/debugging
- Want to re-fetch everything
- Suspect cache corruption

---

## When to Clear Cache

Clear the cache if:
1. **Prices outdated** - Want fresh marketplace data for all items
2. **Cache corrupted** - File damaged or wrong format
3. **Major changes** - Reorganized collection in Discogs
4. **Testing** - Comparing cache vs non-cache behavior

**How to clear:**
```cmd
# Command line
python 1_download_collection.py --clear-cache

# Or manually delete
del discogs_cache.json  (Windows)
rm discogs_cache.json   (Mac/Linux)
```

---

## Cache Safety

**Q: What if I delete items from Discogs?**
A: Next download detects they're gone and removes from cache

**Q: What if cache is corrupted?**
A: Script falls back to full download automatically

**Q: What if I move the cache file?**
A: Put it in same directory as scripts, or script creates new one

**Q: Does cache expire?**
A: No, it's valid forever (until you clear it)

---

## Example Workflow

### Monthly Collection Management

**Week 1 (Full download):**
```cmd
python 1_download_collection.py -c
```
Time: 15-20 min (builds cache)

**Week 2 (5 new items):**
```cmd
python 1_download_collection.py -c
```
Time: 2 min ⚡

**Week 3 (No changes):**
```cmd
python 1_download_collection.py -c
```
Time: 30 sec ⚡⚡

**Week 4 (10 new items):**
```cmd
python 1_download_collection.py -c
```
Time: 3 min ⚡

**Month end (refresh all prices):**
```cmd
python 1_download_collection.py --clear-cache
python 1_download_collection.py -c
```
Time: 15-20 min (rebuilds cache with fresh data)

---

## Troubleshooting

### "Cache shows old prices"

**Cause:** Using cached data, no changes detected
**Solution:** Clear cache to force refresh

```cmd
python 1_download_collection.py --clear-cache
```

### "Cache file is huge"

**Cause:** Full metadata includes tracklists, credits
**Solution:** Normal! Cache includes everything. Delete if space is tight.

### "Download still slow with cache"

**Cause:** Many new/changed items
**Solution:** This is normal - cache only helps when few changes

### "Cache not updating"

**Cause:** Items haven't changed in Discogs
**Solution:** Working correctly! Only fetches changed items.

---

## Advanced: Cache Internals

The cache stores items by `instance_id`:
```json
{
  "items": {
    "123456": {
      "instance_id": 123456,
      "id": 789,
      "folder_id": 0,
      "date_added": "2024-01-15T10:30:00",
      "basic_information": { ... },
      "detailed_metadata": { ... },
      "custom_field_values": [ ... ]
    }
  },
  "last_updated": "2026-02-08T13:50:50.123456"
}
```

**Detection logic:**
```python
if instance_id not in cache:
    → NEW ITEM → Fetch
elif date_added != cache[instance_id].date_added:
    → CHANGED ITEM → Fetch
else:
    → UNCHANGED → Use cache
```

---

## Summary

✅ **Always use cache** (`-c` flag) for regular updates
✅ **Clear cache monthly** to refresh all marketplace data
✅ **Cache is automatic** - no manual management needed
✅ **Speed boost is huge** - 5-10x faster!

Happy collecting! 🎵
