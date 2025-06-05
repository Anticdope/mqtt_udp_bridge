import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paho.mqtt.client as mqtt
from datetime import datetime
import json
import socket
import threading
import os

class MQTTUDPBridge:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT to UDP Bridge")
        self.root.geometry("900x750")
        self.root.minsize(700, 550)
        
        # Simple modern styling
        self.setup_modern_theme()
        
        self.client = None
        self.connected = False
        self.udp_mappings = []
        self.broker_settings = {'address': 'localhost', 'port': 1883, 'auto_connect': True}
        self.mappings_file = "mqtt_udp_mappings.json"
        
        # Load existing mappings and settings
        self.load_mappings()
        
        self.create_widgets()
        
        # Update display with loaded mappings
        self.update_mappings_display()
        
        # Auto-connect if enabled
        if self.broker_settings.get('auto_connect', True):
            self.root.after(1000, self.auto_connect)
        
    def setup_modern_theme(self):
        """Configure clean modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure modern styles
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Info.TLabel', font=('Segoe UI', 8))
        
        # Button styles
        style.configure('Accent.TButton', font=('Segoe UI', 9, 'bold'))
        
    def create_widgets(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # MQTT Connection tab
        self.create_mqtt_tab(notebook)
        
        # UDP Mappings tab
        self.create_udp_mappings_tab(notebook)
        
        # Messages/Log tab
        self.create_messages_tab(notebook)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("⭕ Disconnected")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
    def create_mqtt_tab(self, notebook):
        mqtt_frame = ttk.Frame(notebook)
        notebook.add(mqtt_frame, text="MQTT Connection")
        
        # Connection settings
        conn_frame = ttk.LabelFrame(mqtt_frame, text="MQTT Broker Settings", padding=10)
        conn_frame.pack(fill="x", padx=15, pady=15)
        
        # Broker
        ttk.Label(conn_frame, text="Broker:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.broker_entry = ttk.Entry(conn_frame, width=30, font=('Segoe UI', 9))
        self.broker_entry.insert(0, self.broker_settings['address'])
        self.broker_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        
        # Port
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.port_entry = ttk.Entry(conn_frame, width=10, font=('Segoe UI', 9))
        self.port_entry.insert(0, str(self.broker_settings['port']))
        self.port_entry.grid(row=0, column=3, padx=5, pady=8, sticky="w")
        
        # Connect button and status
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=15, sticky="w")
        
        self.connect_button = ttk.Button(button_frame, text="🔌 Connect", command=self.toggle_connection, style='Accent.TButton')
        self.connect_button.pack(side="left", padx=(0, 15))
        
        # Auto-connect checkbox
        self.auto_connect_var = tk.BooleanVar(value=self.broker_settings.get('auto_connect', True))
        ttk.Checkbutton(button_frame, text="Auto-connect on startup", variable=self.auto_connect_var, 
                       command=self.save_auto_connect_setting).pack(side="left", padx=(0, 15))
        
        # Connection status indicator
        self.conn_status_label = ttk.Label(button_frame, text="●", foreground="red", font=('Segoe UI', 14, 'bold'))
        self.conn_status_label.pack(side="left")
        
        # Subscribed topics display
        topics_frame = ttk.LabelFrame(mqtt_frame, text="📡 Subscribed Topics", padding=10)
        topics_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Create frame for listbox and scrollbar
        list_frame = ttk.Frame(topics_frame)
        list_frame.pack(fill="both", expand=True)
        
        self.topics_listbox = tk.Listbox(list_frame, height=8, font=('Consolas', 9))
        topics_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.topics_listbox.yview)
        self.topics_listbox.configure(yscrollcommand=topics_scrollbar.set)
        
        self.topics_listbox.pack(side="left", fill="both", expand=True)
        topics_scrollbar.pack(side="right", fill="y")
        
        conn_frame.columnconfigure(1, weight=1)
        
    def create_udp_mappings_tab(self, notebook):
        udp_frame = ttk.Frame(notebook)
        notebook.add(udp_frame, text="UDP Mappings")
        
        # Add new mapping frame
        add_frame = ttk.LabelFrame(udp_frame, text="➕ Add New Mapping", padding=10)
        add_frame.pack(fill="x", padx=15, pady=15)
        
        # Topic
        ttk.Label(add_frame, text="MQTT Topic:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.new_topic_entry = ttk.Entry(add_frame, width=25, font=('Segoe UI', 9))
        self.new_topic_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # UDP IP
        ttk.Label(add_frame, text="UDP IP:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.new_udp_ip_entry = ttk.Entry(add_frame, width=15, font=('Segoe UI', 9))
        self.new_udp_ip_entry.insert(0, "127.0.0.1")
        self.new_udp_ip_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # UDP Port
        ttk.Label(add_frame, text="UDP Port:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.new_udp_port_entry = ttk.Entry(add_frame, width=10, font=('Segoe UI', 9))
        self.new_udp_port_entry.insert(0, "8080")
        self.new_udp_port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # UDP Message
        ttk.Label(add_frame, text="UDP Message:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.new_udp_message_entry = ttk.Entry(add_frame, width=25, font=('Segoe UI', 9))
        self.new_udp_message_entry.insert(0, "{payload}")
        self.new_udp_message_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        # Add button and help
        button_help_frame = ttk.Frame(add_frame)
        button_help_frame.grid(row=2, column=0, columnspan=4, pady=15, sticky="ew")
        
        ttk.Button(button_help_frame, text="➕ Add Mapping", command=self.add_mapping).pack(side="left")
        
        # Help text
        help_text = "💡 Use {payload} for MQTT message content, {topic} for topic name"
        ttk.Label(button_help_frame, text=help_text, style='Info.TLabel').pack(side="left", padx=(20, 0))
        
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(3, weight=1)
        
        # Current mappings frame
        mappings_frame = ttk.LabelFrame(udp_frame, text="📋 Current Mappings", padding=10)
        mappings_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Create frame for treeview and scrollbar
        tree_frame = ttk.Frame(mappings_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Treeview for mappings
        columns = ("Topic", "UDP IP", "UDP Port", "UDP Message")
        self.mappings_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        for i, col in enumerate(columns):
            self.mappings_tree.heading(col, text=col)
            if col == "UDP Message":
                self.mappings_tree.column(col, width=200)
            else:
                self.mappings_tree.column(col, width=120)
        
        mappings_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.mappings_tree.yview)
        self.mappings_tree.configure(yscrollcommand=mappings_scrollbar.set)
        
        self.mappings_tree.pack(side="left", fill="both", expand=True)
        mappings_scrollbar.pack(side="right", fill="y")
        
        # Bind double-click to edit
        self.mappings_tree.bind("<Double-1>", self.edit_mapping)
        
        # Buttons
        button_frame = ttk.Frame(mappings_frame)
        button_frame.pack()
        ttk.Button(button_frame, text="✏️ Edit Selected", command=self.edit_mapping).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🗑️ Remove Selected", command=self.remove_mapping).pack(side="left", padx=5)
        
    def create_messages_tab(self, notebook):
        messages_frame = ttk.Frame(notebook)
        notebook.add(messages_frame, text="Messages & Log")
        
        # Control buttons
        control_frame = ttk.Frame(messages_frame)
        control_frame.pack(fill="x", padx=15, pady=15)
        
        ttk.Button(control_frame, text="🧹 Clear Log", command=self.clear_messages).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Reload Mappings", command=self.reload_mappings).pack(side="left", padx=5)
        
        # Enable/disable UDP sending
        self.udp_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="🚀 Enable UDP Sending", variable=self.udp_enabled).pack(side="left", padx=20)
        
        # Mappings file info
        mappings_info = ttk.Label(control_frame, text=f"📄 {self.mappings_file}", style='Info.TLabel')
        mappings_info.pack(side="right", padx=5)
        
        # Messages display
        self.message_display = scrolledtext.ScrolledText(messages_frame, wrap=tk.WORD, height=25, font=('Consolas', 9))
        self.message_display.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.message_display.config(state=tk.DISABLED)
        
    def add_mapping(self):
        topic = self.new_topic_entry.get().strip()
        udp_ip = self.new_udp_ip_entry.get().strip()
        udp_message = self.new_udp_message_entry.get().strip()
        
        try:
            udp_port = int(self.new_udp_port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "UDP Port must be a number")
            return
        
        if not topic or not udp_ip or not udp_message:
            messagebox.showerror("Error", "All fields are required")
            return
        
        # Check if topic already exists
        for mapping in self.udp_mappings:
            if mapping['topic'] == topic:
                messagebox.showerror("Error", f"Topic '{topic}' already has a mapping")
                return
        
        mapping = {
            'topic': topic,
            'udp_ip': udp_ip,
            'udp_port': udp_port,
            'udp_message': udp_message
        }
        
        self.udp_mappings.append(mapping)
        self.save_broker_settings()
        self.save_mappings()
        self.update_mappings_display()
        self.update_mqtt_subscriptions()
        
        # Clear entries
        self.new_topic_entry.delete(0, tk.END)
        self.new_udp_ip_entry.delete(0, tk.END)
        self.new_udp_ip_entry.insert(0, "127.0.0.1")
        self.new_udp_port_entry.delete(0, tk.END)
        self.new_udp_port_entry.insert(0, "8080")
        self.new_udp_message_entry.delete(0, tk.END)
        self.new_udp_message_entry.insert(0, "{payload}")
        
    def remove_mapping(self):
        selection = self.mappings_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mapping to remove")
            return
        
        item = self.mappings_tree.item(selection[0])
        topic = item['values'][0]
        
        self.udp_mappings = [m for m in self.udp_mappings if m['topic'] != topic]
        self.save_mappings()
        self.update_mappings_display()
        self.update_mqtt_subscriptions()
        
    def edit_mapping(self, event=None):
        """Edit selected mapping"""
        selection = self.mappings_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mapping to edit")
            return
        
        item = self.mappings_tree.item(selection[0])
        values = item['values']
        old_topic = values[0]
        
        # Find the mapping in our list
        mapping_to_edit = None
        for mapping in self.udp_mappings:
            if mapping['topic'] == old_topic:
                mapping_to_edit = mapping
                break
        
        if not mapping_to_edit:
            messagebox.showerror("Error", "Could not find mapping to edit")
            return
        
        # Create edit dialog
        self.show_edit_dialog(mapping_to_edit)
    
    def show_edit_dialog(self, mapping):
        """Show dialog to edit a mapping"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Mapping")
        edit_window.geometry("500x300")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Center the window
        edit_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 150, self.root.winfo_rooty() + 100))
        
        # Create form
        form_frame = ttk.LabelFrame(edit_window, text="Edit Mapping", padding=20)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Topic
        ttk.Label(form_frame, text="MQTT Topic:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        topic_entry = ttk.Entry(form_frame, width=40, font=('Segoe UI', 9))
        topic_entry.insert(0, mapping['topic'])
        topic_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # UDP IP
        ttk.Label(form_frame, text="UDP IP:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ip_entry = ttk.Entry(form_frame, width=40, font=('Segoe UI', 9))
        ip_entry.insert(0, mapping['udp_ip'])
        ip_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # UDP Port
        ttk.Label(form_frame, text="UDP Port:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        port_entry = ttk.Entry(form_frame, width=40, font=('Segoe UI', 9))
        port_entry.insert(0, str(mapping['udp_port']))
        port_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # UDP Message
        ttk.Label(form_frame, text="UDP Message:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        message_entry = ttk.Entry(form_frame, width=40, font=('Segoe UI', 9))
        message_entry.insert(0, mapping['udp_message'])
        message_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        # Help text
        help_text = "💡 Use {payload} for MQTT message content, {topic} for topic name"
        ttk.Label(form_frame, text=help_text, font=("Segoe UI", 8)).grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def save_changes():
            new_topic = topic_entry.get().strip()
            new_ip = ip_entry.get().strip()
            new_message = message_entry.get().strip()
            
            try:
                new_port = int(port_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "UDP Port must be a number")
                return
            
            if not new_topic or not new_ip or not new_message:
                messagebox.showerror("Error", "All fields are required")
                return
            
            # Check if new topic conflicts with existing mappings (except current one)
            for existing_mapping in self.udp_mappings:
                if existing_mapping != mapping and existing_mapping['topic'] == new_topic:
                    messagebox.showerror("Error", f"Topic '{new_topic}' already has a mapping")
                    return
            
            # Update the mapping
            mapping['topic'] = new_topic
            mapping['udp_ip'] = new_ip
            mapping['udp_port'] = new_port
            mapping['udp_message'] = new_message
            
            self.save_mappings()
            self.update_mappings_display()
            self.update_mqtt_subscriptions()
            
            edit_window.destroy()
            self.log_message(f"✏️ Updated mapping: {new_topic}")
        
        def cancel_edit():
            edit_window.destroy()
        
        ttk.Button(button_frame, text="💾 Save Changes", command=save_changes).pack(side="left", padx=10)
        ttk.Button(button_frame, text="❌ Cancel", command=cancel_edit).pack(side="left", padx=10)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Focus on first field
        topic_entry.focus_set()
        
    def update_mappings_display(self):
        # Clear existing items
        for item in self.mappings_tree.get_children():
            self.mappings_tree.delete(item)
        
        # Add current mappings
        for mapping in self.udp_mappings:
            self.mappings_tree.insert("", "end", values=(
                mapping['topic'],
                mapping['udp_ip'],
                mapping['udp_port'],
                mapping['udp_message']
            ))
    
    def update_mqtt_subscriptions(self):
        if self.client and self.connected:
            # Subscribe to all topics in mappings
            for mapping in self.udp_mappings:
                self.client.subscribe(mapping['topic'])
        
        # Update topics listbox
        self.topics_listbox.delete(0, tk.END)
        for mapping in self.udp_mappings:
            self.topics_listbox.insert(tk.END, mapping['topic'])
        
    def toggle_connection(self):
        if not self.connected:
            self.connect_mqtt()
        else:
            self.disconnect_mqtt()
    
    def connect_mqtt(self):
        broker = self.broker_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            self.log_message("Error: Port must be a number")
            return
        
        # Save broker settings
        self.save_broker_settings()
        
        # Create a new client instance
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Update status
        self.status_var.set(f"Connecting to {broker}:{port}...")
        self.root.update()
        
        try:
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            self.connect_button.config(text="🔌 Disconnect")
            self.connected = True
        except Exception as e:
            self.log_message(f"Connection failed: {str(e)}")
            self.status_var.set("Connection failed")
    
    def auto_connect(self):
        """Automatically connect on startup if enabled"""
        if self.broker_settings.get('auto_connect', True) and not self.connected:
            self.log_message("🔄 Auto-connecting to broker...")
            self.connect_mqtt()
    
    def save_auto_connect_setting(self):
        """Save the auto-connect setting"""
        self.broker_settings['auto_connect'] = self.auto_connect_var.get()
        self.save_mappings()
    
    def disconnect_mqtt(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        self.connect_button.config(text="🔌 Connect")
        self.connected = False
        self.status_var.set("⭕ Disconnected")
        self.conn_status_label.config(foreground="red")
        self.log_message("Disconnected from broker")
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.status_var.set(f"✅ Connected to {self.broker_entry.get()}:{self.port_entry.get()}")
            self.conn_status_label.config(foreground="green")
            self.log_message("Connected to MQTT broker")
            self.update_mqtt_subscriptions()
        else:
            conn_results = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier", 
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            reason = conn_results.get(rc, f"Unknown error code {rc}")
            self.status_var.set(f"❌ Connection failed: {reason}")
            self.conn_status_label.config(foreground="red")
            self.log_message(f"Connection failed: {reason}")
            self.connected = False
            self.connect_button.config(text="🔌 Connect")
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.log_message("Unexpected disconnection")
            self.status_var.set("⚠️ Unexpectedly disconnected")
            self.conn_status_label.config(foreground="orange")
        self.connected = False
        self.connect_button.config(text="🔌 Connect")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            topic = msg.topic
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Log the received message
            self.log_message(f"📨 [{timestamp}] {topic} → {payload}")
            
            # Check for matching UDP mappings
            for mapping in self.udp_mappings:
                if self.topic_matches(mapping['topic'], topic):
                    if self.udp_enabled.get():
                        threading.Thread(target=self.send_udp, args=(mapping, topic, payload), daemon=True).start()
                    else:
                        self.log_message(f"🚫 UDP disabled - would send to {mapping['udp_ip']}:{mapping['udp_port']}")
                    
        except Exception as e:
            self.log_message(f"Error processing message: {str(e)}")
    
    def topic_matches(self, pattern, topic):
        """Check if topic matches pattern (supports MQTT wildcards + and #)"""
        if pattern == topic:
            return True
        
        # Handle # wildcard (must be at end)
        if pattern.endswith('#'):
            prefix = pattern[:-1]
            return topic.startswith(prefix)
        
        # Handle + wildcard
        if '+' in pattern:
            pattern_parts = pattern.split('/')
            topic_parts = topic.split('/')
            
            if len(pattern_parts) != len(topic_parts):
                return False
            
            for p_part, t_part in zip(pattern_parts, topic_parts):
                if p_part != '+' and p_part != t_part:
                    return False
            return True
        
        return False
    
    def send_udp(self, mapping, topic, payload):
        try:
            # Format the UDP message
            udp_message = mapping['udp_message'].replace('{payload}', payload).replace('{topic}', topic)
            
            # Send UDP message
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)  # 5 second timeout
            sock.sendto(udp_message.encode('utf-8'), (mapping['udp_ip'], mapping['udp_port']))
            sock.close()
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_message(f"🚀 [{timestamp}] UDP → {mapping['udp_ip']}:{mapping['udp_port']} → {udp_message}")
            
        except Exception as e:
            self.log_message(f"❌ UDP send error: {str(e)}")
    
    def log_message(self, message):
        self.message_display.config(state=tk.NORMAL)
        self.message_display.insert(tk.END, message + "\n")
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)
    
    def clear_messages(self):
        self.message_display.config(state=tk.NORMAL)
        self.message_display.delete(1.0, tk.END)
        self.message_display.config(state=tk.DISABLED)
    
    def load_mappings(self):
        """Load UDP mappings and broker settings from JSON file"""
        try:
            if os.path.exists(self.mappings_file):
                with open(self.mappings_file, 'r') as f:
                    data = json.load(f)
                
                # Handle both old format (just mappings list) and new format (dict with mappings and broker)
                if isinstance(data, list):
                    # Old format - just mappings
                    self.udp_mappings = data
                    self.broker_settings = {'address': 'localhost', 'port': 1883, 'auto_connect': True}
                    print(f"Loaded {len(self.udp_mappings)} mappings from {self.mappings_file} (old format)")
                elif isinstance(data, dict):
                    # New format - mappings and broker settings
                    self.udp_mappings = data.get('mappings', [])
                    broker_data = data.get('broker', {'address': 'localhost', 'port': 1883, 'auto_connect': True})
                    # Ensure auto_connect key exists
                    if 'auto_connect' not in broker_data:
                        broker_data['auto_connect'] = True
                    self.broker_settings = broker_data
                    print(f"Loaded {len(self.udp_mappings)} mappings and broker settings from {self.mappings_file}")
                else:
                    self.udp_mappings = []
                    self.broker_settings = {'address': 'localhost', 'port': 1883, 'auto_connect': True}
                    print("Invalid file format. Starting with defaults.")
            else:
                self.udp_mappings = []
                self.broker_settings = {'address': 'localhost', 'port': 1883, 'auto_connect': True}
                print(f"No existing mappings file found. Starting with empty mappings.")
        except Exception as e:
            print(f"Error loading mappings: {str(e)}")
            self.udp_mappings = []
            self.broker_settings = {'address': 'localhost', 'port': 1883, 'auto_connect': True}
    
    def save_mappings(self):
        """Save UDP mappings and broker settings to JSON file"""
        try:
            data = {
                'broker': self.broker_settings,
                'mappings': self.udp_mappings
            }
            with open(self.mappings_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {len(self.udp_mappings)} mappings and broker settings to {self.mappings_file}")
        except Exception as e:
            print(f"Error saving mappings: {str(e)}")
            # Also log to the GUI if it exists
            if hasattr(self, 'message_display'):
                self.log_message(f"❌ Error saving mappings: {str(e)}")
    
    def save_broker_settings(self):
        """Save current broker settings from the UI"""
        try:
            self.broker_settings['address'] = self.broker_entry.get().strip()
            self.broker_settings['port'] = int(self.port_entry.get().strip())
        except ValueError:
            # If port is invalid, keep the old value
            pass
    
    def reload_mappings(self):
        """Reload mappings and broker settings from file and update displays"""
        old_count = len(self.udp_mappings)
        old_broker = f"{self.broker_settings['address']}:{self.broker_settings['port']}"
        
        self.load_mappings()
        new_count = len(self.udp_mappings)
        new_broker = f"{self.broker_settings['address']}:{self.broker_settings['port']}"
        
        # Update UI with loaded broker settings
        self.broker_entry.delete(0, tk.END)
        self.broker_entry.insert(0, self.broker_settings['address'])
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, str(self.broker_settings['port']))
        self.auto_connect_var.set(self.broker_settings.get('auto_connect', True))
        
        self.update_mappings_display()
        self.update_mqtt_subscriptions()
        
        self.log_message(f"🔄 Reloaded: {old_count} → {new_count} mappings, broker: {old_broker} → {new_broker}")
        
    def on_closing(self):
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
        # Save mappings one final time before closing
        self.save_mappings()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTUDPBridge(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()