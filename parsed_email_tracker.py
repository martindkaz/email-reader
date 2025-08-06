import json
import os
from datetime import datetime


class ParsedEmailTracker:
    def __init__(self, filename="processed_emails.json"):
        self.filename = filename
        self.processed_ids = set()
        self.load_processed_ids()
    
    def load_processed_ids(self):
        """Load processed email IDs from JSON file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('processed_ids', []))
            except (json.JSONDecodeError, KeyError):
                print(f"Warning: Could not load {self.filename}, starting fresh")
                self.processed_ids = set()
    
    def save_processed_ids(self):
        """Save processed email IDs to JSON file"""
        data = {
            'processed_ids': list(self.processed_ids),
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def is_processed(self, internet_message_id):
        """Check if an email has been processed"""
        return internet_message_id in self.processed_ids
    
    def mark_processed(self, internet_message_id):
        """Mark an email as processed"""
        self.processed_ids.add(internet_message_id)
        self.save_processed_ids()
    
    def get_processed_count(self):
        """Get count of processed emails"""
        return len(self.processed_ids)
    
    def clear_all(self):
        """Clear all processed email IDs (for testing/reset)"""
        self.processed_ids.clear()
        self.save_processed_ids()