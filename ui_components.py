"""
UI Components for MQTT UDP Bridge
Handles all UI creation and layout management
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os

class UIComponents:
    def __init__(self, root, app_instance):
        self.root = root
        self.app = app_instance
        self.setup_modern_theme()
        
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
        
    def create_main_layout(self):
        """Create the main application layout"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Create tabs
        self.create_mqtt_tab(notebook)
        self.create_udp_mappings_tab(notebook)
        self.create_messages_tab(notebook)
        
        # Status bar
        self.create_status_bar()
        
    def create_mqtt_tab(self, notebook):
        """Create MQTT connection tab"""
        mqtt_frame = ttk.Frame(notebook)
        notebook.add(mqtt_frame, text="MQTT Connection")
        
        # Connection settings
        conn_frame = ttk.LabelFrame(mqtt_frame, text="MQTT Broker Settings", padding=10)
        conn_frame.pack(fill="x", padx=15, pady=15)
        
        # Broker
        ttk.Label(conn_frame, text="Broker:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.app.broker_entry = ttk.Entry(conn_frame, width=30, font=('Segoe UI', 9))
        self.app.broker_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        
        # Port
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.app.port_entry = ttk.Entry(conn_frame, width=10, font=('Segoe UI', 9))
        self.app.port_entry.grid(row=0, column=3, padx=5, pady=8, sticky="w")
        
        # Connect button and status
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=15, sticky="w")
        
        self.app.connect_button = ttk.Button(button_frame, text="🔌 Connect", command=self.app.toggle_connection, style='Accent.TButton')
        self.app.connect_button.pack(side="left", padx=(0, 15))
        
        # Auto-connect checkbox
        self.app.auto_connect_var = tk.BooleanVar()
        ttk.Checkbutton(button_frame, text="Auto-connect on startup", variable=self.app.auto_connect_var, 
                       command=self.app.save_auto_connect_setting).pack(side="left", padx=(0, 15))
        
        # Connection status indicator
        self.app.conn_status_label = ttk.Label(button_frame, text="●", foreground="red", font=('Segoe UI', 14, 'bold'))
        self.app.conn_status_label.pack(side="left")
        
        # Subscribed topics display
        topics_frame = ttk.LabelFrame(mqtt_frame, text="📡 Subscribed Topics", padding=10)
        topics_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Create frame for listbox and scrollbar
        list_frame = ttk.Frame(topics_frame)
        list_frame.pack(fill="both", expand=True)
        
        self.app.topics_listbox = tk.Listbox(list_frame, height=8, font=('Consolas', 9))
        topics_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.app.topics_listbox.yview)
        self.app.topics_listbox.configure(yscrollcommand=topics_scrollbar.set)
        
        self.app.topics_listbox.pack(side="left", fill="both", expand=True)
        topics_scrollbar.pack(side="right", fill="y")
        
        conn_frame.columnconfigure(1, weight=1)
        
    def create_udp_mappings_tab(self, notebook):
        """Create UDP mappings configuration tab"""
        udp_frame = ttk.Frame(notebook)
        notebook.add(udp_frame, text="UDP Mappings")
        
        # Create main container
        main_container = ttk.Frame(udp_frame)
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Add new mapping form
        self.create_add_mapping_form(main_container)
        
        # Current mappings table
        self.create_mappings_table(main_container)
        
    def create_add_mapping_form(self, parent):
        """Create the add new mapping form"""
        add_frame = ttk.LabelFrame(parent, text="➕ Add New Mapping", padding=15)
        add_frame.pack(fill="x", pady=(0, 15))
        
        # Row 1: Trigger Name and Topic
        ttk.Label(add_frame, text="Trigger Name:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.app.new_trigger_name_entry = ttk.Entry(add_frame, width=25, font=('Segoe UI', 9))
        self.app.new_trigger_name_entry.insert(0, "Sensor")
        self.app.new_trigger_name_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        
        ttk.Label(add_frame, text="MQTT Topic:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=2, padx=(15,5), pady=8, sticky="w")
        self.app.new_topic_entry = ttk.Entry(add_frame, width=30, font=('Segoe UI', 9))
        self.app.new_topic_entry.grid(row=0, column=3, padx=5, pady=8, sticky="ew")
        
        # Row 2: UDP IP and Port
        ttk.Label(add_frame, text="UDP IP:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.app.new_udp_ip_entry = ttk.Entry(add_frame, width=20, font=('Segoe UI', 9))
        self.app.new_udp_ip_entry.insert(0, "127.0.0.1")
        self.app.new_udp_ip_entry.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        
        ttk.Label(add_frame, text="UDP Port:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=2, padx=(15,5), pady=8, sticky="w")
        self.app.new_udp_port_entry = ttk.Entry(add_frame, width=15, font=('Segoe UI', 9))
        self.app.new_udp_port_entry.insert(0, "8080")
        self.app.new_udp_port_entry.grid(row=1, column=3, padx=5, pady=8, sticky="w")
        
        # Row 3: UDP Message
        ttk.Label(add_frame, text="UDP Message:", font=('Segoe UI', 9, 'bold')).grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.app.new_udp_message_entry = ttk.Entry(add_frame, width=50, font=('Segoe UI', 9))
        self.app.new_udp_message_entry.insert(0, "{payload}")
        self.app.new_udp_message_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=8, sticky="ew")
        
        # Row 4: Trigger and Timeout
        ttk.Label(add_frame, text="Trigger on:", font=('Segoe UI', 9, 'bold')).grid(row=3, column=0, padx=5, pady=8, sticky="w")
        self.app.new_trigger_entry = ttk.Entry(add_frame, width=15, font=('Segoe UI', 9))
        self.app.new_trigger_entry.insert(0, "1")
        self.app.new_trigger_entry.grid(row=3, column=1, padx=5, pady=8, sticky="w")
        
        ttk.Label(add_frame, text="Timeout (sec):", font=('Segoe UI', 9, 'bold')).grid(row=3, column=2, padx=(15,5), pady=8, sticky="w")
        self.app.new_timeout_entry = ttk.Entry(add_frame, width=15, font=('Segoe UI', 9))
        self.app.new_timeout_entry.insert(0, "1.0")
        self.app.new_timeout_entry.grid(row=3, column=3, padx=5, pady=8, sticky="w")
        
        # Row 5: UDP Delay and Car Length
        ttk.Label(add_frame, text="UDP Delay (sec):", font=('Segoe UI', 9, 'bold')).grid(row=4, column=0, padx=5, pady=8, sticky="w")
        self.app.new_delay_entry = ttk.Entry(add_frame, width=15, font=('Segoe UI', 9))
        self.app.new_delay_entry.insert(0, "0.0")
        self.app.new_delay_entry.grid(row=4, column=1, padx=5, pady=8, sticky="w")
        
        ttk.Label(add_frame, text="Car Length (m):", font=('Segoe UI', 9, 'bold')).grid(row=4, column=2, padx=(15,5), pady=8, sticky="w")
        self.app.new_car_length_entry = ttk.Entry(add_frame, width=15, font=('Segoe UI', 9))
        self.app.new_car_length_entry.insert(0, "4.5")
        self.app.new_car_length_entry.grid(row=4, column=3, padx=5, pady=8, sticky="w")
        
        # Row 6: Speed Units
        ttk.Label(add_frame, text="Speed Units:", font=('Segoe UI', 9, 'bold')).grid(row=5, column=0, padx=5, pady=8, sticky="w")
        self.app.speed_units_var = tk.StringVar(value="mph")
        speed_combo = ttk.Combobox(add_frame, textvariable=self.app.speed_units_var, values=["mph", "km/h", "m/s"], width=12, font=('Segoe UI', 9))
        speed_combo.grid(row=5, column=1, padx=5, pady=8, sticky="w")
        speed_combo.state(['readonly'])
        
        # Row 7: Add button
        button_frame = ttk.Frame(add_frame)
        button_frame.grid(row=6, column=0, columnspan=4, pady=15)
        
        ttk.Button(button_frame, text="➕ Add Mapping", command=self.app.add_mapping, style='Accent.TButton').pack(side="left")

        
        # Configure grid weights
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(3, weight=2)
        
            
    def create_mappings_table(self, parent):
        """Create the current mappings table"""
        mappings_frame = ttk.LabelFrame(parent, text="📋 Current Mappings", padding=10)
        mappings_frame.pack(fill="both", expand=True)
        
        # Create frame for treeview and scrollbar
        tree_frame = ttk.Frame(mappings_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Treeview for mappings
        columns = ("Trigger Name", "Topic", "UDP Target", "Message", "Trigger", "Delay", "Timeout")
        self.app.mappings_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        # Configure columns
        column_widths = {
            "Trigger Name": 120, "Topic": 180, "UDP Target": 130, 
            "Message": 200, "Trigger": 70, "Delay": 60, "Timeout": 70
        }
        
        for col in columns:
            self.app.mappings_tree.heading(col, text=col)
            self.app.mappings_tree.column(col, width=column_widths[col], minwidth=60)
        
        mappings_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.app.mappings_tree.yview)
        self.app.mappings_tree.configure(yscrollcommand=mappings_scrollbar.set)
        
        self.app.mappings_tree.pack(side="left", fill="both", expand=True)
        mappings_scrollbar.pack(side="right", fill="y")
        
        # Bind double-click to edit
        self.app.mappings_tree.bind("<Double-1>", self.app.edit_mapping)
        
        # Buttons
        button_frame = ttk.Frame(mappings_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="✏️ Edit Selected", command=self.app.edit_mapping).pack(side="left", padx=10)
        ttk.Button(button_frame, text="🗑️ Remove Selected", command=self.app.remove_mapping).pack(side="left", padx=10)
        ttk.Button(button_frame, text="📄 Export Config", command=self.app.export_config).pack(side="left", padx=10)
        
    def create_messages_tab(self, notebook):
        """Create messages and log tab"""
        messages_frame = ttk.Frame(notebook)
        notebook.add(messages_frame, text="Messages & Log")
        
        # Control buttons
        control_frame = ttk.Frame(messages_frame)
        control_frame.pack(fill="x", padx=15, pady=15)
        
        ttk.Button(control_frame, text="🧹 Clear Log", command=self.app.clear_messages).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🔄 Reload Mappings", command=self.app.reload_mappings).pack(side="left", padx=5)
        
        # Enable/disable UDP sending
        self.app.udp_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="🚀 Enable UDP Sending", variable=self.app.udp_enabled).pack(side="left", padx=20)
        
        # Mappings file info
        mappings_info = ttk.Label(control_frame, text="📄 Loading...", style='Info.TLabel')
        mappings_info.pack(side="right", padx=5)
        self.app.mappings_info_label = mappings_info
        
        # Messages display
        self.app.message_display = scrolledtext.ScrolledText(messages_frame, wrap=tk.WORD, height=30, font=('Consolas', 9))
        self.app.message_display.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.app.message_display.config(state=tk.DISABLED)
        
    def create_status_bar(self):
        """Create status bar at bottom of window"""
        self.app.status_var = tk.StringVar()
        self.app.status_var.set("⭕ Disconnected")
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.app.status_bar = ttk.Label(status_frame, textvariable=self.app.status_var, relief=tk.SUNKEN, anchor=tk.W, font=('Segoe UI', 9))
        self.app.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Version label
        version_label = ttk.Label(status_frame, text="v2.0", font=('Segoe UI', 8), foreground='gray')
        version_label.pack(side=tk.RIGHT, padx=5)
        
    def show_edit_dialog(self, mapping):
        """Show dialog to edit a mapping"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Mapping")
        edit_window.geometry("700x700")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Center the window
        edit_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 200, self.root.winfo_rooty() + 75))
        
        return self._create_edit_form(edit_window, mapping)
        
    def _create_edit_form(self, parent, mapping):
        """Create the edit form inside the dialog"""
        # Create scrollable form
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Edit UDP Mapping", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create form in a LabelFrame
        form_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=20)
        form_frame.pack(fill="both", expand=True)
        
        # Create form fields and return them for the calling function to handle
        return self._create_edit_fields(form_frame, mapping, parent)
        
    def _create_edit_fields(self, form_frame, mapping, dialog_window):
        """Create edit form fields and return entry widgets"""
        entries = {}
        
        # Trigger Name
        ttk.Label(form_frame, text="Trigger Name:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        entries['trigger_name'] = ttk.Entry(form_frame, width=50, font=('Segoe UI', 9))
        entries['trigger_name'].insert(0, mapping.get('trigger_name', ''))
        entries['trigger_name'].grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Topic
        ttk.Label(form_frame, text="MQTT Topic:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        entries['topic'] = ttk.Entry(form_frame, width=50, font=('Segoe UI', 9))
        entries['topic'].insert(0, mapping['topic'])
        entries['topic'].grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Create sections for better organization
        self._create_edit_sections(form_frame, mapping, entries)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        # Return entries and button frame for the main app to handle
        return entries, button_frame, dialog_window
        
    def _create_edit_sections(self, form_frame, mapping, entries):
        """Create organized sections in edit dialog"""
        # UDP Target section
        target_frame = ttk.LabelFrame(form_frame, text="UDP Target", padding=10)
        target_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=15, sticky="ew")
        
        ttk.Label(target_frame, text="IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        entries['ip'] = ttk.Entry(target_frame, width=20, font=('Segoe UI', 9))
        entries['ip'].insert(0, mapping['udp_ip'])
        entries['ip'].grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(target_frame, text="Port:").grid(row=0, column=2, padx=(15,5), pady=5, sticky="w")
        entries['port'] = ttk.Entry(target_frame, width=10, font=('Segoe UI', 9))
        entries['port'].insert(0, str(mapping['udp_port']))
        entries['port'].grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Message section
        msg_frame = ttk.LabelFrame(form_frame, text="UDP Message", padding=10)
        msg_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=15, sticky="ew")
        
        ttk.Label(msg_frame, text="Message Template:").grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        entries['message'] = tk.Text(msg_frame, width=50, height=3, font=('Segoe UI', 9))
        entries['message'].insert('1.0', mapping['udp_message'])
        entries['message'].grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Continue with other sections...
        self._create_trigger_section(form_frame, mapping, entries)
        self._create_speed_section(form_frame, mapping, entries)
        
    def _create_trigger_section(self, form_frame, mapping, entries):
        """Create trigger settings section"""
        trigger_frame = ttk.LabelFrame(form_frame, text="Trigger Settings", padding=10)
        trigger_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=15, sticky="ew")
        
        ttk.Label(trigger_frame, text="Timeout (sec):").grid(row=0, column=2, padx=(15,5), pady=5, sticky="w")
        entries['timeout'] = ttk.Entry(trigger_frame, width=15, font=('Segoe UI', 9))
        entries['timeout'].insert(0, str(mapping.get('timeout', 1.0)))
        entries['timeout'].grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(trigger_frame, text="UDP Delay (sec):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        entries['delay'] = ttk.Entry(trigger_frame, width=15, font=('Segoe UI', 9))
        entries['delay'].insert(0, str(mapping.get('udp_delay', 0.0)))
        entries['delay'].grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
    def _create_speed_section(self, form_frame, mapping, entries):
        """Create speed calculation section"""
        speed_frame = ttk.LabelFrame(form_frame, text="Speed Calculation", padding=10)
        speed_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=15, sticky="ew")
        
        ttk.Label(speed_frame, text="Car Length (m):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        entries['car_length'] = ttk.Entry(speed_frame, width=15, font=('Segoe UI', 9))
        entries['car_length'].insert(0, str(mapping.get('car_length', 4.5)))
        entries['car_length'].grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(speed_frame, text="Speed Units:").grid(row=0, column=2, padx=(15,5), pady=5, sticky="w")
        entries['speed_units_var'] = tk.StringVar(value=mapping.get('speed_units', 'mph'))
        entries['speed_units'] = ttk.Combobox(speed_frame, textvariable=entries['speed_units_var'], values=["mph", "km/h", "m/s"], width=12, font=('Segoe UI', 9))
        entries['speed_units'].grid(row=0, column=3, padx=5, pady=5, sticky="w")
        entries['speed_units'].state(['readonly'])
        
        
    def show_export_dialog(self):
        """Show file export dialog"""
        return filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
    def show_error(self, title, message):
        """Show error dialog"""
        messagebox.showerror(title, message)
        
    def show_warning(self, title, message):
        """Show warning dialog"""
        messagebox.showwarning(title, message)
        
    def show_info(self, title, message):
        """Show info dialog"""
        messagebox.showinfo(title, message)