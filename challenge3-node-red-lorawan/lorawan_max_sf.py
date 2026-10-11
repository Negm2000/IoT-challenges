import math

# --- Parameters ---
N_nodes = 50
lambda_node_per_sec = 1.0 / 60.0  # Packet rate per node in packets/second
DER_threshold = 0.70

# Airtime for each SF in milliseconds (from https://www.thethingsnetwork.org/airtime-calculator)
airtimes_ms = {
    7: 77.1,
    8: 143.9,
    9: 267.3,
    10: 493.6,
    11: 987.1,
    12: 1974.3
}

# --- Calculations ---

# Calculate total network traffic rate
lambda_total_per_sec = N_nodes * lambda_node_per_sec

print(f"Number of Nodes (N): {N_nodes}")
print(f"Total Network Traffic Rate (Lambda_total): {lambda_total_per_sec:.4f} packets/second")
print(f"Required Success Rate (DER): >= {DER_threshold:.2f}")
print("-" * 30)

valid_sfs = []

# Iterate through Spreading Factors
# Sorting keys ensures we process from SF7 to SF12
for sf in airtimes_ms.keys():
    # Get airtime and convert to seconds
    t_packet_ms = airtimes_ms[sf]
    t_packet_s = t_packet_ms / 1000.0

    # Calculate offered load (G)
    G = lambda_total_per_sec * t_packet_s

    # Calculate success rate (DER) using Aloha formula
    DER = math.exp(-2 * G)

    print(f"SF{sf}:")
    print(f"  Airtime (T_packet) = {t_packet_ms:.1f} ms = {t_packet_s:.4f} s")
    print(f"  Offered Load (G)   = {G:.4f}")
    print(f"  Calculated DER     = {DER:.4f}")

    # Check if DER meets the threshold
    if DER >= DER_threshold:
        print(f"  ---> Meets threshold (>= {DER_threshold:.2f})")
        valid_sfs.append(sf)
    else:
        print(f"  ---> Does NOT meet threshold")
    print("-" * 10)

print("=" * 30)

# Determine the biggest valid SF
if not valid_sfs:
    print("Result: No Spreading Factor meets the 70% success rate requirement.")
else:
    biggest_valid_sf = max(valid_sfs)
    print(f"Result: Spreading Factors meeting the requirement: {valid_sfs}")
    print(f"The biggest LoRa SF for having a success rate of at least 70% is: SF{biggest_valid_sf}")
print("=" * 30) 