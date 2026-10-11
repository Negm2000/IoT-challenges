import math
from itertools import product
from collections import Counter
from fractions import Fraction
import matplotlib.pyplot as plt
import numpy as np

# Memoization dictionaries
memo_probs_frac = {}  # Stores probabilities P(s | N, L)
memo_D_optimal_frac = {} # Stores results for D_optimal(k)

def calculate_probs_of_s_successes_frac(N_tags, L_slots):
    state = (N_tags, L_slots)
    if state in memo_probs_frac:
        return memo_probs_frac[state]

    if N_tags == 0:
        memo_probs_frac[state] = {0: Fraction(1, 1)} # 0 successes with probability 1
        return memo_probs_frac[state]
    
    if L_slots == 0: # No slots for tags to transmit in, 0 successes
        # All N_tags are unresolved (0 successes), assuming N_tags > 0.
        memo_probs_frac[state] = {0: Fraction(1,1)}
        return memo_probs_frac[state]

    num_total_assignments_int = L_slots ** N_tags
    s_outcome_counts = Counter() # Stores counts: {num_successes: occurrences}

    for assignment_choices in product(range(L_slots), repeat=N_tags):
        slot_occupancy = Counter(assignment_choices) # Counts tags per slot
        num_successes_for_this_assignment = 0
        for slot_idx in slot_occupancy:
            if slot_occupancy[slot_idx] == 1: # Slot has exactly one tag
                num_successes_for_this_assignment += 1
        s_outcome_counts[num_successes_for_this_assignment] += 1
            
    probabilities = {
        s: Fraction(count, num_total_assignments_int)
        for s, count in s_outcome_counts.items()
    }
    
    # Ensure all s from 0 to N_tags have a probability (even if 0) for complete output
    for s_val in range(N_tags + 1):
        if s_val not in probabilities:
            probabilities[s_val] = Fraction(0)
            
    memo_probs_frac[state] = probabilities
    return probabilities

def D_expected_slots_optimal(k_tags, given_Ds_param=None):
    if k_tags == 0:
        return Fraction(0)
    
    # Use a local copy or passed-in dictionary for the "given" values for this call context
    current_given_Ds = given_Ds_param if given_Ds_param is not None else {}

    if k_tags in current_given_Ds: # Use given values first if they exist for this k_tags
         if k_tags not in memo_D_optimal_frac: # Store if not already, to make it canonical for future use
            memo_D_optimal_frac[k_tags] = current_given_Ds[k_tags]
         return current_given_Ds[k_tags]

    if k_tags in memo_D_optimal_frac: # Then check global memo for prior calculations
        return memo_D_optimal_frac[k_tags]

    if k_tags == 1: # D(1) is always 1 if not specified otherwise
        memo_D_optimal_frac[1] = Fraction(1)
        return Fraction(1)

    L_slots = k_tags 
    probs_s_successes = calculate_probs_of_s_successes_frac(k_tags, L_slots)
    
    sum_term_numerator = Fraction(0)
    for s, prob_s in probs_s_successes.items():
        if prob_s == 0: continue # Optimization
        if s == 0: # P(0 | k,L) is handled in the denominator
            continue 
        # For D_optimal(k_tags-s), it might use a value from current_given_Ds or recurse further.
        sum_term_numerator += prob_s * D_expected_slots_optimal(k_tags - s, current_given_Ds)

    prob_zero_success = probs_s_successes.get(0, Fraction(0)) # P(0 | k,L)
                                                     
    if prob_zero_success == 1 and k_tags > 0 :
        # This should ideally not happen for L_slots = k_tags and k_tags > 0
        # This implies D(k) is infinite, division by zero in the formula.
        print(f"Critical Warning: P(s=0) is 1 for D_optimal({k_tags}) with L_slots={L_slots}. D({k_tags}) is effectively infinite.")
        memo_D_optimal_frac[k_tags] = float('inf') 
        return memo_D_optimal_frac[k_tags]

    denominator = Fraction(1) - prob_zero_success
    if denominator == 0: # Should be caught by prob_zero_success == 1
         if k_tags > 0:
            print(f"Error: Denominator is zero for D_optimal({k_tags}). P(s=0) is 1.")
            memo_D_optimal_frac[k_tags] = float('inf')
            return memo_D_optimal_frac[k_tags]
         else: # k_tags == 0, D(0) = 0
            return Fraction(0)

    result = (Fraction(L_slots) + sum_term_numerator) / denominator
    memo_D_optimal_frac[k_tags] = result
    return result

