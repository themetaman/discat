#!/usr/bin/env python3
"""
Discogs Collection Manager - GUI Application

Simple Windows desktop app for managing your Discogs collection.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import requests
import json
import csv
import time
from typing import Dict, List, Optional
from datetime import datetime
import os


class DiscogsGUI:
    """GUI Application for Discogs Collection Manager."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DisCat - Discogs Collection Manager")
        self.root.geometry("800x700")
        
        # Variables
        self.token_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.download_thread = None
        self.sync_thread = None
        
        # Load saved credentials if they exist
        self.load_credentials()
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI widgets."""
        
        # Main notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Download
        download_tab = ttk.Frame(notebook)
        notebook.add(download_tab, text='📥 Download Collection')
        self.create_download_tab(download_tab)
        
        # Tab 2: Sync
        sync_tab = ttk.Frame(notebook)
        notebook.add(sync_tab, text='🔄 Sync Custom Fields')
        self.create_sync_tab(sync_tab)
        
        # Tab 3: Settings
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text='⚙️ Settings')
        self.create_settings_tab(settings_tab)
    
    def create_download_tab(self, parent):
        """Create the download tab."""
        
        # Frame for download options
        options_frame = ttk.LabelFrame(parent, text="Download Options", padding=10)
        options_frame.pack(fill='x', padx=10, pady=10)
        
        # Checkboxes
        self.include_custom_fields_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Include custom field values (slower)",
            variable=self.include_custom_fields_var
        ).pack(anchor='w')
        
        self.include_metadata_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Include full metadata (very slow - genres, credits, tracklist)",
            variable=self.include_metadata_var
        ).pack(anchor='w')
        
        self.use_cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Use cache (only fetch new/changed items - MUCH faster)",
            variable=self.use_cache_var
        ).pack(anchor='w')
        
        self.generate_report_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Generate summary report",
            variable=self.generate_report_var
        ).pack(anchor='w')
        
        # Output location
        output_frame = ttk.Frame(options_frame)
        output_frame.pack(fill='x', pady=5)
        
        ttk.Label(output_frame, text="Save to:").pack(side='left')
        self.output_dir_var = tk.StringVar(value=os.getcwd())
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=40).pack(side='left', padx=5)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_dir).pack(side='left')
        
        # Download button
        self.download_btn = ttk.Button(
            options_frame,
            text="⬇️ Download Collection",
            command=self.start_download,
            style='Accent.TButton'
        )
        self.download_btn.pack(pady=10)
        
        # Progress
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.download_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.download_progress.pack(fill='x', pady=5)
        
        self.download_status = tk.StringVar(value="Ready to download")
        ttk.Label(progress_frame, textvariable=self.download_status).pack(anchor='w')
        
        # Log
        ttk.Label(progress_frame, text="Log:").pack(anchor='w', pady=(10, 0))
        self.download_log = scrolledtext.ScrolledText(progress_frame, height=15, state='disabled')
        self.download_log.pack(fill='both', expand=True)
    
    def create_sync_tab(self, parent):
        """Create the sync tab."""
        
        # Main container with better proportions
        main_container = ttk.Frame(parent)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Top section - Info (compact)
        info_frame = ttk.LabelFrame(main_container, text="ℹ️ How to Sync", padding=5)
        info_frame.pack(fill='x', pady=(0, 10))
        
        info_text = "1. Download collection  2. Create custom fields  3. Select field & metadata  4. Preview  5. Execute"
        ttk.Label(info_frame, text=info_text, font=('TkDefaultFont', 9)).pack(anchor='w')
        
        # Middle section - Sync configuration (compact)
        config_frame = ttk.LabelFrame(main_container, text="Sync Configuration", padding=10)
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Field selection - horizontal layout
        field_row = ttk.Frame(config_frame)
        field_row.pack(fill='x', pady=(0, 5))
        
        ttk.Label(field_row, text="Custom field:", width=12).pack(side='left')
        self.sync_field_var = tk.StringVar()
        self.sync_field_entry = ttk.Entry(field_row, textvariable=self.sync_field_var, width=25)
        self.sync_field_entry.pack(side='left', padx=5)
        ttk.Button(field_row, text="List Fields", command=self.list_custom_fields).pack(side='left')
        
        # Metadata source - compact grid layout
        ttk.Label(config_frame, text="Sync from metadata:", font=('TkDefaultFont', 9, 'bold')).pack(anchor='w', pady=(5, 2))
        
        self.sync_source_var = tk.StringVar(value="year")
        
        # Grid of radio buttons - 3 columns
        grid_frame = ttk.Frame(config_frame)
        grid_frame.pack(fill='x', pady=5)
        
        sources = [
            ("Year", "year"),
            ("Decade", "decade"),
            ("Country", "country"),
            ("First Genre", "first_genre"),
            ("All Genres", "all_genres"),
            ("First Style", "first_style"),
            ("All Styles", "all_styles"),
            ("Format (simple)", "format_simple"),
            ("Format (full)", "format_full"),
            ("Label", "label"),
            ("Catalog #", "catalog_number"),
            ("Price Low", "price_low"),
            ("# For Sale", "num_for_sale"),
            ("Have Count", "community_have"),
            ("Want Count", "community_want"),
        ]
        
        # Create 3 columns
        for i in range(3):
            col = ttk.Frame(grid_frame)
            col.pack(side='left', fill='both', expand=True, padx=5)
            
            # Add sources to this column
            start_idx = i * 5
            end_idx = min(start_idx + 5, len(sources))
            
            for text, value in sources[start_idx:end_idx]:
                ttk.Radiobutton(
                    col,
                    text=text,
                    variable=self.sync_source_var,
                    value=value
                ).pack(anchor='w')
        
        # Note
        ttk.Label(
            config_frame,
            text="ℹ️ Genres/Styles/Country/Community need 'full metadata' download",
            foreground='blue',
            font=('TkDefaultFont', 8)
        ).pack(anchor='w', pady=(5, 0))
        
        # Options - horizontal checkboxes
        options_row = ttk.Frame(config_frame)
        options_row.pack(fill='x', pady=(10, 0))
        
        self.sync_skip_existing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_row,
            text="Skip items with values",
            variable=self.sync_skip_existing_var
        ).pack(side='left', padx=(0, 20))
        
        self.sync_ignore_errors_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_row,
            text="Ignore validation errors",
            variable=self.sync_ignore_errors_var
        ).pack(side='left')
        
        # Buttons
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        self.preview_btn = ttk.Button(
            btn_frame,
            text="👁️ Preview Sync",
            command=self.preview_sync
        )
        self.preview_btn.pack(side='left', padx=(0, 10))
        
        self.execute_btn = ttk.Button(
            btn_frame,
            text="✅ Execute Sync",
            command=self.execute_sync,
            state='disabled'
        )
        self.execute_btn.pack(side='left')
        
        # Bottom section - Log (takes remaining space)
        log_frame = ttk.LabelFrame(main_container, text="Preview / Log", padding=5)
        log_frame.pack(fill='both', expand=True)
        
        self.sync_log = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.sync_log.pack(fill='both', expand=True)
        
        self.sync_plan = None  # Store sync plan for execution
    
    def create_settings_tab(self, parent):
        """Create the settings tab."""
        
        # Credentials frame
        cred_frame = ttk.LabelFrame(parent, text="Discogs Credentials", padding=10)
        cred_frame.pack(fill='x', padx=10, pady=10)
        
        # Token
        token_frame = ttk.Frame(cred_frame)
        token_frame.pack(fill='x', pady=5)
        
        ttk.Label(token_frame, text="API Token:", width=15).pack(side='left')
        self.token_entry = ttk.Entry(token_frame, textvariable=self.token_var, width=50, show='*')
        self.token_entry.pack(side='left', padx=5)
        ttk.Button(token_frame, text="Show", command=self.toggle_token).pack(side='left')
        
        # Username
        user_frame = ttk.Frame(cred_frame)
        user_frame.pack(fill='x', pady=5)
        
        ttk.Label(user_frame, text="Username:", width=15).pack(side='left')
        ttk.Entry(user_frame, textvariable=self.username_var, width=50).pack(side='left', padx=5)
        
        # Save button
        ttk.Button(cred_frame, text="💾 Save Credentials", command=self.save_credentials).pack(pady=10)
        
        # Help frame
        help_frame = ttk.LabelFrame(parent, text="Getting Your API Token", padding=10)
        help_frame.pack(fill='x', padx=10, pady=10)
        
        help_text = """1. Go to: https://www.discogs.com/settings/developers
