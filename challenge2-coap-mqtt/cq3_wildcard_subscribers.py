import pyshark

# --- Configuration ---
pcap_file = 'challenge2.pcapng'

# IPs identified from DNS responses for broker.hivemq.com in the pcap
hivemq_ips = ["35.158.43.69", "35.158.34.213", "18.192.151.104"]

clients_using_multilevel = set() # Set to store unique clients using multi-level wildcards

# --- Filtering and Processing ---
# Construct the IP filter part dynamically
ip_filter_part = " || ".join([f"ip.dst == {ip}" for ip in hivemq_ips])

# Filter for MQTT SUBSCRIBE (8) packets TO any of the HiveMQ broker IPs/Port
mqtt_filter = f'mqtt && ({ip_filter_part}) && mqtt.msgtype == 8'

print(f"Analyzing {pcap_file} for MQTT SUBSCRIBE to HiveMQ IPs ({', '.join(hivemq_ips)})...")
print(f"Using filter: {mqtt_filter}")

processed_packets = 0
cap = pyshark.FileCapture(pcap_file, display_filter=mqtt_filter, keep_packets=False)

for packet in cap:
    processed_packets += 1
    topic = packet.mqtt.topic
    if topic.endswith('#'):
        print(f"Packet {processed_packets}: Found SUBSCRIBE with multi-level wildcard '#' in topic '{topic}' from IP {packet.ip.src} with {packet.tcp.srcport}")   
        clients_using_multilevel.add((packet.ip.src, packet.tcp.srcport))
print(f"\nProcessing complete. Analyzed {processed_packets} relevant SUBSCRIBE packets.")

# --- Final Count ---
final_count = len(clients_using_multilevel)

# --- Output ---
print(f"\n--- RESULT ---")
print(f"CQ3: Found {final_count} different MQTT clients (unique source IP + Port) subscribing to HiveMQ (IPs: {', '.join(hivemq_ips)}) using multi-level wildcards ('#').")
