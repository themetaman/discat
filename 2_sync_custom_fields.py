#!/usr/bin/env python3
"""
Script 2: SYNC CUSTOM FIELDS BACK
- Reads your downloaded collection data
- Updates custom field values in Discogs
- Always shows preview before syncing
- Validates dropdown values
"""

import requests
import json
import csv
import time
import os
from typing import Dict, List, Optional, Callable


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


class DiscogsCustomFieldSync:
    """Sync custom field values back to Discogs."""
    
    BASE_URL = "https://api.discogs.com"
    
    def __init__(self, user_token: str, username: str):
        self.user_token = user_token
        self.username = username
        self.headers = {
            'User-Agent': 'DiscogsCustomFieldSync/1.0',
            'Authorization': f'Discogs token={user_token}',
            'Content-Type': 'application/json'
        }
        self._custom_fields = None
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None) -> Dict:
        """Make API request."""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Rate limiting
            remaining = int(response.headers.get('X-Discogs-Ratelimit-Remaining', 60))
            if remaining < 10:
                print(f"   ⚠️  Rate limit low. Pausing...")
                time.sleep(60)
            
            response.raise_for_status()
            
            if response.status_code == 204:
                return {}
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {response.text}")
            raise
    
    def get_custom_fields(self) -> List[Dict]:
        """Get custom field definitions from Discogs."""
        if self._custom_fields:
            return self._custom_fields
        
        print("📋 Getting custom field definitions...")
        
        endpoint = f"/users/{self.username}/collection/fields"
        data = self._make_request('GET', endpoint)
        
        self._custom_fields = data.get('fields', [])
        
        print(f"✅ Found {len(self._custom_fields)} custom fields:")
        for field in self._custom_fields:
            field_type = field.get('type', 'text')
            print(f"   - {field['name']} (ID: {field['id']}, Type: {field_type})")
            if field_type == 'dropdown':
                print(f"     Options: {field.get('options', [])}")
        
        return self._custom_fields
    
    def update_custom_field(self, folder_id: int, release_id: int,
                           instance_id: int, field_id: int, value: str) -> Dict:
        """Update a single custom field value."""
        endpoint = (
            f"/users/{self.username}/collection/folders/{folder_id}/"
            f"releases/{release_id}/instances/{instance_id}/fields/{field_id}"
        )
        
        data = {'value': value}
        return self._make_request('POST', endpoint, data=data)
    
    def load_collection_data(self, filename: str = "discogs_collection_full.json") -> List[Dict]:
        """Load collection data from JSON file."""
        print(f"📂 Loading collection data from {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded {len(data)} items")
        return data
    
    def sync_from_metadata_extractor(self, 
                                    collection: List[Dict],
                                    field_name: str,
                                    metadata_extractor: Callable,
                                    skip_if_has_value: bool = False) -> Dict:
        """
        Sync custom field from a metadata extractor function.
        
        Returns dict with preview data and function to execute sync.
        """
        # Get field definition
        custom_fields = self.get_custom_fields()
        field_id = None
        field_type = None
        field_options = []
        
        for field in custom_fields:
            if field['name'] == field_name:
                field_id = field['id']
                field_type = field.get('type', 'text')
                field_options = field.get('options', [])
                break
        
        if field_id is None:
            print(f"\n❌ Custom field '{field_name}' not found!")
            print(f"Available: {[f['name'] for f in custom_fields]}")
            return None
        
        print(f"\n🔍 Analyzing sync to: {field_name}")
        print(f"   Type: {field_type}")
        if field_type == 'dropdown':
            print(f"   Options: {field_options}")
        
        # Analyze what would change
        changes = []
        skipped = []
        validation_errors = []
        
        for item in collection:
            # Extract new value
            new_value = metadata_extractor(item)
            if new_value is None:
                continue
            
            new_value = str(new_value)
            
            # Validate dropdown
            if field_type == 'dropdown' and new_value not in field_options:
                validation_errors.append({
                    'title': item['basic_information']['title'],
                    'value': new_value
                })
                continue
            
            # Get current value
            current_value = None
            for note in item.get('custom_field_values', []):
                if note.get('field_id') == field_id:
                    current_value = note.get('value')
                    break
            
            # Skip if has value and skip_if_has_value
            if skip_if_has_value and current_value:
                skipped.append({
                    'title': item['basic_information']['title'],
                    'current': current_value
                })
                continue
            
            # Only if changed
            if str(new_value) != str(current_value):
                changes.append({
                    'item': item,
                    'title': item['basic_information']['title'],
                    'current': current_value,
                    'new': new_value,
                    'folder_id': item['folder_id'],
                    'release_id': item['id'],
                    'instance_id': item['instance_id']
                })
        
        return {
            'field_name': field_name,
            'field_id': field_id,
            'field_type': field_type,
            'field_options': field_options,
            'changes': changes,
            'skipped': skipped,
            'validation_errors': validation_errors
        }
    
    def execute_sync(self, sync_plan: Dict) -> int:
        """Execute a sync plan."""
        changes = sync_plan['changes']
        field_id = sync_plan['field_id']
        field_name = sync_plan['field_name']
        
        print(f"\n🔄 Syncing {len(changes)} items to '{field_name}'...")
        
        updated = 0
        
        for idx, change in enumerate(changes, 1):
            try:
                print(f"   [{idx}/{len(changes)}] {change['title']} → '{change['new']}'")
                
                self.update_custom_field(
                    change['folder_id'],
                    change['release_id'],
                    change['instance_id'],
                    field_id,
                    change['new']
                )
                
                updated += 1
                time.sleep(1.5)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n✅ Updated {updated} items")
        return updated


