"""
Speed Calculator for MQTT UDP Bridge
Handles vehicle speed calculation based on sensor timing
"""

import json
from datetime import datetime

class SpeedCalculator:
    def __init__(self, message_callback, topic_matches_func):
        self.speed_tracking = {}  # topic -> {'start_time': time, 'car_length': length, 'speed_units': units}
        self.message_callback = message_callback
        self.topic_matches = topic_matches_func
        
    def handle_speed_calculation(self, topic, payload, timestamp, mappings=None):
        """Handle speed calculation based on sensor state changes"""
        try:
            # Parse the JSON payload to get the Val field
            data = json.loads(payload)
            
            if isinstance(data, dict) and "Val" in data:
                val = int(data["Val"])
                current_time = datetime.now()
                
                # Find mapping for this topic to get car length and speed units
                mapping = None
                if mappings:
                    for m in mappings:
                        if self.topic_matches(m['topic'], topic):
                            mapping = m
                            break
                
                if not mapping or mapping.get('car_length', 0) <= 0:
                    return None  # No speed calculation if no car length set
                
                car_length = mapping.get('car_length', 4.5)
                speed_units = mapping.get('speed_units', 'mph')
                
                if val == 1:
                    # Car starts passing over sensor - record start time
                    self.speed_tracking[topic] = {
                        'start_time': current_time,
                        'car_length': car_length,
                        'speed_units': speed_units
                    }
                    self.message_callback(f"🚗 Vehicle detected on {topic}")
                    return None
                
                elif val == 0 and topic in self.speed_tracking:
                    # Car finishes passing over sensor - calculate speed
                    tracking_data = self.speed_tracking[topic]
                    start_time = tracking_data['start_time']
                    car_length = tracking_data['car_length']
                    speed_units = tracking_data['speed_units']
                    
                    # Calculate time difference in seconds
                    time_diff = (current_time - start_time).total_seconds()
                    
                    if time_diff > 0:
                        # Speed = distance / time
                        speed_ms = car_length / time_diff  # meters per second
                        
                        # Convert to desired units
                        if speed_units == "mph":
                            speed = speed_ms * 2.23694  # m/s to mph
                            unit_display = "mph"
                        elif speed_units == "km/h":
                            speed = speed_ms * 3.6  # m/s to km/h
                            unit_display = "km/h"
                        else:  # m/s
                            speed = speed_ms
                            unit_display = "m/s"
                        
                        speed_str = f"{speed:.1f} {unit_display}"
                        self.message_callback(f"🏁 Vehicle passed {topic}: {speed_str} (length: {car_length}m, time: {time_diff:.2f}s)")
                        
                        # Clean up tracking data
                        del self.speed_tracking[topic]
                        
                        return speed_str
                    else:
                        # Clean up tracking data for invalid measurement
                        del self.speed_tracking[topic]
                        return None
                        
        except (json.JSONDecodeError, ValueError, KeyError):
            # Not valid sensor data, skip speed calculation
            pass
        
        return None
    
    def clear_tracking(self):
        """Clear all speed tracking data"""
        self.speed_tracking.clear()