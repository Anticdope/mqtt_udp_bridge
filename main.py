#!/usr/bin/env python3
"""
MQTT to UDP Bridge v2.0
Main application entry point
"""

import tkinter as tk
from mqtt_udp_bridge import MQTTUDPBridge

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = MQTTUDPBridge(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()