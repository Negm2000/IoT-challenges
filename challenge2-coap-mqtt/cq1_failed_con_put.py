import pyshark

pcap_file = 'challenge2.pcapng'
local_server_ip = '127.0.0.1'

request_info = {} # Stores {MID: Token} of CON PUT requests
failed_request_tokens = set() # Stores unique tokens of requests that failed

# Pass 1: Find all CON PUT requests, map MID -> Token
cap1 = pyshark.FileCapture(pcap_file, display_filter=f'coap && coap.code == 3 && coap.type == 0 && ip.dst == {local_server_ip} && !_ws.malformed')
for req_packet in cap1:
    request_info[req_packet.coap.mid] = req_packet.coap.token
cap1.close()

original_request_tokens = set(request_info.values()) # Helper set for token lookup

# Pass 2: Find unsuccessful responses (Error code >= 128 OR RST type 3) FROM server
cap2 = pyshark.FileCapture(pcap_file, display_filter=f'coap && !_ws.malformed && ip.src == {local_server_ip} && (coap.code >= 128 || coap.type == 3)')
for rsp_packet in cap2:
    response_mid = rsp_packet.coap.mid
    response_token = rsp_packet.coap.token
    response_type = int(rsp_packet.coap.type)
    response_code = int(rsp_packet.coap.code)

    if response_mid in request_info: # Check 1: MID match (RST or direct ACK error)
        failed_request_tokens.add(request_info[response_mid]) # Add original request's token
    elif response_type != 3 and response_code >= 128 and response_token in original_request_tokens: # Check 2: Token match for separate errors
         failed_request_tokens.add(response_token) # Add this response's token (which matches an original request)
cap2.close()

# Final Count is the number of unique tokens associated with failed requests
final_count = len(failed_request_tokens)
# Final output
print(f"\n--- RESULT ---")
print(f"CQ1: Found {final_count} different tokens of CON PUT requests that failed (either by error code or RST).")