# --- Main logic for Exercise 3 ---
print("--- Exercise 3: RFID Collision Resolution Efficiency ---")

# 0. Given D values for optimal frame sizes and pre-populate memo
N_initial_tags = 4
# These are D(k) when frame size L=k
optimal_Ds_given = {
    0: Fraction(0),
    1: Fraction(1),      # Standard D(1)
    2: Fraction(4),      # Given L2=4 for r=N
    3: Fraction(51, 8)   # Given L3=51/8 for r=N
}
# Pre-populate memo_D_optimal_frac with given values. D_expected_slots_optimal will use them.
for k, val in optimal_Ds_given.items():
    memo_D_optimal_frac[k] = val

# 1. Calculate D(k) for optimal frame sizes (up to N_initial_tags=4)
# The D_expected_slots_optimal will use the pre-populated memo for k=0,1,2,3.
# It will compute D(4) using these values.
D_values_optimal_computed = {} # To store all D(k) for optimal L=k frames
for k_val_calc in range(N_initial_tags + 1):
    D_values_optimal_computed[k_val_calc] = D_expected_slots_optimal(k_val_calc, optimal_Ds_given)

print("\nOptimal D values (D(k) for frame size k):")
for k_val in sorted(D_values_optimal_computed.keys()):
    val = D_values_optimal_computed[k_val]
    if isinstance(val, Fraction):
        print(f"  D({k_val}) = {val} (float: {float(val):.4f})")
    else: # For potential float('inf')
        print(f"  D({k_val}) = {val}")


# 2. Calculate efficiency for different initial frame sizes r1
initial_frame_sizes_r1 = [1, 2, 3, 4, 5, 6]
efficiencies_eta_float = []
expected_total_slots_list_float = []
results_for_report = [] # To store (r1, D(N,r1) as fraction, eta as fraction)

print("\nCalculating D(N,r1) and efficiencies η for N=4:")
for r1_val in initial_frame_sizes_r1:
    probs_first_frame = calculate_probs_of_s_successes_frac(N_initial_tags, r1_val)
    
    expected_slots_after_first_frame = Fraction(0)
    for s_successes, prob_s in probs_first_frame.items():
        if prob_s == 0: continue # Optimization
        remaining_tags = N_initial_tags - s_successes
        D_val_for_remaining = D_values_optimal_computed[remaining_tags]
        expected_slots_after_first_frame += prob_s * D_val_for_remaining
        
    total_expected_slots_D_N_r1_frac = Fraction(r1_val) + expected_slots_after_first_frame
    
    eta_frac = Fraction(0)
    if total_expected_slots_D_N_r1_frac > 0 : 
        eta_frac = Fraction(N_initial_tags) / total_expected_slots_D_N_r1_frac
    elif N_initial_tags == 0: 
        eta_frac = Fraction(0)

    efficiencies_eta_float.append(float(eta_frac))
    expected_total_slots_list_float.append(float(total_expected_slots_D_N_r1_frac))
    results_for_report.append({
        "r1": r1_val,
        "D_N_r1_frac": total_expected_slots_D_N_r1_frac,
        "D_N_r1_float": float(total_expected_slots_D_N_r1_frac),
        "eta_frac": eta_frac,
        "eta_float": float(eta_frac)
    })
    