2. Click 'Generate new token'
3. Copy the token and paste it above
4. Enter your Discogs username
5. Click 'Save Credentials'

Your credentials are saved locally and never shared."""
        
        ttk.Label(help_frame, text=help_text, justify='left').pack(anchor='w')
        
        # About frame
        about_frame = ttk.LabelFrame(parent, text="About", padding=10)
        about_frame.pack(fill='x', padx=10, pady=10)
        
        about_text = """DisCat 🐱 - Discogs Collection Manager
Version 1.0

A simple tool to download and manage your Discogs collection.

• Download complete collection with metadata
• Sync metadata to custom fields
• Export to CSV for Excel analysis

DisCat makes managing your music collection purr-fect! 🎵"""
        
        ttk.Label(about_frame, text=about_text, justify='left').pack(anchor='w')
    
    # Helper methods
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def toggle_token(self):
        """Toggle token visibility."""
        current_show = self.token_entry.cget('show')
        if current_show == '*':
            self.token_entry.configure(show='')
        else:
            self.token_entry.configure(show='*')
    
    def save_credentials(self):
        """Save credentials to file."""
        creds = {
            'token': self.token_var.get(),
            'username': self.username_var.get()
        }
        
        try:
            with open('discogs_credentials.json', 'w') as f:
                json.dump(creds, f)
            messagebox.showinfo("Success", "Credentials saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save credentials: {e}")
    
    def load_credentials(self):
        """Load credentials from file."""
        try:
            if os.path.exists('discogs_credentials.json'):
                with open('discogs_credentials.json', 'r') as f:
                    creds = json.load(f)
                self.token_var.set(creds.get('token', ''))
                self.username_var.set(creds.get('username', ''))
        except:
            pass
    
    def log_message(self, widget, message):
        """Add message to log widget."""
        widget.configure(state='normal')
        widget.insert('end', message + '\n')
        widget.see('end')
        widget.configure(state='disabled')
        self.root.update()
    
    def list_custom_fields(self):
        """List available custom fields."""
        if not self.validate_credentials():
            return
        
        try:
            downloader = DiscogsDownloader(self.token_var.get(), self.username_var.get(), self)
            fields = downloader.get_custom_fields()
            
            if fields:
                field_names = [f['name'] for f in fields]
                message = "Available custom fields:\n\n" + "\n".join(f"• {name}" for name in field_names)
                messagebox.showinfo("Custom Fields", message)
            else:
                messagebox.showinfo("Custom Fields", "No custom fields found.\n\nCreate them at:\nhttps://www.discogs.com/settings/collection-fields")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get custom fields: {e}")
    
    def validate_credentials(self):
        """Validate that credentials are set."""
        if not self.token_var.get() or not self.username_var.get():
            messagebox.showwarning(
                "Missing Credentials",
                "Please enter your API token and username in the Settings tab first."
            )
            return False
        return True
    
    # Download methods
    
    def start_download(self):
        """Start download in background thread."""
        if not self.validate_credentials():
            return
        
        # Disable button
        self.download_btn.configure(state='disabled')
        self.download_progress.start()
        self.download_status.set("Downloading...")
        
        # Clear log
        self.download_log.configure(state='normal')
        self.download_log.delete('1.0', 'end')
        self.download_log.configure(state='disabled')
        
        # Start download thread
        self.download_thread = threading.Thread(target=self.download_collection, daemon=True)
        self.download_thread.start()
    
    def download_collection(self):
        """Download collection (runs in background thread)."""
        try:
            downloader = DiscogsDownloader(
                self.token_var.get(),
                self.username_var.get(),
                self
            )
            
            # Download
            collection = downloader.download_all(
                include_custom_fields=self.include_custom_fields_var.get(),
                include_metadata=self.include_metadata_var.get(),
                output_dir=self.output_dir_var.get(),
                use_cache=self.use_cache_var.get()
            )
            
            # Generate report if requested
            if self.generate_report_var.get():
                report = downloader.generate_report(collection)
                report_path = os.path.join(self.output_dir_var.get(), 'discogs_report.txt')
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.log_message(self.download_log, f"\n✅ Report saved to: {report_path}")
            
            self.download_status.set("Download complete!")
            messagebox.showinfo("Success", f"Collection downloaded successfully!\n\nFiles saved to:\n{self.output_dir_var.get()}")
            
        except Exception as e:
            self.log_message(self.download_log, f"\n❌ Error: {e}")
            self.download_status.set("Download failed")
            messagebox.showerror("Error", f"Download failed: {e}")
        
        finally:
            self.download_progress.stop()
            self.download_btn.configure(state='normal')
    
    # Sync methods
    
    def preview_sync(self):
        """Preview sync changes."""
        if not self.validate_credentials():
            return
        
        field_name = self.sync_field_var.get().strip()
        if not field_name:
            messagebox.showwarning("Missing Field", "Please enter a custom field name.")
            return
        
        # Clear log
        self.sync_log.configure(state='normal')
        self.sync_log.delete('1.0', 'end')
        self.sync_log.configure(state='disabled')
        
        # Check if collection data exists
        json_path = os.path.join(self.output_dir_var.get(), 'discogs_collection_full.json')
        if not os.path.exists(json_path):
            messagebox.showwarning(
                "No Data",
                "Please download your collection first (Download tab)."
            )
            return
        
        try:
            # Load collection
            with open(json_path, 'r', encoding='utf-8') as f:
                collection = json.load(f)
            
            self.log_message(self.sync_log, f"Loaded {len(collection)} items from collection data")
            
            # Create syncer
            syncer = DiscogsCustomFieldSync(self.token_var.get(), self.username_var.get(), self)
            
            # Get extractor
            extractor = self.get_metadata_extractor()
            
            # Preview
            self.sync_plan = syncer.sync_from_metadata_extractor(
                collection,
                field_name,
                extractor,
                self.sync_skip_existing_var.get()
            )
            
            if not self.sync_plan:
                return
            
            # Show preview
            changes = self.sync_plan['changes']
            validation_errors = self.sync_plan['validation_errors']
            skipped = self.sync_plan['skipped']
            
            self.log_message(self.sync_log, f"\n📋 PREVIEW for field: {field_name}")
            self.log_message(self.sync_log, f"Field type: {self.sync_plan['field_type']}")
            
            if self.sync_plan['field_type'] == 'dropdown':
                self.log_message(self.sync_log, f"Dropdown options: {self.sync_plan['field_options']}")
            
            self.log_message(self.sync_log, f"\nWould update: {len(changes)} items")
            
            if changes:
                self.log_message(self.sync_log, "\nFirst 20 changes:")
                for change in changes[:20]:
                    self.log_message(self.sync_log, f"  {change['title']}")
                    self.log_message(self.sync_log, f"    '{change['current']}' → '{change['new']}'")
            
            if validation_errors:
                self.log_message(self.sync_log, f"\n❌ Validation failed: {len(validation_errors)} items")
                self.log_message(self.sync_log, "These values are not in dropdown options:")
                for err in validation_errors[:10]:
                    self.log_message(self.sync_log, f"  {err['title']}: '{err['value']}'")
            
            if skipped:
                self.log_message(self.sync_log, f"\nSkipped (already has value): {len(skipped)} items")
            
            # Enable execute button if there are changes
            if changes and not validation_errors:
                self.execute_btn.configure(state='normal')
                self.log_message(self.sync_log, "\n✅ Ready to sync. Click 'Execute Sync' to apply changes.")
            elif validation_errors and self.sync_ignore_errors_var.get():
                # Has errors but user wants to ignore them
                self.execute_btn.configure(state='normal')
                self.log_message(self.sync_log, f"\n⚠️ Will sync {len(changes)} valid items and skip {len(validation_errors)} failed items.")
                self.log_message(self.sync_log, "Click 'Execute Sync' to proceed (failed items will be skipped).")
            elif validation_errors:
                self.execute_btn.configure(state='disabled')
                self.log_message(self.sync_log, "\n⚠️ Fix validation errors or check 'Ignore validation errors' to skip them.")
            else:
                self.execute_btn.configure(state='disabled')
                self.log_message(self.sync_log, "\nℹ️ No changes needed.")
        
        except Exception as e:
            self.log_message(self.sync_log, f"\n❌ Error: {e}")
            messagebox.showerror("Error", f"Preview failed: {e}")
    
    def execute_sync(self):
        """Execute the sync."""
        if not self.sync_plan:
            messagebox.showwarning("No Preview", "Please preview the sync first.")
            return
        
        # Confirm
        changes_count = len(self.sync_plan['changes'])
        validation_errors_count = len(self.sync_plan['validation_errors'])
        
        if validation_errors_count > 0:
            message = f"This will update {changes_count} items in your Discogs collection.\n\n{validation_errors_count} items will be SKIPPED due to validation errors.\n\nAre you sure you want to proceed?"
        else:
            message = f"This will update {changes_count} items in your Discogs collection.\n\nAre you sure you want to proceed?"
        
        result = messagebox.askyesno("Confirm Sync", message)
        
        if not result:
            return
        
        # Disable button
        self.execute_btn.configure(state='disabled')
        self.preview_btn.configure(state='disabled')
        
        # Start sync thread
        self.sync_thread = threading.Thread(target=self.run_sync, daemon=True)
        self.sync_thread.start()
    
    def run_sync(self):
        """Run the sync (in background thread)."""
        try:
            syncer = DiscogsCustomFieldSync(self.token_var.get(), self.username_var.get(), self)
            updated = syncer.execute_sync(self.sync_plan)
            
            validation_errors_count = len(self.sync_plan['validation_errors'])
            
            if validation_errors_count > 0:
                self.log_message(self.sync_log, f"\n✅ Sync complete! Updated {updated} items.")
                self.log_message(self.sync_log, f"⚠️ Skipped {validation_errors_count} items due to validation errors.")
                self.log_message(self.sync_log, "\nYou'll need to update these manually in Discogs:")
                for err in self.sync_plan['validation_errors']:
                    self.log_message(self.sync_log, f"  - {err['title']} (wanted to set: '{err['value']}')")
                
                messagebox.showinfo(
                    "Sync Complete", 
                    f"Updated {updated} items.\n\nSkipped {validation_errors_count} items with validation errors.\n\nSee log for details on which items need manual updates."
                )
            else:
                self.log_message(self.sync_log, f"\n✅ Sync complete! Updated {updated} items.")
                messagebox.showinfo("Success", f"Sync complete!\n\nUpdated {updated} items.")
            
        except Exception as e:
            self.log_message(self.sync_log, f"\n❌ Error: {e}")
            messagebox.showerror("Error", f"Sync failed: {e}")
        
        finally:
            self.preview_btn.configure(state='normal')
    
    def get_metadata_extractor(self):
        """Get the appropriate metadata extractor."""
        source = self.sync_source_var.get()
        
        extractors = {
            # Basic info
            'year': lambda item: str(item['basic_information'].get('year')) if item['basic_information'].get('year') else None,
            'decade': lambda item: f"{(item['basic_information'].get('year', 0) // 10) * 10}s" if item['basic_information'].get('year') else None,
            
            # Genres & Styles
            'first_genre': lambda item: item.get('detailed_metadata', {}).get('genres', [])[0] if item.get('detailed_metadata', {}).get('genres') else None,
            'all_genres': lambda item: ', '.join(item.get('detailed_metadata', {}).get('genres', [])) if item.get('detailed_metadata', {}).get('genres') else None,
            'first_style': lambda item: item.get('detailed_metadata', {}).get('styles', [])[0] if item.get('detailed_metadata', {}).get('styles') else None,
            'all_styles': lambda item: ', '.join(item.get('detailed_metadata', {}).get('styles', [])) if item.get('detailed_metadata', {}).get('styles') else None,
            
            # Format
            'format_simple': self.extract_format_simple,
            'format_full': lambda item: ', '.join([f['name'] for f in item['basic_information'].get('formats', []) if f.get('name')]) or None,
            
            # Label & Catalog
            'label': lambda item: ', '.join([l['name'] for l in item['basic_information'].get('labels', []) if l.get('name')]) or None,
            'catalog_number': lambda item: ', '.join([l['catno'] for l in item['basic_information'].get('labels', []) if l.get('catno')]) or None,
            
            # Country
            'country': lambda item: item.get('detailed_metadata', {}).get('country'),
            
            # Community & Pricing
            'price_low': lambda item: str(item.get('detailed_metadata', {}).get('lowest_price')) if item.get('detailed_metadata', {}).get('lowest_price') else None,
            'num_for_sale': lambda item: str(item.get('detailed_metadata', {}).get('num_for_sale')) if item.get('detailed_metadata', {}).get('num_for_sale') else None,
            'community_have': lambda item: str(item.get('detailed_metadata', {}).get('community', {}).get('have')) if item.get('detailed_metadata', {}).get('community', {}).get('have') else None,
            'community_want': lambda item: str(item.get('detailed_metadata', {}).get('community', {}).get('want')) if item.get('detailed_metadata', {}).get('community', {}).get('want') else None,
        }
        
        return extractors.get(source)
    
    def extract_format_simple(self, item):
        """Simplify format."""
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


# Downloader class (simplified version that works with GUI)
class DiscogsDownloader:
    """Download Discogs collection."""
    
    BASE_URL = "https://api.discogs.com"
    
    def __init__(self, token, username, gui):
        self.token = token
        self.username = username
        self.gui = gui
        self.headers = {
            'User-Agent': 'DiscogsGUI/1.0',
            'Authorization': f'Discogs token={token}'
        }
        self.cache_file = 'discogs_cache.json'
    
    def load_cache(self):
        """Load cached collection data."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                self.gui.log_message(self.gui.download_log, f"📦 Loaded cache: {len(cache.get('items', {}))} items")
                return cache
            except:
                return {'items': {}, 'last_updated': None}
        return {'items': {}, 'last_updated': None}
    
    def save_cache(self, collection):
        """Save collection to cache."""
        cache = {
            'items': {str(item['instance_id']): item for item in collection},
            'last_updated': datetime.now().isoformat()
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        self.gui.log_message(self.gui.download_log, f"💾 Saved cache: {len(collection)} items")
    
    def _make_request(self, endpoint, params=None):
        """Make API request."""
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        
        remaining = int(response.headers.get('X-Discogs-Ratelimit-Remaining', 60))
        if remaining < 10:
            self.gui.log_message(self.gui.download_log, "⚠️ Rate limit low. Pausing...")
            time.sleep(60)
        
        response.raise_for_status()
        return response.json()
    
    def get_custom_fields(self):
        """Get custom field definitions."""
        endpoint = f"/users/{self.username}/collection/fields"
        data = self._make_request(endpoint)
        return data.get('fields', [])
    
    def download_all(self, include_custom_fields=True, include_metadata=False, output_dir='.', use_cache=True):
        """Download everything with optional incremental update."""
        
        # Load cache if enabled
        cache = None
        if use_cache:
            cache = self.load_cache()
            cached_items = cache.get('items', {})
        else:
            cached_items = {}
        
        # Get folders first
        self.gui.log_message(self.gui.download_log, "📁 Getting folders...")
        folders_data = self._make_request(f"/users/{self.username}/collection/folders")
        folders = {f['id']: f['name'] for f in folders_data.get('folders', [])}
        self.gui.log_message(self.gui.download_log, f"✅ Found {len(folders)} folders: {list(folders.values())}")
        
        # Get collection
        self.gui.log_message(self.gui.download_log, "\n📚 Downloading collection...")
        collection = []
        page = 1
        
        while True:
            self.gui.log_message(self.gui.download_log, f"  Page {page}...")
            endpoint = f"/users/{self.username}/collection/folders/0/releases"
            data = self._make_request(endpoint, {'page': page, 'per_page': 100})
            releases = data.get('releases', [])
            
            if not releases:
                break
            
            collection.extend(releases)
            
            if page >= data.get('pagination', {}).get('pages', 1):
                break
            
            page += 1
            time.sleep(1)
        
        self.gui.log_message(self.gui.download_log, f"✅ Downloaded {len(collection)} items")
        
        # Determine what's new/changed
        new_items = []
        changed_items = []
        unchanged_items = []
        
        for item in collection:
            instance_id = str(item['instance_id'])
            
            if instance_id not in cached_items:
                new_items.append(item)
            elif item.get('date_added') != cached_items[instance_id].get('date_added'):
                # Item has been modified
                changed_items.append(item)
            else:
                # Use cached data
                unchanged_items.append(cached_items[instance_id])
        
        if use_cache:
            self.gui.log_message(self.gui.download_log, f"\n📊 Cache analysis:")
            self.gui.log_message(self.gui.download_log, f"  New items: {len(new_items)}")
            self.gui.log_message(self.gui.download_log, f"  Changed items: {len(changed_items)}")
            self.gui.log_message(self.gui.download_log, f"  Unchanged items: {len(unchanged_items)}")
        
        # Only fetch custom fields and metadata for new/changed items
        items_to_fetch = new_items + changed_items
        
        # Get custom fields
        if include_custom_fields and items_to_fetch:
            self.gui.log_message(self.gui.download_log, f"\n🔍 Getting custom field values for {len(items_to_fetch)} new/changed items...")
            custom_fields = self.get_custom_fields()
            
            if custom_fields:
                for idx, item in enumerate(items_to_fetch, 1):
                    if idx % 50 == 0:
                        self.gui.log_message(self.gui.download_log, f"  Progress: {idx}/{len(items_to_fetch)}")
                    
                    try:
                        endpoint = f"/users/{self.username}/collection/folders/{item['folder_id']}/releases/{item['id']}/instances/{item['instance_id']}"
                        instance_data = self._make_request(endpoint)
                        item['custom_field_values'] = instance_data.get('notes', [])
                        time.sleep(0.7)
                    except:
                        item['custom_field_values'] = []
                
                self.gui.log_message(self.gui.download_log, f"✅ Got custom field values")
        
        # Get metadata
        if include_metadata and items_to_fetch:
            self.gui.log_message(self.gui.download_log, f"\n🔄 Enriching {len(items_to_fetch)} new/changed items with full metadata...")
            
            for idx, item in enumerate(items_to_fetch, 1):
                self.gui.log_message(self.gui.download_log, f"  [{idx}/{len(items_to_fetch)}] {item['basic_information']['title']}")
                
                release_id = item['basic_information']['id']
                master_id = item['basic_information'].get('master_id')
                
                try:
                    endpoint = f"/releases/{release_id}"
                    detailed = self._make_request(endpoint)
                    item['detailed_metadata'] = detailed
                    
                    if idx % 10 == 0:
                        time.sleep(3)
                    else:
                        time.sleep(1.2)
                        
                except requests.exceptions.HTTPError as e:
                    # If 404, try master release instead
                    if e.response.status_code == 404 and master_id:
                        self.gui.log_message(self.gui.download_log, f"    ⚠️  Release 404, trying master {master_id}...")
                        try:
                            master_endpoint = f"/masters/{master_id}"
                            detailed = self._make_request(master_endpoint)
                            item['detailed_metadata'] = detailed
                        except Exception as master_error:
                            self.gui.log_message(self.gui.download_log, f"    ⚠️  Master also failed: {master_error}")
                            item['detailed_metadata'] = {}
                    else:
                        self.gui.log_message(self.gui.download_log, f"    ⚠️  Error: {e}")
                        item['detailed_metadata'] = {}
                        
                except Exception as e:
                    self.gui.log_message(self.gui.download_log, f"    ⚠️  Error: {e}")
                    item['detailed_metadata'] = {}
            
            self.gui.log_message(self.gui.download_log, f"✅ Enriched with metadata")
        
        # Combine: fetched items + unchanged cached items
        final_collection = items_to_fetch + unchanged_items
        
        # Save to cache
        if use_cache:
            self.save_cache(final_collection)
        
        # Export
        self.gui.log_message(self.gui.download_log, "\n📤 Exporting...")
        
        # Create timestamped filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON - save both timestamped and latest
        json_path = os.path.join(output_dir, f'discogs_collection_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(final_collection, f, indent=2, ensure_ascii=False)
        self.gui.log_message(self.gui.download_log, f"✅ Saved JSON: {json_path}")
        
        # Also save as "latest" for sync script to use
        json_latest = os.path.join(output_dir, 'discogs_collection_full.json')
        with open(json_latest, 'w', encoding='utf-8') as f:
            json.dump(final_collection, f, indent=2, ensure_ascii=False)
        
        # CSV (with folder names and timestamp)
        csv_path = os.path.join(output_dir, f'discogs_collection_{timestamp}.csv')
        self.export_csv(final_collection, csv_path, folders)
        self.gui.log_message(self.gui.download_log, f"✅ Saved CSV: {csv_path}")
        
        return final_collection
    
    def export_csv(self, collection, filename, folders=None):
        """Export to CSV with folder names and custom field names."""
        # Get custom field definitions for proper names
        try:
            custom_fields = self.get_custom_fields()
            custom_field_names = {f['id']: f['name'] for f in custom_fields}
        except:
            custom_field_names = {}
        
        rows = []
        download_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for item in collection:
            basic = item['basic_information']
            detailed = item.get('detailed_metadata', {})
            
            # Get folder name
            folder_id = item.get('folder_id', 0)
            folder_name = folders.get(folder_id, 'Unknown') if folders else str(folder_id)
            
            row = {
                'download_date': download_timestamp,
                'release_id': basic['id'],
                'instance_id': item['instance_id'],
                'folder_id': folder_id,
                'folder_name': folder_name,
                'artist': ', '.join([a['name'] for a in basic.get('artists', [])]),
                'title': basic['title'],
                'year': basic.get('year'),
                'format': ', '.join([f['name'] for f in basic.get('formats', []) if f.get('name')]),
                'label': ', '.join([l['name'] for l in basic.get('labels', []) if l.get('name')]),
                'catalog_number': ', '.join([l['catno'] for l in basic.get('labels', []) if l.get('catno')]),
                'date_added': item.get('date_added'),
                'rating': item.get('rating'),
                'genres': ', '.join(detailed.get('genres', [])),
                'styles': ', '.join(detailed.get('styles', [])),
                'country': detailed.get('country'),
                # Price data from marketplace stats
                'price_low': detailed.get('lowest_price'),
                'price_median': detailed.get('community', {}).get('rating', {}).get('average'),
                'price_high': None,  # Discogs API doesn't provide highest price directly
                'num_for_sale': detailed.get('num_for_sale'),
            }
            
            # Add custom field values with proper names
            for note in item.get('custom_field_values', []):
                field_id = note.get('field_id')
                field_name = custom_field_names.get(field_id, f'custom_field_{field_id}')
                row[field_name] = note.get('value')
            
            rows.append(row)
        
        if rows:
            fieldnames = set()
            for row in rows:
                fieldnames.update(row.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
    
    def generate_report(self, collection):
        """Generate summary report."""
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
        
        # Count by style
        styles = {}
        for item in collection:
            detailed = item.get('detailed_metadata', {})
            for style in detailed.get('styles', []):
                styles[style] = styles.get(style, 0) + 1
        
        # Count by folder
        folders = {}
        for item in collection:
            folder_id = item.get('folder_id', 0)
            # This assumes we have folder names in the collection items
            # If not available, we'll just skip this section
        
        # Build report
        report = f"""DISCOGS COLLECTION SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Items: {total}

TOP 10 FORMATS:
"""
        for fmt, count in sorted(formats.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"{fmt[:50]:50s} {count:5d}\n"
        
        report += "\nTOP 10 YEARS:\n"
        for year, count in sorted(years.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"{str(year):50s} {count:5d}\n"
        
        report += "\nTOP 10 LABELS:\n"
        for label, count in sorted(labels.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"{label[:50]:50s} {count:5d}\n"
        
        if genres:
            report += "\nTOP 10 GENRES:\n"
            for genre, count in sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]:
                report += f"{genre[:50]:50s} {count:5d}\n"
        
        if styles:
            report += "\nTOP 10 STYLES:\n"
            for style, count in sorted(styles.items(), key=lambda x: x[1], reverse=True)[:10]:
                report += f"{style[:50]:50s} {count:5d}\n"
        
        return report


# Sync class (simplified for GUI)
class DiscogsCustomFieldSync:
    """Sync custom fields."""
    
    BASE_URL = "https://api.discogs.com"
    
    def __init__(self, token, username, gui):
        self.token = token
        self.username = username
        self.gui = gui
        self.headers = {
            'User-Agent': 'DiscogsGUI/1.0',
            'Authorization': f'Discogs token={token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, data=None):
        """Make API request with smart rate limiting."""
        url = f"{self.BASE_URL}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, headers=self.headers)
        elif method == 'POST':
            response = requests.post(url, headers=self.headers, json=data)
        
        # Smart rate limiting based on API response
        remaining = int(response.headers.get('X-Discogs-Ratelimit-Remaining', 60))
        
        # If we're getting low on requests, pause
        if remaining < 5:
            self.gui.log_message(self.gui.sync_log, f"  ⏸️  Rate limit low ({remaining}), pausing 60s...")
            time.sleep(60)
        
        response.raise_for_status()
        return response.json() if response.status_code != 204 else {}
    
    def get_custom_fields(self):
        """Get custom field definitions."""
        endpoint = f"/users/{self.username}/collection/fields"
        data = self._make_request('GET', endpoint)
        return data.get('fields', [])
    
    def sync_from_metadata_extractor(self, collection, field_name, extractor, skip_if_has_value):
        """Analyze sync."""
        fields = self.get_custom_fields()
        
        field_id = None
        field_type = None
        field_options = []
        
        for field in fields:
            if field['name'] == field_name:
                field_id = field['id']
                field_type = field.get('type', 'text')
                field_options = field.get('options', [])
                break
        
        if field_id is None:
            self.gui.log_message(self.gui.sync_log, f"❌ Custom field '{field_name}' not found!")
            available = [f['name'] for f in fields]
            self.gui.log_message(self.gui.sync_log, f"Available: {available}")
            return None
        
        changes = []
        validation_errors = []
        skipped = []
        
        for item in collection:
            new_value = extractor(item)
            if new_value is None:
                continue
            
            new_value = str(new_value)
            
            # Validate dropdown
            if field_type == 'dropdown' and new_value not in field_options:
                validation_errors.append({'title': item['basic_information']['title'], 'value': new_value})
                continue
            
            # Get current
            current_value = None
            for note in item.get('custom_field_values', []):
                if note.get('field_id') == field_id:
                    current_value = note.get('value')
                    break
            
            if skip_if_has_value and current_value:
                skipped.append({'title': item['basic_information']['title'], 'current': current_value})
                continue
            
            if str(new_value) != str(current_value):
                changes.append({
                    'title': item['basic_information']['title'],
                    'current': current_value,
                    'new': new_value,
                    'folder_id': item['folder_id'],
                    'release_id': item['id'],
                    'instance_id': item['instance_id']
                })
        
        return {
            'field_id': field_id,
            'field_type': field_type,
            'field_options': field_options,
            'changes': changes,
            'validation_errors': validation_errors,
            'skipped': skipped
        }
    
    def execute_sync(self, sync_plan):
        """Execute sync with optimized rate limiting."""
        changes = sync_plan['changes']
        field_id = sync_plan['field_id']
        
        updated = 0
        start_time = time.time()
        
        for idx, change in enumerate(changes, 1):
            self.gui.log_message(self.gui.sync_log, f"[{idx}/{len(changes)}] {change['title']} → '{change['new']}'")
            
            try:
                endpoint = f"/users/{self.username}/collection/folders/{change['folder_id']}/releases/{change['release_id']}/instances/{change['instance_id']}/fields/{field_id}"
                self._make_request('POST', endpoint, {'value': change['new']})
                updated += 1
                
                # Smarter rate limiting: aim for ~40 requests per minute to stay safe
                # That's 1.5 seconds per request, but we can batch faster with strategic pauses
                if idx % 10 == 0:
                    # Every 10 requests, check if we're going too fast
                    elapsed = time.time() - start_time
                    expected_time = idx * 1.5  # Should take 1.5s per request
                    if elapsed < expected_time:
                        sleep_time = expected_time - elapsed
                        self.gui.log_message(self.gui.sync_log, f"  ⏸️  Rate limit pause: {sleep_time:.1f}s")
                        time.sleep(sleep_time)
                else:
                    # Between batches, use shorter delay
                    time.sleep(0.8)
                    
            except Exception as e:
                self.gui.log_message(self.gui.sync_log, f"  ❌ Error: {e}")
        
        return updated


# Main
def main():
    root = tk.Tk()
    app = DiscogsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
