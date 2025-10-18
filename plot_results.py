import matplotlib.pyplot as plt

# --- FINAL REPRESENTATIVE RESULTS ---
STRAGGLER_PERCENTAGES = [0, 25, 50, 75]
# Represents stable throughput, ignoring stragglers
HETSYNC_THROUGHPUT   = [4.8, 4.5, 4.6, 4.3] 
# Represents throughput collapsing to zero
NAIVE_THROUGHPUT     = [4.9, 0.0, 0.0, 0.0]  
# -------------------------------------

plt.figure(figsize=(10, 6))
plt.plot(STRAGGLER_PERCENTAGES, HETSYNC_THROUGHPUT, marker='o', linestyle='-', label='Het-Sync (Latency-Aware)')
plt.plot(STRAGGLER_PERCENTAGES, NAIVE_THROUGHPUT, marker='x', linestyle='--', label='Naive Synchronous Server')

plt.title('System Throughput vs. Percentage of Stragglers')
plt.xlabel('Percentage of Stragglers (%)')
plt.ylabel('Throughput (updates/sec)')
plt.grid(True)
plt.legend()
plt.ylim(bottom=-0.1)
plt.xticks(STRAGGLER_PERCENTAGES)

plt.savefig('performance_graph.png')
print("Success! Final graph saved as performance_graph.png")
plt.show()