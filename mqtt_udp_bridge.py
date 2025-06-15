"""
MQTT to UDP Bridge v2.0 - Main Application Class
Coordinates all components and handles application logic
"""

import tkinter as tk
from tkinter import ttk
from config_manager import ConfigManager
from mqtt_handler import MQTTHandler
from speed_calculator import SpeedCalculator
from udp_sender import UDPSender
from ui_components import UIComponents

class MQTTUDPBridge:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT to UDP Bridge v2.0")
        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.udp_mappings = []
        self.broker_settings = {}
        
        # Load configuration
        self.load_initial_config()
        
        # Initialize UI
        self.ui = UIComponents(root, self)
        self.ui.create_main_layout()
        
        # Initialize core components
        self.speed_calculator = SpeedCalculator(self.log_message, self.topic_matches)
        self.udp_sender = UDPSender(
            self.log_message,
            self.get_mappings,
            self.is_udp_enabled,
            self.topic_matches,
            self.should_trigger
        )
        self.mqtt_handler = MQTTHandler(self.log_message, self.speed_calculator, self.udp_sender)
        
        # Set up UI with loaded data
        self.setup_ui_with_data()
        self.update_mappings_display()
        
        # Auto-connect if enabled
        if self.broker_settings.get('auto_connect', True):
            self.root.after(3000, self.auto_connect)
    
    def load_initial_config(self):
        """Load initial configuration from file"""
        self.udp_mappings, self.broker_settings = self.config_manager.load_mappings()
        
    def setup_ui_with_data(self):
        """Setup UI components with loaded data"""
        # Set broker settings in UI
        self.broker_entry.insert(0, self.broker_settings['address'])
        self.port_entry.insert(0, str(self.broker_settings['port']))
        self.auto_connect_var.set(self.broker_settings.get('auto_connect', True))
        
        # Update mappings file info
        if hasattr(self, 'mappings_info_label'):
            self.mappings_info_label.config(text=f"📄 {self.config_manager.get_mappings_filename()}")
    
    # Configuration Management
    def save_mappings(self):
        """Save current mappings to file"""
        success = self.config_manager.save_mappings(self.udp_mappings, self.broker_settings)
        if not success and hasattr(self, 'message_display'):
            self.log_message("❌ Error saving mappings")
            
    def save_broker_settings(self):
        """Save current broker settings from UI"""
        try:
            self.broker_settings['address'] = self.broker_entry.get().strip()
            self.broker_settings['port'] = int(self.port_entry.get().strip())
        except ValueError:
            pass  # Keep old values if invalid
            
    def save_auto_connect_setting(self):
        """Save auto-connect setting"""
        self.broker_settings['auto_connect'] = self.auto_connect_var.get()
        self.save_mappings()
        
    def reload_mappings(self):
        """Reload mappings from file"""
        old_count = len(self.udp_mappings)
        old_broker = f"{self.broker_settings['address']}:{self.broker_settings['port']}"
        
        self.udp_mappings, self.broker_settings = self.config_manager.load_mappings()
        new_count = len(self.udp_mappings)
        new_broker = f"{self.broker_settings['address']}:{self.broker_settings['port']}"
        
        # Update UI with loaded settings
        self.broker_entry.delete(0, tk.END)
        self.broker_entry.insert(0, self.broker_settings['address'])
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, str(self.broker_settings['port']))
        self.auto_connect_var.set(self.broker_settings.get('auto_connect', True))
        
        self.update_mappings_display()
        self.update_mqtt_subscriptions()
        
        self.log_message(f"🔄 Reloaded: {old_count} → {new_count} mappings, broker: {old_broker} → {new_broker}")
        
    def export_config(self):
        """Export configuration to file"""
        filename = self.ui.show_export_dialog()
        if filename:
            success = self.config_manager.export_config(filename)
            if success:
                self.log_message(f"📄 Configuration exported to {filename}")
                self.ui.show_info("Export Complete", f"Configuration exported to:\n{filename}")
            else:
                self.log_message(f"❌ Export failed")
                self.ui.show_error("Export Failed", "Failed to export configuration")
    
    # MQTT Connection Management
    def toggle_connection(self):
        """Toggle MQTT connection"""
        if not self.mqtt_handler.connected:
            self.connect_mqtt()
        else:
            self.disconnect_mqtt()
            
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        broker = self.broker_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            self.log_message("Error: Port must be a number")
            return
            
        self.save_broker_settings()
        
        self.status_var.set(f"Connecting to {broker}:{port}...")
        self.root.update()
        
        success = self.mqtt_handler.connect(broker, port)
        if success:
            self.connect_button.config(text="🔌 Disconnect")
            self.status_var.set(f"✅ Connected to {broker}:{port}")
            self.conn_status_label.config(foreground="green")
            self.update_mqtt_subscriptions()
        else:
            self.status_var.set("❌ Connection failed")
            self.conn_status_label.config(foreground="red")
            
    def disconnect_mqtt(self):
        """Disconnect from MQTT broker"""
        self.mqtt_handler.disconnect()
        self.connect_button.config(text="🔌 Connect")
        self.status_var.set("⭕ Disconnected")
        self.conn_status_label.config(foreground="red")
        self.log_message("Disconnected from broker")
        
    def auto_connect(self):
        """Automatically connect on startup"""
        if self.broker_settings.get('auto_connect', True) and not self.mqtt_handler.connected:
            self.log_message("🔄 Auto-connecting to broker...")
            self.root.after(500, self.connect_mqtt)
    
    def update_mqtt_subscriptions(self):
        """Update MQTT subscriptions and UI"""
        self.mqtt_handler.update_subscriptions(self.udp_mappings)
        
        # Update topics listbox
        self.topics_listbox.delete(0, tk.END)
        for mapping in self.udp_mappings:
            self.topics_listbox.insert(tk.END, mapping['topic'])
    
    # Mapping Management
    def add_mapping(self):
        """Add new UDP mapping"""
        # Get values from UI
        trigger_name = self.new_trigger_name_entry.get().strip()
        topic = self.new_topic_entry.get().strip()
        udp_ip = self.new_udp_ip_entry.get().strip()
        udp_message = self.new_udp_message_entry.get().strip()
        trigger_value = self.new_trigger_entry.get().strip()
        timeout_str = self.new_timeout_entry.get().strip()
        delay_str = self.new_delay_entry.get().strip()
        car_length_str = self.new_car_length_entry.get().strip()
        speed_units = self.speed_units_var.get()
        
        # Validate inputs
        validation_result = self._validate_mapping_inputs(
            trigger_name, topic, udp_ip, udp_message, 
            self.new_udp_port_entry.get().strip(), timeout_str, delay_str, car_length_str
        )
        
        if not validation_result['valid']:
            self.ui.show_error("Error", validation_result['message'])
            return
            
        # Check for duplicates
        for mapping in self.udp_mappings:
            if mapping.get('trigger_name', '') == trigger_name:
                self.ui.show_error("Error", f"Trigger name '{trigger_name}' already exists")
                return
            if mapping['topic'] == topic:
                self.ui.show_error("Error", f"Topic '{topic}' already has a mapping")
                return
        
        # Create mapping
        mapping = {
            'trigger_name': trigger_name,
            'topic': topic,
            'udp_ip': udp_ip,
            'udp_port': validation_result['udp_port'],
            'udp_message': udp_message,
            'trigger_value': trigger_value,
            'timeout': validation_result['timeout'],
            'udp_delay': validation_result['udp_delay'],
            'car_length': validation_result['car_length'],
            'speed_units': speed_units
        }
        
        self.udp_mappings.append(mapping)
        self.save_broker_settings()
        self.save_mappings()
        self.update_mappings_display()
        self.update_mqtt_subscriptions()
        
        self.log_message(f"➕ Added trigger: {trigger_name} ({topic} → {udp_ip}:{validation_result['udp_port']})")
        self._clear_add_form()
        
    def remove_mapping(self):
        """Remove selected mapping"""
        selection = self.mappings_tree.selection()
        if not selection:
            self.ui.show_warning("Warning", "Please select a mapping to remove")
            return
            
        item = self.mappings_tree.item(selection[0])
        trigger_name = item['values'][0]
        
        # Find and remove mapping
        mapping_to_remove = None
        for mapping in self.udp_mappings:
            if mapping.get('trigger_name', '') == trigger_name:
                mapping_to_remove = mapping
                break
                
        if mapping_to_remove:
            self.udp_mappings.remove(mapping_to_remove)
            self.save_mappings()
            self.update_mappings_display()
            self.update_mqtt_subscriptions()
            self.log_message(f"🗑️ Removed trigger: {trigger_name}")
        else:
            self.ui.show_error("Error", "Could not find mapping to remove")
            
    def edit_mapping(self, event=None):
        """Edit selected mapping"""
        selection = self.mappings_tree.selection()
        if not selection:
            self.ui.show_warning("Warning", "Please select a mapping to edit")
            return
            
        item = self.mappings_tree.item(selection[0])
        trigger_name = item['values'][0]
        
        # Find mapping
        mapping_to_edit = None
        for mapping in self.udp_mappings:
            if mapping.get('trigger_name', '') == trigger_name:
                mapping_to_edit = mapping
                break
                
        if not mapping_to_edit:
            self.ui.show_error("Error", "Could not find mapping to edit")
            return
            
        self._show_edit_dialog(mapping_to_edit)
        
    def _show_edit_dialog(self, mapping):
        """Show edit dialog for mapping"""
        entries, button_frame, dialog_window = self.ui.show_edit_dialog(mapping)
        
        def save_changes():
            # Get values from entries
            new_trigger_name = entries['trigger_name'].get().strip()
            new_topic = entries['topic'].get().strip()
            new_ip = entries['ip'].get().strip()
            new_message = entries['message'].get('1.0', 'end-1c').strip()
            new_trigger = entries['trigger'].get().strip()
            new_timeout_str = entries['timeout'].get().strip()
            new_delay_str = entries['delay'].get().strip()
            new_car_length_str = entries['car_length'].get().strip()
            new_speed_units = entries['speed_units_var'].get()
            new_port_str = entries['port'].get().strip()
            
            # Validate inputs
            validation_result = self._validate_mapping_inputs(
                new_trigger_name, new_topic, new_ip, new_message,
                new_port_str, new_timeout_str, new_delay_str, new_car_length_str
            )
            
            if not validation_result['valid']:
                self.ui.show_error("Error", validation_result['message'])
                return
                
            # Check for conflicts (except current mapping)
            for existing_mapping in self.udp_mappings:
                if existing_mapping != mapping:
                    if existing_mapping.get('trigger_name', '') == new_trigger_name:
                        self.ui.show_error("Error", f"Trigger name '{new_trigger_name}' already exists")
                        return
                    if existing_mapping['topic'] == new_topic:
                        self.ui.show_error("Error", f"Topic '{new_topic}' already has a mapping")
                        return
            
            # Update mapping
            mapping.update({
                'trigger_name': new_trigger_name,
                'topic': new_topic,
                'udp_ip': new_ip,
                'udp_port': validation_result['udp_port'],
                'udp_message': new_message,
                'trigger_value': new_trigger,
                'timeout': validation_result['timeout'],
                'udp_delay': validation_result['udp_delay'],
                'car_length': validation_result['car_length'],
                'speed_units': new_speed_units
            })
            
            self.save_mappings()
            self.update_mappings_display()
            self.update_mqtt_subscriptions()
            
            dialog_window.destroy()
            self.log_message(f"✏️ Updated trigger: {new_trigger_name} ({new_topic} → {new_ip}:{validation_result['udp_port']})")
            
        def cancel_edit():
            dialog_window.destroy()
            
        # Add buttons
        ttk.Button(button_frame, text="💾 Save Changes", command=save_changes, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="❌ Cancel", command=cancel_edit).pack(side="left", padx=10)
        
        # Focus on first field
        entries['trigger_name'].focus_set()
    
    def update_mappings_display(self):
        """Update the mappings table display"""
        # Clear existing items
        for item in self.mappings_tree.get_children():
            self.mappings_tree.delete(item)
            
        # Add current mappings
        for mapping in self.udp_mappings:
            trigger_display = mapping.get('trigger_value', '')
            if trigger_display == '':
                trigger_display = 'any'
            delay_display = mapping.get('udp_delay', 0.0)
            timeout_display = mapping.get('timeout', 1.0)
            trigger_name = mapping.get('trigger_name', 'Unnamed')
            
            udp_target = f"{mapping['udp_ip']}:{mapping['udp_port']}"
            
            # Truncate message for display
            message_display = mapping['udp_message']
            if len(message_display) > 25:
                message_display = message_display[:22] + "..."
                
            self.mappings_tree.insert("", "end", values=(
                trigger_name,
                mapping['topic'],
                udp_target,
                message_display,
                trigger_display,
                f"{delay_display:.1f}",
                f"{timeout_display:.1f}"
            ))
    
    # Utility Methods
    def _validate_mapping_inputs(self, trigger_name, topic, udp_ip, udp_message, udp_port_str, timeout_str, delay_str, car_length_str):
        """Validate mapping input values"""
        result = {'valid': False, 'message': ''}
        
        # Required fields
        if not trigger_name or not topic or not udp_ip or not udp_message:
            result['message'] = "Trigger Name, Topic, UDP IP, and UDP Message are required"
            return result
            
        # UDP Port
        try:
            udp_port = int(udp_port_str)
            result['udp_port'] = udp_port
        except ValueError:
            result['message'] = "UDP Port must be a number"
            return result
            
        # Timeout
        try:
            timeout = float(timeout_str) if timeout_str else 1.0
            timeout = round(max(0.0, timeout), 1)
            result['timeout'] = timeout
        except ValueError:
            result['message'] = "Timeout must be a number (seconds)"
            return result
            
        # UDP Delay
        try:
            udp_delay = float(delay_str) if delay_str else 0.0
            udp_delay = round(max(0.0, udp_delay), 1)
            result['udp_delay'] = udp_delay
        except ValueError:
            result['message'] = "UDP Delay must be a number (seconds)"
            return result
            
        # Car Length
        try:
            car_length = float(car_length_str) if car_length_str else 0.0
            car_length = max(0.0, car_length)
            result['car_length'] = car_length
        except ValueError:
            result['message'] = "Car Length must be a number (meters)"
            return result
            
        result['valid'] = True
        return result
        
    def _clear_add_form(self):
        """Clear the add mapping form"""
        self.new_trigger_name_entry.delete(0, tk.END)
        self.new_trigger_name_entry.insert(0, "Sensor")
        self.new_topic_entry.delete(0, tk.END)
        self.new_udp_ip_entry.delete(0, tk.END)
        self.new_udp_ip_entry.insert(0, "127.0.0.1")
        self.new_udp_port_entry.delete(0, tk.END)
        self.new_udp_port_entry.insert(0, "8080")
        self.new_udp_message_entry.delete(0, tk.END)
        self.new_udp_message_entry.insert(0, "{payload}")
        self.new_trigger_entry.delete(0, tk.END)
        self.new_trigger_entry.insert(0, "1")
        self.new_timeout_entry.delete(0, tk.END)
        self.new_timeout_entry.insert(0, "1.0")
        self.new_delay_entry.delete(0, tk.END)
        self.new_delay_entry.insert(0, "0.0")
        self.new_car_length_entry.delete(0, tk.END)
        self.new_car_length_entry.insert(0, "4.5")
        self.speed_units_var.set("mph")
        
    # Callback Methods for Components
    def get_mappings(self):
        """Get current mappings (callback for UDP sender)"""
        return self.udp_mappings
        
    def is_udp_enabled(self):
        """Check if UDP sending is enabled (callback for UDP sender)"""
        return self.udp_enabled.get()
        
    def topic_matches(self, pattern, topic):
        """Check topic matching (callback for other components)"""
        return self.mqtt_handler.topic_matches(pattern, topic)
        
    def should_trigger(self, payload, trigger_value):
        """Check trigger conditions (callback for UDP sender)"""
        return self.mqtt_handler.should_trigger(payload, trigger_value)
        
    def log_message(self, message):
        """Log message to UI (callback for all components)"""
        if hasattr(self, 'message_display'):
            self.message_display.config(state=tk.NORMAL)
            self.message_display.insert(tk.END, message + "\n")
            self.message_display.see(tk.END)
            self.message_display.config(state=tk.DISABLED)
            
    def clear_messages(self):
        """Clear message log"""
        self.message_display.config(state=tk.NORMAL)
        self.message_display.delete(1.0, tk.END)
        self.message_display.config(state=tk.DISABLED)
        
    def on_closing(self):
        """Handle application closing"""
        if self.mqtt_handler.connected:
            self.mqtt_handler.disconnect()
        self.save_mappings()
        self.root.destroy()