import pyshark
from collections import defaultdict

# --- Config ---
pcap_file = 'challenge2.pcapng'
coap_me_ip = "134.102.218.18"
coap_filter = f'coap && ip.dst == {coap_me_ip} && coap.code == 1 && (coap.type == 0 || coap.type == 1) && !_ws.malformed'

# defaultdict to store counts of CON and NON requests for each path
# The default value is a dictionary with keys 'CON' and 'NON' initialized to 0
# This allows us to increment the counts easily without checking for existence first
counts = defaultdict(lambda: defaultdict(int))
cap = pyshark.FileCapture(pcap_file, display_filter=coap_filter, keep_packets=False)
for packet in cap:
    # Path extraction
    path = packet.coap.opt_uri_path
    # Increment CON (0) or NON (1) count
    counts[path]['CON' if int(packet.coap.type) == 0 else 'NON'] += 1

# --- Output ---
final_match_count = 0
# Find and print paths with equal CON and NON counts
for path, c in counts.items():
    if c.get('CON', 0) == c.get('NON', 0) and c.get('CON', 0) > 0:
        print(f"Path: {path}, CON: {c['CON']}, NON: {c['NON']}")
        final_match_count += 1
# --- Output ---
print(f"\n--- RESULT ---")
print(f"CQ2: Found {final_match_count} different resources that received the same number of CON and NON requests.")