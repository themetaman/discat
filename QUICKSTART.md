# DisCat 🐱 - Quick Start Guide

**Discogs Collection Manager - Get Started in 5 Minutes**

## 🚀 5-Minute Setup

### Method 1: GUI (Easiest)

1. **Get Python**: Download from python.org (check "Add to PATH")
2. **Install requests**: `pip install requests`
3. **Get Discogs token**: https://www.discogs.com/settings/developers
4. **Run GUI**: `python discogs_gui.py`
5. **Enter credentials**: Settings tab → Enter token/username → Save
6. **Download**: Download tab → Click "Download Collection"

Done! Your CSV is ready in minutes.

---

### Method 2: Command Line

1. **Get Python**: Download from python.org
2. **Install requests**: `pip install requests`
3. **Get Discogs token**: https://www.discogs.com/settings/developers
4. **Edit script**: Open `1_download_collection.py`, add token/username
5. **Run**: `python 1_download_collection.py -c`

---

## 📋 10 Common Use Cases

### 1. Weekly Collection Updates (with cache)

**Command Line:**
```cmd
python 1_download_collection.py -c
```

**Result:** ~2 minutes (only fetches changes)

---

### 2. Complete Download with Everything

**GUI:** ✅ Check all options, click Download
**Result:** CSV with genres, styles, credits, pricing (~15-20 min)

---

### 3. Sync Release Year to Custom Field

1. Create "Year" custom field in Discogs
2. GUI → Sync tab → Field: "Year", Select: "Year"
3. Preview → Execute

---

### 4. Track Collection Value Over Time

Monthly snapshots:
```
discogs_collection_20260101_120000.csv
discogs_collection_20260201_120000.csv
```
Compare `price_low` columns!

---

### 5. Find Most Valuable Items

Excel: Sort by `price_low` (descending)

---

### 6. Organize by Folder

Excel: Filter `folder_name` column

---

### 7. Sync Styles

1. Create "Style" dropdown in Discogs
2. GUI → Sync → "First Style" or "All Styles"

---

### 8. Export for DJ Software

Custom fields: BPM, Key, Energy
Download with cache flag for quick updates

---

### 9. Find Items to Sell

Excel: Filter high `price_low` + low `community_want`

---

### 10. Compare to Market

Download weekly, compare `price_low` and `num_for_sale` changes

---

## ⚡ Pro Tips

- **First download**: ~15-20 min
- **With cache (`-c`)**: ~2 min!
- **Files are timestamped**: Easy to track history
- **Clear cache when needed**: `--clear-cache` flag

---

## 🆘 Quick Fixes

- **429 Error**: Script auto-pauses, just wait
- **404 Error**: Auto-fallback to master release
- **Validation errors**: Check "Ignore validation errors"
- **Slow?**: Use `-c` cache flag!

Enjoy! 🎵