print("\n--- Results Table ---")
print("r1 | D(N=4, r1) (Slots) | η (Efficiency)")
print("---|--------------------|---------------")
for res in results_for_report:
    print(f"{res['r1']:2d} | {str(res['D_N_r1_frac']):>18} ({res['D_N_r1_float']:7.4f}) | {str(res['eta_frac']):>13} ({res['eta_float']:.4f})")


# 3. Plotting
plt.figure(figsize=(10, 6))
plt.plot(initial_frame_sizes_r1, efficiencies_eta_float, marker='o', linestyle='-')
plt.title('Collision Resolution Efficiency (η) vs. Initial Frame Size (r1) for N=4 Tags', fontsize=14)
plt.xlabel('Initial Frame Size (r1)', fontsize=12)
plt.ylabel('Efficiency (η = N / D(N,r1))', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xticks(initial_frame_sizes_r1) 
for i, r1_val_plot in enumerate(initial_frame_sizes_r1): # Renamed r1_val to r1_val_plot to avoid conflict
    plt.annotate(f"{efficiencies_eta_float[i]:.4f}", (r1_val_plot, efficiencies_eta_float[i]), textcoords="offset points", xytext=(0,5), ha='center')

plot_filename = "Exercise3_efficiency_plot.png"
try:
    plt.savefig(plot_filename)
    print(f"\nPlot saved as {plot_filename}")
except Exception as e:
    print(f"Error saving plot: {e}. Ensure Matplotlib backend is suitable (e.g., Agg for non-GUI).")

# 4. Find r1 for max η and comment
max_eta_val = -1.0
for res_item in results_for_report:
    if res_item['eta_float'] > max_eta_val:
        max_eta_val = res_item['eta_float']
best_r1_values_list = [res_item['r1'] for res_item in results_for_report if abs(res_item['eta_float'] - max_eta_val) < 1e-9]


print("\n--- Summary of Efficiency Analysis ---")
print(f"Maximum efficiency η = {max_eta_val:.4f}")
if len(best_r1_values_list) == 1:
    print(f"This maximum efficiency is achieved at r1 = {best_r1_values_list[0]}")
else:
    print(f"This maximum efficiency is achieved at r1 values: {best_r1_values_list}")

comment_text = """
Comments on the results:
The efficiency η quantifies how effectively communication slots are used for successful tag identification. It is defined as the total number of tags (N) divided by the total expected number of slots required for their arbitration (D(N, r1)).

- When the initial frame size (r1) is too small compared to the number of tags (N=4):
  For example, at r1=1, all 4 tags must choose the single available slot, leading to a guaranteed collision. No tags are resolved in the first frame. The entire backlog of 4 tags is then handled by subsequent optimally-sized frames, leading to a high D(4,1) (which is 1 + D_optimal(4)) and thus very low efficiency.
  For r1=2, there's a high chance of initial collisions as 4 tags contend for 2 slots. This results in a larger expected remaining backlog and thus higher D(4,2) and lower efficiency compared to optimal r1.

- When the initial frame size (r1) is too large:
  For example, at r1=6 for N=4 tags. While this reduces the probability of initial collisions (increasing the chance that more tags are resolved in the first frame), it also means that if tags are identified quickly, many of the r1 slots in the first frame go unused (empty). These empty slots are "wasted" in the context of the first frame's fixed cost, contributing to a higher D(N,r1) and thereby reducing overall efficiency.

- Optimal r1:
  There's a trade-off. The maximum efficiency is achieved when r1 is chosen to balance the likelihood of collisions against the wastage from too many empty slots.
  For N=4 tags, the calculated results show that the maximum efficiency occurs at r1=4. This aligns with the common heuristic in ALOHA-based systems that setting the frame size close to the estimated number of contending tags often optimizes performance (e.g., throughput or, in this case, slot utilization efficiency for full resolution). At r1=4, there's a reasonable chance for many tags to find unique slots, reducing the work for subsequent frames without excessive initial slot wastage. The efficiency drops for r1=5 and r1=6 because the cost of the initial frame (5 or 6 slots) starts to outweigh the benefit of slightly fewer initial collisions for the N=4 tags.
"""
print(comment_text)
