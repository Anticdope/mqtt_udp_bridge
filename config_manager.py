"""
Configuration Manager for MQTT UDP Bridge
Handles loading/saving of mappings and broker settings
"""

import json
import os
import sys
from tkinter import messagebox

class ConfigManager:
    def __init__(self):
        # Ensure JSON file is always in the same directory as the executable
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.mappings_file = os.path.join(app_dir, "map.json")
        
    def load_mappings(self):
        """Load UDP mappings and broker settings from JSON file"""
        try:
            if os.path.exists(self.mappings_file):
                with open(self.mappings_file, 'r') as f:
                    data = json.load(f)
                
                # Handle both old format (just mappings list) and new format
                if isinstance(data, list):
                    # Old format - just mappings - add missing fields
                    udp_mappings = []
                    for i, mapping in enumerate(data):
                        self._ensure_mapping_fields(mapping, i)
                        udp_mappings.append(mapping)
                    broker_settings = self._default_broker_settings()
                    print(f"Loaded {len(udp_mappings)} mappings from {self.mappings_file} (old format)")
                elif isinstance(data, dict):
                    # New format - mappings and broker settings
                    mappings_data = data.get('mappings', [])
                    udp_mappings = []
                    for i, mapping in enumerate(mappings_data):
                        self._ensure_mapping_fields(mapping, i)
                        udp_mappings.append(mapping)
                    
                    broker_data = data.get('broker', self._default_broker_settings())
                    if 'auto_connect' not in broker_data:
                        broker_data['auto_connect'] = True
                    broker_settings = broker_data
                    print(f"Loaded {len(udp_mappings)} mappings and broker settings from {self.mappings_file}")
                else:
                    udp_mappings = []
                    broker_settings = self._default_broker_settings()
                    print("Invalid file format. Starting with defaults.")
            else:
                udp_mappings = []
                broker_settings = self._default_broker_settings()
                print(f"No existing mappings file found. Starting with empty mappings.")
                
            return udp_mappings, broker_settings
            
        except Exception as e:
            print(f"Error loading mappings: {str(e)}")
            return [], self._default_broker_settings()
    
    def save_mappings(self, udp_mappings, broker_settings):
        """Save UDP mappings and broker settings to JSON file"""
        try:
            data = {
                'broker': broker_settings,
                'mappings': udp_mappings
            }
            with open(self.mappings_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {len(udp_mappings)} mappings and broker settings to {self.mappings_file}")
            return True
        except Exception as e:
            print(f"Error saving mappings: {str(e)}")
            return False
    
    def export_config(self, destination_file):
        """Export current configuration to a file"""
        try:
            import shutil
            shutil.copy2(self.mappings_file, destination_file)
            return True
        except Exception as e:
            print(f"Export failed: {str(e)}")
            return False
    
    def _ensure_mapping_fields(self, mapping, index):
        """Ensure all required fields exist in mapping"""
        defaults = {
            'trigger_value': '',
            'udp_delay': 0.0,
            'car_length': 4.5,
            'speed_units': 'mph',
            'trigger_name': f"Sensor{index+1}",
            'timeout': 1.0
        }
        
        for field, default_value in defaults.items():
            if field not in mapping:
                mapping[field] = default_value
    
    def _default_broker_settings(self):
        """Return default broker settings"""
        return {
            'address': 'localhost',
            'port': 1883,
            'auto_connect': True
        }
    
    def get_mappings_filename(self):
        """Get the basename of the mappings file"""
        return os.path.basename(self.mappings_file)