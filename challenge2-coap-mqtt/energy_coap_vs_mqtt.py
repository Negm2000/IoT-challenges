import sys

# Constants
ETX, ERX, EC_VALVE_PROCESSING = 50e-9, 58e-9, 2.4e-3 # J/bit, J/bit, J
SENSOR_EVENTS_PER_DAY = (24 * 60) / 5 # Sensor sends 288 updates per day (every 5 minutes)
VALVE_PROCESSING_EVENTS_PER_DAY = (24 * 60) / 30 # Valve processes data every 30 minutes (48 times a day)

# CoAP Sizes (Bytes)
coap_get_req_size, coap_get_resp_size, coap_empty_ack_size = 60, 55, 14

# MQTT Sizes (Bytes)
mqtt_subscribe_size, mqtt_suback_size, mqtt_publish_size = 58, 52, 68
mqtt_connect_size, mqtt_connack_size = 54, 47
mqtt_pingreq_size, mqtt_pingresp_size = 52, 48 # Needed only for EQ2 estimate


def calculate_comm_energy(bytes_tx, bytes_rx): # Returns energy in Joules
    return ((bytes_tx * 8 * ETX) + (bytes_rx * 8 * ERX))

# EQ1a: CoAP GET+OBSERVE(NON updates)
def calculate_coap_observe():
    # Valve sends a NON-Confirmable GET+OBSERVE to sensor 
    valve_setup = calculate_comm_energy(coap_get_req_size, coap_get_resp_size) # Only once
    sensor_setup = calculate_comm_energy(coap_get_resp_size, coap_get_req_size) # Only once
    sensor_periodic = calculate_comm_energy(bytes_tx = coap_get_resp_size, bytes_rx = 0) * SENSOR_EVENTS_PER_DAY # Sensor sends NON updates (288 times a day)
    valve_periodic_comm = calculate_comm_energy(bytes_tx = 0, bytes_rx = coap_get_resp_size) * SENSOR_EVENTS_PER_DAY # Valve receives NON updates (288 times a day)
    valve_processing = EC_VALVE_PROCESSING * VALVE_PROCESSING_EVENTS_PER_DAY # Every 30 minutes valve processes the data (48 times a day)
    total_sensor = sensor_setup + sensor_periodic # Joules
    total_valve = valve_setup + valve_periodic_comm + valve_processing # Joules
    return total_sensor, total_valve 

# EQ1b: MQTT, QOS 0, no PINGs (Keep Alive > 5 min)
def calculate_mqtt_no_ping():
    sensor_connect = calculate_comm_energy(mqtt_connect_size, mqtt_connack_size) # Sensor connects to broker once and receives CONNACK
    sensor_publish = calculate_comm_energy(mqtt_publish_size, 0) * SENSOR_EVENTS_PER_DAY # Sensor publishes 288 times a day (QoS 0)
    valve_connect = calculate_comm_energy(mqtt_connect_size, mqtt_connack_size) # Valve connects to broker once and receives CONNACK
    valve_subscribe = calculate_comm_energy(mqtt_subscribe_size, mqtt_suback_size) # Valve subscribes to topic once and receives SUBACK
    valve_rx = calculate_comm_energy(0, mqtt_publish_size) * SENSOR_EVENTS_PER_DAY # Valve receives 288 messages a day (QoS 0)
    valve_processing = EC_VALVE_PROCESSING * VALVE_PROCESSING_EVENTS_PER_DAY # Every 30 minutes valve processes the data (48 times a day)
    # Total energy calculations
    total_sensor = sensor_connect + sensor_publish # Joules
    total_valve = valve_connect + valve_subscribe + valve_rx + valve_processing # Joules
    return total_sensor, total_valve

# EQ2: Optimizing MQTT by aggregating sensor data (5 min), and calculating the average on the raspberry pi which is unconstrained in power
# Offloading the processing to the raspberry pi (unconstrained in power) instead of the valve (constrained in power) --> eliminating the processing energy cost on the valve
# sending the average to the valve every 30 minutes (48 times a day) instead of sending every 5 minutes (288 times a day) reducing the number of messages sent
def optimized_mqtt():
    # Sensor is unchaneged, but the valve now receives aggregated data every 30 minutes
    sensor_connect = calculate_comm_energy(mqtt_connect_size, mqtt_connack_size) # Sensor connects to broker once and receives CONNACK
    sensor_publish = calculate_comm_energy(mqtt_publish_size, 0) * SENSOR_EVENTS_PER_DAY # Sensor publishes 288 times a day (QoS 0)
    valve_connect = calculate_comm_energy(mqtt_connect_size, mqtt_connack_size) # Valve connects to broker once and receives CONNACK
    valve_subscribe = calculate_comm_energy(mqtt_subscribe_size, mqtt_suback_size) # Valve subscribes to topic once and receives SUBACK
    valve_rx = calculate_comm_energy(0, mqtt_publish_size) * VALVE_PROCESSING_EVENTS_PER_DAY # Valve receives 48 (previously 288) messages a day (QoS 0)
    # Total energy calculations
    total_sensor = sensor_connect + sensor_publish # Joules
    total_valve = valve_connect + valve_subscribe + valve_rx # Joules
    return total_sensor, total_valve

# Main Execution & Output
coap_sensor_mj, coap_valve_mj =  [x * 1e3 for x in calculate_coap_observe()]
mqtt_sensor_mj, mqtt_valve_mj = [x * 1e3 for x in calculate_mqtt_no_ping()]
optimized_sensor_mj, optimized_valve_mj = [x * 1e3 for x in optimized_mqtt()]
savings_sensor_mj = mqtt_sensor_mj - optimized_sensor_mj
savings_valve_mj = mqtt_valve_mj - optimized_valve_mj
print("--- Numerical Results (mJ) ---")
print(f"EQ1a: Total energy consumed by: Sensor: {coap_sensor_mj:.2f} mJ + Valve: {coap_valve_mj:.2f} mJ = {coap_sensor_mj + coap_valve_mj:.2f} mJ")
print(f"EQ1b: Total energy consumed by: Sensor: {mqtt_sensor_mj:.2f} mJ + Valve: {mqtt_valve_mj:.2f} mJ = {mqtt_sensor_mj + mqtt_valve_mj:.2f} mJ")
print(f"EQ2:  Total energy consumed by: Sensor: {optimized_sensor_mj:.2f} mJ + Valve: {optimized_valve_mj:.2f} mJ   = {optimized_sensor_mj + optimized_valve_mj:.2f} mJ")
print(f"EQ2: Savings --> Sensor: {savings_sensor_mj:.2f} mJ + Valve: {savings_valve_mj:.2f} mJ = {savings_sensor_mj + savings_valve_mj:.2f} mJ")
print("-------------------------------")