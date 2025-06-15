"""
UDP Sender for MQTT UDP Bridge
Handles UDP message sending with timeout management and trigger filtering
"""

import socket
import threading
from datetime import datetime

class UDPSender:
    def __init__(self, message_callback, mappings_getter, udp_enabled_getter, topic_matches_func, should_trigger_func):
        self.message_callback = message_callback
        self.get_mappings = mappings_getter
        self.is_udp_enabled = udp_enabled_getter
        self.topic_matches = topic_matches_func
        self.should_trigger = should_trigger_func
        self.trigger_timeouts = {}  # trigger_name -> last_trigger_time
    
    def process_message(self, topic, payload, timestamp, current_time, speed_calculated):
        """Process incoming MQTT message and handle UDP sending"""
        # Check for matching UDP mappings
        for mapping in self.get_mappings():
            if self.topic_matches(mapping['topic'], topic):
                # Check if we should trigger based on the payload value
                trigger_value = mapping.get('trigger_value', '')
                trigger_name = mapping.get('trigger_name', 'Unnamed')
                timeout = mapping.get('timeout', 0.0)
                
                if trigger_value == '' or self.should_trigger(payload, trigger_value):
                    # Check timeout to prevent double triggering
                    if timeout > 0 and trigger_name in self.trigger_timeouts:
                        last_trigger = self.trigger_timeouts[trigger_name]
                        time_diff = (current_time - last_trigger).total_seconds()
                        if time_diff < timeout:
                            self.message_callback(f"⏸️ [{timestamp}] {trigger_name} ignored → Too soon ({time_diff:.1f}s < {timeout:.1f}s timeout)")
                            continue
                    
                    # Update timeout tracking
                    self.trigger_timeouts[trigger_name] = current_time
                    
                    # Create human-readable trigger message
                    udp_target = f"{mapping['udp_ip']}:{mapping['udp_port']}"
                    
                    if self.is_udp_enabled():
                        # Get delay for this mapping
                        udp_delay = mapping.get('udp_delay', 0.0)
                        if udp_delay > 0:
                            if speed_calculated:
                                self.message_callback(f"🚗 [{timestamp}] {trigger_name} triggered → Sending to {udp_target} in {udp_delay:.1f}s (Speed: {speed_calculated})")
                            else:
                                self.message_callback(f"🔔 [{timestamp}] {trigger_name} triggered → Sending to {udp_target} in {udp_delay:.1f}s")
                            # Schedule UDP send with delay
                            threading.Timer(udp_delay, self.send_udp, args=(mapping, topic, payload, speed_calculated)).start()
                        else:
                            # Send immediately
                            if speed_calculated:
                                self.message_callback(f"🚗 [{timestamp}] {trigger_name} triggered → Sent to {udp_target} (Speed: {speed_calculated})")
                            else:
                                self.message_callback(f"🔔 [{timestamp}] {trigger_name} triggered → Sent to {udp_target}")
                            threading.Thread(target=self.send_udp, args=(mapping, topic, payload, speed_calculated), daemon=True).start()
                    else:
                        self.message_callback(f"🚫 [{timestamp}] {trigger_name} triggered → UDP disabled")
    
    def send_udp(self, mapping, topic, payload, calculated_speed=None):
        """Send UDP message to specified target"""
        try:
            # Format the UDP message with speed if available
            udp_message = mapping['udp_message'].replace('{payload}', payload).replace('{topic}', topic)
            
            if calculated_speed and '{speed}' in udp_message:
                udp_message = udp_message.replace('{speed}', calculated_speed)
            elif '{speed}' in udp_message:
                udp_message = udp_message.replace('{speed}', 'N/A')
            
            # Send UDP message
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)  # 5 second timeout
            sock.sendto(udp_message.encode('utf-8'), (mapping['udp_ip'], mapping['udp_port']))
            sock.close()
            
            # Only log if there was a delay (immediate sends are logged in process_message)
            if mapping.get('udp_delay', 0.0) > 0:
                timestamp = datetime.now().strftime("%H:%M:%S")
                trigger_name = mapping.get('trigger_name', 'Unnamed')
                if calculated_speed:
                    self.message_callback(f"🚗 [{timestamp}] {trigger_name} delayed send completed to {mapping['udp_ip']}:{mapping['udp_port']} (Speed: {calculated_speed})")
                else:
                    self.message_callback(f"🔔 [{timestamp}] {trigger_name} delayed send completed to {mapping['udp_ip']}:{mapping['udp_port']}")
            
        except Exception as e:
            self.message_callback(f"❌ UDP send failed to {mapping['udp_ip']}:{mapping['udp_port']}: {str(e)}")
    
    def clear_timeouts(self):
        """Clear all trigger timeout tracking"""
        self.trigger_timeouts.clear()