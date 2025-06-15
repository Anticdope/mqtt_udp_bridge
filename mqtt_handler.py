"""
MQTT Handler for MQTT UDP Bridge
Manages MQTT connections, subscriptions, and message processing
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime

class MQTTHandler:
    def __init__(self, message_callback, speed_calculator, udp_sender):
        self.client = None
        self.connected = False
        self.subscribed_topics = set()
        self.message_callback = message_callback
        self.speed_calculator = speed_calculator
        self.udp_sender = udp_sender
        
    def connect(self, broker, port):
        """Connect to MQTT broker"""
        try:
            # Create a new client instance
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            self.connected = True
            return True
            
        except Exception as e:
            self.message_callback(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        self.connected = False
        self.subscribed_topics = set()
    
    def update_subscriptions(self, mappings):
        """Update MQTT subscriptions based on current mappings"""
        if not self.client or not self.connected:
            self.subscribed_topics = set()
            return
        
        # Get current topics we should be subscribed to
        new_topics = set(mapping['topic'] for mapping in mappings)
        
        # Subscribe to new topics (silently)
        topics_to_subscribe = new_topics - self.subscribed_topics
        for topic in topics_to_subscribe:
            self.client.subscribe(topic)
        
        # Unsubscribe from removed topics (silently)
        topics_to_unsubscribe = self.subscribed_topics - new_topics
        for topic in topics_to_unsubscribe:
            self.client.unsubscribe(topic)
        
        # Update our tracking
        self.subscribed_topics = new_topics
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection result"""
        if rc == 0:
            self.message_callback("Connected to MQTT broker")
            # Clear subscribed topics tracking since this is a new connection
            self.subscribed_topics = set()
            return True
        else:
            conn_results = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier", 
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            reason = conn_results.get(rc, f"Unknown error code {rc}")
            self.message_callback(f"Connection failed: {reason}")
            self.connected = False
            return False
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection"""
        if rc != 0:
            self.message_callback("Unexpected disconnection")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message"""
        try:
            payload = msg.payload.decode('utf-8')
            topic = msg.topic
            timestamp = datetime.now().strftime("%H:%M:%S")
            current_time = datetime.now()
            
            # Handle speed calculation for sensor data
            speed_calculated = self.speed_calculator.handle_speed_calculation(topic, payload, timestamp)
            
            # Let the UDP sender handle the message processing
            self.udp_sender.process_message(topic, payload, timestamp, current_time, speed_calculated)
                    
        except Exception as e:
            self.message_callback(f"❌ Error processing message: {str(e)}")
    
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
    
    def should_trigger(self, payload, trigger_value):
        """Check if the payload should trigger UDP sending"""
        if trigger_value == '':
            return True  # Empty trigger means send on any value
        
        # First try exact string match
        if payload.strip() == trigger_value:
            return True
        
        # Try to parse as JSON and check if it contains the trigger value
        try:
            data = json.loads(payload)
            
            # If it's a simple value, compare directly
            if isinstance(data, (str, int, float)):
                return str(data) == trigger_value
            
            # If it's a dict, look for the "Val" field first (Advantech format)
            if isinstance(data, dict):
                # Check "Val" field first (your specific sensor format)
                if "Val" in data:
                    return str(data["Val"]) == trigger_value
                
                # Check other common value field names as fallback
                for key in ['value', 'val', 'state', 'status', 'data']:
                    if key in data:
                        return str(data[key]) == trigger_value
                
                # If no common fields found, check if any value matches
                for value in data.values():
                    if str(value) == trigger_value:
                        return True
            
        except (json.JSONDecodeError, TypeError):
            # Not JSON, fall back to string comparison
            pass
        
        # Try numeric comparison
        try:
            payload_num = float(payload.strip())
            trigger_num = float(trigger_value)
            return payload_num == trigger_num
        except (ValueError, TypeError):
            pass
        
        return False