# ==================== METADATA EXTRACTORS ====================

def extract_year(item: Dict) -> Optional[str]:
    """Extract release year."""
    year = item['basic_information'].get('year')
    return str(year) if year else None

def extract_decade(item: Dict) -> Optional[str]:
    """Calculate decade from year."""
    year = item['basic_information'].get('year')
    if year:
        return f"{(year // 10) * 10}s"
    return None

def extract_first_genre(item: Dict) -> Optional[str]:
    """Extract first genre."""
    detailed = item.get('detailed_metadata', {})
    genres = detailed.get('genres', [])
    return genres[0] if genres else None

def extract_format_simple(item: Dict) -> Optional[str]:
    """
    Simplify format to: Vinyl, CD, Cassette, Digital, or Other.
    For dropdown with exactly these options.
    """
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


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║                   DisCat 🐱                                    ║
║         Discogs Collection Manager - Sync Tool                ║
║         Updates Discogs custom fields from metadata            ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
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
    
    syncer = DiscogsCustomFieldSync(USER_TOKEN, USERNAME)
    
    # Load collection data
    collection = syncer.load_collection_data()
    
    # Get custom fields
    syncer.get_custom_fields()
    
    print("\n" + "="*70)
    print("EXAMPLE SYNC OPERATIONS")
    print("="*70)
    print("\nUncomment the operation you want to perform below.")
    print("Each operation shows a preview before syncing.\n")
    
    # ==================== EXAMPLE 1: Sync Year ====================
    # Uncomment to sync release year to a custom field called "Year"
    
    # print("\n" + "="*70)
    # print("SYNC: Year")
    # print("="*70)
    # 
    # plan = syncer.sync_from_metadata_extractor(
    #     collection=collection,
    #     field_name="Year",  # Must match your custom field name
    #     metadata_extractor=extract_year,
    #     skip_if_has_value=False
    # )
    # 
    # if plan and plan['changes']:
    #     print(f"\n📋 PREVIEW: Would update {len(plan['changes'])} items")
    #     print("\nFirst 10 changes:")
    #     for change in plan['changes'][:10]:
    #         print(f"  {change['title']}: '{change['current']}' → '{change['new']}'")
    #     
    #     if plan['validation_errors']:
    #         print(f"\n❌ {len(plan['validation_errors'])} validation errors")
    #         for err in plan['validation_errors'][:5]:
    #             print(f"  {err['title']}: '{err['value']}' not valid")
    #     
    #     user_input = input(f"\nSync {len(plan['changes'])} items? (yes/no): ").lower()
    #     if user_input == 'yes':
    #         syncer.execute_sync(plan)
    #     else:
    #         print("❌ Cancelled")
    
    
    # ==================== EXAMPLE 2: Sync Format ====================
    # Uncomment to sync simplified format to a dropdown field
    
    # print("\n" + "="*70)
    # print("SYNC: Format Type")
    # print("="*70)
    # 
    # plan = syncer.sync_from_metadata_extractor(
    #     collection=collection,
    #     field_name="Format",  # Must match your dropdown field name
    #     metadata_extractor=extract_format_simple,
    #     skip_if_has_value=False
    # )
    # 
    # if plan and plan['changes']:
    #     print(f"\n📋 PREVIEW: Would update {len(plan['changes'])} items")
    #     print("\nFirst 10 changes:")
    #     for change in plan['changes'][:10]:
    #         print(f"  {change['title']}: '{change['current']}' → '{change['new']}'")
    #     
    #     user_input = input(f"\nSync {len(plan['changes'])} items? (yes/no): ").lower()
    #     if user_input == 'yes':
    #         syncer.execute_sync(plan)
    #     else:
    #         print("❌ Cancelled")
    
    
    print("\n💡 To use this script:")
    print("1. Uncomment one of the EXAMPLE operations above")
    print("2. Change field_name to match your custom field")
    print("3. Run the script")
    print("4. Review the preview")
    print("5. Type 'yes' to sync or 'no' to cancel")
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
