#!/usr/bin/env python3
"""
Script 1: DOWNLOAD EVERYTHING
- Downloads your Discogs collection
- Gets full metadata for each release
- Gets your custom field values
- Exports to CSV and JSON
- Generates summary report
- Supports incremental caching for faster updates
"""

import requests
import json
import time
import csv
import argparse
import os
from typing import Dict, List, Optional
from datetime import datetime


def load_env_config():
    """Load configuration from config.env file if it exists (no dependencies)."""
    config = {}
    env_file = 'config.env'
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


class DiscogsDownloader:
    """Download complete Discogs collection with all metadata and custom fields."""
    
    BASE_URL = "https://api.discogs.com"
    
    def __init__(self, user_token: str, username: str):
        self.user_token = user_token
        self.username = username
        self.headers = {
            'User-Agent': 'DiscogsDownloader/1.0',
            'Authorization': f'Discogs token={user_token}'
        }
        self.cache_file = 'discogs_cache.json'
    
    def load_cache(self) -> Dict:
        """Load cached collection data."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                print(f"📦 Loaded cache: {len(cache.get('items', {}))} items from {cache.get('last_updated')}")
                return cache
            except Exception as e:
                print(f"⚠️  Failed to load cache: {e}")
                return {'items': {}, 'last_updated': None}
        return {'items': {}, 'last_updated': None}
    
    def save_cache(self, collection: List[Dict]) -> None:
        """Save collection to cache."""
        cache = {
            'items': {str(item['instance_id']): item for item in collection},
            'last_updated': datetime.now().isoformat()
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved cache: {len(collection)} items")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a GET request with smart rate limiting."""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Smart rate limiting based on actual API headers
            remaining = int(response.headers.get('X-Discogs-Ratelimit-Remaining', 60))
            
            # Only pause if getting low
            if remaining < 5:
                print(f"   ⚠️  Rate limit low ({remaining} remaining). Pausing 60 seconds...")
                time.sleep(60)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
            raise
    
    def get_collection(self, folder_id: int = 0) -> List[Dict]:
        """Get basic collection items."""
        print(f"📚 Downloading collection for: {self.username}")
        
        all_items = []
        page = 1
        
        while True:
            print(f"   Page {page}...")
            
            endpoint = f"/users/{self.username}/collection/folders/{folder_id}/releases"
            params = {'page': page, 'per_page': 100}
            
            data = self._make_request(endpoint, params)
            releases = data.get('releases', [])
            
            if not releases:
                break
            
            all_items.extend(releases)
            
            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break
            
            page += 1
            time.sleep(1)
        
        print(f"✅ Downloaded {len(all_items)} items")
        return all_items
    
    def get_folders(self) -> Dict[int, str]:
        """Get folder names mapped by ID."""
        print("\n📁 Getting folders...")
        endpoint = f"/users/{self.username}/collection/folders"
        data = self._make_request(endpoint)
        folders = {f['id']: f['name'] for f in data.get('folders', [])}
        print(f"✅ Found {len(folders)} folders: {list(folders.values())}")
        return folders
    
    def get_custom_fields(self) -> List[Dict]:
        """Get custom field definitions."""
        print("\n📋 Getting custom field definitions...")
        
        endpoint = f"/users/{self.username}/collection/fields"
        data = self._make_request(endpoint)
        
        fields = data.get('fields', [])
        
        if fields:
            print(f"✅ Found {len(fields)} custom fields:")
            for field in fields:
                print(f"   - {field['name']} (Type: {field.get('type')})")
        else:
            print("ℹ️  No custom fields found")
        
        return fields
    
    def get_custom_field_values(self, collection: List[Dict]) -> List[Dict]:
        """Get custom field values for each item."""
        print(f"\n🔍 Getting custom field values for {len(collection)} items...")
        print("   (This requires one API call per item)")
        
        enriched = []
        start_time = time.time()
        
        for idx, item in enumerate(collection, 1):
            if idx % 50 == 0:
                elapsed = time.time() - start_time
                rate = idx / elapsed * 60
                print(f"   Progress: {idx}/{len(collection)} (~{rate:.0f} requests/min)")
            
            try:
                endpoint = (
                    f"/users/{self.username}/collection/folders/"
                    f"{item['folder_id']}/releases/{item['id']}/instances/{item['instance_id']}"
                )
                
                instance_data = self._make_request(endpoint)
                item['custom_field_values'] = instance_data.get('notes', [])
                enriched.append(item)
                
                # Faster delay - let rate limit monitoring handle pauses
                time.sleep(0.7)
                
            except Exception as e:
                print(f"   ⚠️  Error on item {idx}: {e}")
                item['custom_field_values'] = []
                enriched.append(item)
        
        print(f"✅ Got custom field values for {len(enriched)} items")
        return enriched
    
    def get_release_details(self, release_id: int) -> Dict:
        """Get full metadata for a release."""
        endpoint = f"/releases/{release_id}"
        return self._make_request(endpoint)
    
    def enrich_with_metadata(self, collection: List[Dict]) -> List[Dict]:
        """Add full Discogs metadata to each item."""
        print(f"\n🔄 Enriching {len(collection)} items with full metadata...")
        print("   (This is slow - one API call per release)")
        
        enriched = []
        start_time = time.time()
        
        for idx, item in enumerate(collection, 1):
            print(f"   [{idx}/{len(collection)}] {item['basic_information']['title']}")
            
            release_id = item['basic_information']['id']
            master_id = item['basic_information'].get('master_id')
            
            try:
                detailed = self.get_release_details(release_id)
                item['detailed_metadata'] = detailed
                enriched.append(item)
                
            except requests.exceptions.HTTPError as e:
                # If 404, try master release instead
                if e.response.status_code == 404 and master_id:
                    print(f"   ⚠️  Release 404, trying master {master_id}...")
                    try:
                        master_endpoint = f"/masters/{master_id}"
                        detailed = self._make_request(master_endpoint)
                        item['detailed_metadata'] = detailed
                        enriched.append(item)
                    except Exception as master_error:
                        print(f"   ⚠️  Master also failed: {master_error}")
                        item['detailed_metadata'] = {}
                        enriched.append(item)
                else:
                    print(f"   ⚠️  Error: {e}")
                    item['detailed_metadata'] = {}
                    enriched.append(item)
                    
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                item['detailed_metadata'] = {}
                enriched.append(item)
            
            # Smarter pacing
            if idx % 10 == 0:
                # Every 10 requests, check our rate
                elapsed = time.time() - start_time
                rate = idx / elapsed * 60
                print(f"   Rate: ~{rate:.0f} requests/min")
                # Small pause to stay safe
                time.sleep(2)
            else:
                # Faster between batches
                time.sleep(0.8)
        
        print(f"✅ Enriched {len(enriched)} items")
        return enriched
    
    def export_to_csv(self, collection: List[Dict], custom_fields: List[Dict], 
                     folders: Dict[int, str], filename: str = "discogs_collection.csv") -> str:
        """Export everything to CSV."""
        print(f"\n📤 Exporting to {filename}...")
        
        # Build field name map
        field_map = {f['id']: f['name'] for f in custom_fields}
        
        rows = []
        download_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for item in collection:
            basic = item['basic_information']
            detailed = item.get('detailed_metadata', {})
            
            # Get folder name
            folder_id = item.get('folder_id', 0)
            folder_name = folders.get(folder_id, 'Unknown')
            
            row = {
                # Download timestamp
                'download_date': download_timestamp,
                
                # IDs
                'release_id': basic['id'],
                'instance_id': item['instance_id'],
                'master_id': basic.get('master_id'),
                
                # Folder
                'folder_id': folder_id,
                'folder_name': folder_name,
                
                # Basic info
                'artist': ', '.join([a['name'] for a in basic.get('artists', [])]),
                'title': basic['title'],
                'year': basic.get('year'),
                'format': ', '.join([f['name'] for f in basic.get('formats', []) if f.get('name')]),
                'label': ', '.join([l['name'] for l in basic.get('labels', []) if l.get('name')]),
                'catalog_number': ', '.join([l['catno'] for l in basic.get('labels', []) if l.get('catno')]),
                
                # Collection info
                'date_added': item.get('date_added'),
                'rating': item.get('rating'),
                
                # Detailed metadata
                'genres': ', '.join(detailed.get('genres', [])),
                'styles': ', '.join(detailed.get('styles', [])),
                'country': detailed.get('country'),
                'released': detailed.get('released'),
                'notes': detailed.get('notes'),
                
                # Community stats
                'community_have': detailed.get('community', {}).get('have'),
                'community_want': detailed.get('community', {}).get('want'),
                
                # Marketplace pricing
                'price_low': detailed.get('lowest_price'),
                'price_median': detailed.get('community', {}).get('rating', {}).get('average'),
                'num_for_sale': detailed.get('num_for_sale'),
                
                # Tracklist
                'track_count': len(detailed.get('tracklist', [])),
                'tracklist': json.dumps(detailed.get('tracklist', [])),
                
                # Credits
                'credits': json.dumps(detailed.get('extraartists', [])),
                
                # Identifiers (barcodes, matrix numbers, etc.)
                'identifiers': json.dumps(detailed.get('identifiers', [])),
            }
            
            # Add custom field values with proper names
            for note in item.get('custom_field_values', []):
                field_id = note.get('field_id')
                field_name = field_map.get(field_id, f'custom_field_{field_id}')
                row[field_name] = note.get('value')
            
            rows.append(row)
        
        # Get all fieldnames
        fieldnames = set()
        for row in rows:
            fieldnames.update(row.keys())
        fieldnames = sorted(list(fieldnames))
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✅ Exported {len(rows)} items to {filename}")
        return filename
    
    def save_json(self, data, filename: str) -> str:
        """Save to JSON."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to {filename}")
        return filename
    
    def generate_report(self, collection: List[Dict]) -> str:
        """Generate summary report."""
        print("\n📊 Generating report...")
        
        total = len(collection)
        
        # Count by format
        formats = {}
        for item in collection:
            fmt = ', '.join([f['name'] for f in item['basic_information'].get('formats', []) if f.get('name')])
            if fmt:
                formats[fmt] = formats.get(fmt, 0) + 1
        
        # Count by year
        years = {}
        for item in collection:
            year = item['basic_information'].get('year')
            if year:
                years[year] = years.get(year, 0) + 1
        
        # Count by label
        labels = {}
        for item in collection:
            for label in item['basic_information'].get('labels', []):
                name = label.get('name')
                if name:
                    labels[name] = labels.get(name, 0) + 1
        
        # Count by genre
        genres = {}
        for item in collection:
            detailed = item.get('detailed_metadata', {})
            for genre in detailed.get('genres', []):
                genres[genre] = genres.get(genre, 0) + 1
        
        # Build report
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║           DISCOGS COLLECTION SUMMARY REPORT                    ║
╚════════════════════════════════════════════════════════════════╝

📊 OVERVIEW
───────────────────────────────────────────────────────────────────
Total Items:        {total}
Generated:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Username:           {self.username}

📀 TOP 10 FORMATS
───────────────────────────────────────────────────────────────────
"""
        for fmt, count in sorted(formats.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"{fmt[:50]:50s} {count:5d}\n"
        
        report += f"""
📅 TOP 10 YEARS
───────────────────────────────────────────────────────────────────
"""
        for year, count in sorted(years.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"{str(year):50s} {count:5d}\n"
        
        report += f"""
🏷️  TOP 10 LABELS
───────────────────────────────────────────────────────────────────
"""
        for label, count in sorted(labels.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"{label[:50]:50s} {count:5d}\n"
        
        if genres:
            report += f"""
🎵 TOP 10 GENRES
───────────────────────────────────────────────────────────────────
"""
            for genre, count in sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]:
                report += f"{genre[:50]:50s} {count:5d}\n"
        
        return report


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║                   DisCat 🐱                                    ║
║         Discogs Collection Manager - Download Tool            ║
║         Downloads metadata + custom fields                     ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download Discogs collection with optional caching')
    parser.add_argument('-c', '--use-cache', action='store_true', 
                       help='Use cache for incremental updates (only fetch new/changed items)')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear cache and force full download')
    args = parser.parse_args()
    
    # Load configuration from config.env if it exists
    env_config = load_env_config()
    
    # Configuration (from config.env or hardcoded)
    USER_TOKEN = env_config.get('DISCOGS_TOKEN', "YOUR_DISCOGS_TOKEN_HERE")
    USERNAME = env_config.get('DISCOGS_USERNAME', "YOUR_USERNAME_HERE")
    
    if USER_TOKEN == "YOUR_DISCOGS_TOKEN_HERE":
        print("⚠️  Please configure credentials!")
        print("\nThree ways to configure:")
        print("  1. Create config.env (copy from config.env.example)")
        print("  2. Edit this script and set USER_TOKEN and USERNAME")
        print("  3. Use the GUI (python discogs_gui.py)")
        return
    
    downloader = DiscogsDownloader(USER_TOKEN, USERNAME)
    
    # Clear cache if requested
    if args.clear_cache:
        if os.path.exists(downloader.cache_file):
            os.remove(downloader.cache_file)
            print("🗑️  Cache cleared!")
    
    # Load cache if using it
    cached_items = {}
    if args.use_cache:
        cache = downloader.load_cache()
        cached_items = cache.get('items', {})
    
    # Step 1: Get folders
    folders = downloader.get_folders()
    
    # Step 2: Get collection
    collection = downloader.get_collection()
    
    # Step 3: Determine what's new/changed
    new_items = []
    changed_items = []
    unchanged_items = []
    
    if args.use_cache and cached_items:
        print("\n📊 Analyzing changes...")
        for item in collection:
            instance_id = str(item['instance_id'])
            
            if instance_id not in cached_items:
                new_items.append(item)
            elif (item.get('date_added') != cached_items[instance_id].get('date_added') or
                  item.get('folder_id') != cached_items[instance_id].get('folder_id')):
                changed_items.append(item)
            else:
                unchanged_items.append(cached_items[instance_id])
        
        print(f"  New items: {len(new_items)}")
        print(f"  Changed items: {len(changed_items)}")
        print(f"  Unchanged items: {len(unchanged_items)}")
        
        items_to_fetch = new_items + changed_items
        
        if not items_to_fetch:
            print("\n✅ No new or changed items - using cached data!")
            collection = list(cached_items.values())
        else:
            print(f"\n🔄 Will fetch data for {len(items_to_fetch)} items")
            collection = items_to_fetch
    
    # Step 4: Get custom fields (only for new/changed if using cache)
    custom_fields = downloader.get_custom_fields()
    
    # Step 5: Get custom field values
    if custom_fields and (not args.use_cache or new_items or changed_items):
        collection = downloader.get_custom_field_values(collection)
    
    # Step 6: Get full metadata
    if not args.use_cache or new_items or changed_items:
        print("\n" + "="*70)
        if args.use_cache:
            print(f"This will fetch detailed metadata for {len(collection)} new/changed items.")
            print(f"Estimated time: ~{len(collection) * 1.5 / 60:.0f} minutes.")
        else:
            print("This next step fetches detailed metadata for each release.")
            print(f"For {len(collection)} items, this will take approximately {len(collection) * 1.5 / 60:.0f} minutes.")
        
        user_input = input("Continue? (y/n): ").lower()
        
        if user_input == 'y':
            collection = downloader.enrich_with_metadata(collection)
        else:
            print("⏭️  Skipping metadata enrichment")
    
    # Combine with unchanged items if using cache
    if args.use_cache and unchanged_items:
        print(f"\n🔗 Combining {len(collection)} fetched items with {len(unchanged_items)} cached items...")
        collection = collection + unchanged_items
    
    # Save to cache
    if args.use_cache:
        downloader.save_cache(collection)
    
    # Step 7: Export
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = downloader.export_to_csv(collection, custom_fields, folders, f"discogs_collection_{timestamp}.csv")
    json_file = downloader.save_json(collection, f"discogs_collection_{timestamp}.json")
    
    # Also save as "latest" for sync script
    downloader.save_json(collection, "discogs_collection_full.json")
    
    # Step 8: Generate report
    report = downloader.generate_report(collection)
    print("\n" + report)
    
    with open("discogs_report.txt", "w", encoding='utf-8') as f:
        f.write(report)
    print("💾 Report saved to discogs_report.txt")
    
    print("\n✅ DOWNLOAD COMPLETE!")
    print(f"\nFiles created:")
    print(f"  - {csv_file} (Open in Excel)")
    print(f"  - {json_file} (Complete backup)")
    print(f"  - discogs_report.txt (Summary)")
    if args.use_cache:
        print(f"  - {downloader.cache_file} (Cache for next time)")
    print(f"\nYour CSV includes:")
    print(f"  ✓ All Discogs metadata")
    if custom_fields:
        print(f"  ✓ All custom field values")
    if args.use_cache:
        print(f"\n💡 Next time, use -c flag for faster incremental updates!")


if __name__ == "__main__":
    main()
