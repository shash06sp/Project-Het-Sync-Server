import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 1. Load the collected data ---
try:
    df = pd.read_csv("latency_data.csv")
except FileNotFoundError:
    print("Error: latency_data.csv not found. Please run tcp_latency.py first to collect data.")
    exit()

# --- 2. Filter and prepare the data ---
# Filter for just the server and worker processes and convert latency to microseconds
server_latencies = df[df['comm'] == 'server']['latency_ns'] / 1000
worker_latencies = df[df['comm'] == 'python3']['latency_ns'] / 1000

# --- 3. Calculate and print the ground-truth statistics ---
print("--- Latency Statistics (microseconds) ---")
print("\nServer (C++):")
print(server_latencies.describe())
print("\nWorkers (Python):")
print(worker_latencies.describe())

# --- 4. Create an accurate and clear histogram using subplots ---

# Create a figure with two vertically stacked subplots that share the same x-axis
fig, axs = plt.subplots(
    nrows=2, 
    ncols=1, 
    figsize=(12, 10), 
    sharex=True 
)

# A main title for the entire figure
fig.suptitle('Distribution of Kernel TCP Send Latency', fontsize=16)

# Plot Server (C++) data on the top subplot (axs[0])
axs[0].hist(server_latencies, bins=30, color='tab:blue', alpha=0.8, label='Server (C++)')
axs[0].set_title('Server (C++) Latency')
axs[0].set_ylabel('Frequency')
axs[0].legend()
axs[0].grid(True)

# Plot Worker (Python) data on the bottom subplot (axs[1])
axs[1].hist(worker_latencies, bins=30, color='tab:orange', alpha=0.8, label='Worker (Python)')
axs[1].set_title('Worker (Python) Latency')
axs[1].set_ylabel('Frequency')
axs[1].set_xlabel('Latency (microseconds)') # X-axis label only on the bottom plot
axs[1].legend()
axs[1].grid(True)

# Adjust layout to prevent titles and labels from overlapping
plt.tight_layout(rect=[0, 0.03, 1, 0.96]) # Adjust rect to make space for suptitle

# --- 5. Save the figure ---
plt.savefig('latency_histogram.png')

print("\nSuccess! Latency histogram saved as latency_histogram.png")