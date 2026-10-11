import pyshark

pcap_file = 'challenge2.pcapng'

# --- Pass 1: Identify all Last Will Topics ---
lwt_topics = set()
print("--- Pass 1: Identifying Last Will Topics ---")
lwt_filter = 'mqtt.conflag.willflag == 1'
lwt_cap = pyshark.FileCapture(pcap_file, display_filter=lwt_filter, keep_packets=False)
for packet in lwt_cap:
    lwt_topics.add(str(packet.mqtt.willtopic))
    print(f"Found LWT topic: {packet.mqtt.willtopic}") 
lwt_cap.close()

# --- Pass 2: Identify non-wildcard subscriptions (Client IP+Port, Topic) ---
# Store tuples: (subscriber_ip, subscriber_port, subscribed_topic)
non_wildcard_subscription_tuples = set()
print("\n--- Pass 2: Identifying Non-Wildcard Subscriptions by Client (IP+Port) ---")
# Filter for SUBSCRIBE messages only
sub_filter = 'mqtt.msgtype == 8 && !_ws.malformed'
sub_cap = pyshark.FileCapture(pcap_file, display_filter=sub_filter, keep_packets=False)
for packet in sub_cap:
    subscriber_ip = packet.ip.src if 'IP' in packet else packet.ipv6.src
    subscriber_port = packet.tcp.srcport
    topic = str(packet.mqtt.topic)
    # Check if the *subscription* is non-wildcard
    if '#' not in topic and '+' not in topic:
        subscription_tuple = (subscriber_ip, subscriber_port, topic)
        non_wildcard_subscription_tuples.add(subscription_tuple)
sub_cap.close()

# --- Pass 3: Find PUBLISH messages matching LWTs and correlate with subscriber (IP+Port) ---
# Stores unique client identifiers (ip, port) that received a relevant LWT
lwt_receivers_ip_port = set()
print("\n--- Pass 3: Correlating PUBLISH Messages with LWTs and Subscriptions ---")
# Filter for PUBLISH messages only
pub_filter = 'mqtt.msgtype == 3 && !_ws.malformed'
pub_cap = pyshark.FileCapture(pcap_file, display_filter=pub_filter, keep_packets=False)
for packet in pub_cap:
    publish_topic = str(packet.mqtt.topic)
    # Condition 1: Is the published topic a Last Will Topic?
    if publish_topic in lwt_topics:
        # Condition 2: Find matching non-wildcard subscription(s) for this topic
        for sub_ip, sub_port, sub_topic in non_wildcard_subscription_tuples:
            if sub_topic == publish_topic:
                client_id = (sub_ip, sub_port)
                if client_id not in lwt_receivers_ip_port: # Avoid duplicate prints for same client
                    print(f"MATCH: Client {client_id} received message on last will topic:'{publish_topic}'.")
                lwt_receivers_ip_port.add(client_id)
pub_cap.close()

# --- Final Count ---
final_count = len(lwt_receivers_ip_port)
# --- Output ---
print(f"\n--- RESULT ---")
print(f"Found {final_count} unique MQTT client connections (unique source IP + source Port) that RECEIVED a Last Will message derived from a subscription WITHOUT a wildcard.")