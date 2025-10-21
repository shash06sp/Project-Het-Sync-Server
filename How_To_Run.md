# How to Build and Run Project Het-Sync

This guide provides step-by-step instructions on how to compile the C++ server and run the manual demonstrations for both the main Het-Sync server and the eBPF kernel profiler.

---
## 1. Prerequisites

Before you begin, ensure your Ubuntu environment has all necessary tools installed.

#### System Tools
Open a terminal and install the C++ compiler (`g++`), `make`, and the `bpfcc-tools` for eBPF.
```bash
sudo apt-get update
sudo apt-get install -y build-essential make bpfcc-tools python3-bpfcc linux-headers-$(uname -r)
```

#### Python Libraries
Install the required Python packages using `pip`.
```bash
pip install numpy matplotlib pandas
```

---
## 2. Build the C++ Server

The provided `Makefile` automates the compilation process.

1.  Open a terminal in the main project directory.
2.  Compile the code by running the `make` command.
    ```bash
    make
    ```
    This will create a single executable file named `server`.

---
## 3. How to Run the Het-Sync Demo (5 Terminals)

This experiment uses five terminals to demonstrate the "straggler problem" and your solution.

### Experiment A: Proving the Naive Server Fails (Gets Stuck) 🐢

1.  **Terminal 1 (Server):** Start the server in **naive mode**.
    ```bash
    ./server naive
    ```

2.  **Terminals 2, 3, & 4 (Fast Workers):** In each of these three terminals, start a fast worker.
    ```bash
    python3 worker.py
    ```

3.  **Terminal 5 (The Straggler):** Start the slow worker.
    ```bash
    python3 straggler.py
    ```

4.  **Observe:** The server in Terminal 1 will get stuck waiting and will **never** print a "Broadcasted..." message. This is the **successful outcome** of this test, proving the naive approach fails.
5.  **Clean Up:** Press `Ctrl+C` in all five terminals.

### Experiment B: Proving the Het-Sync Server Succeeds (Times Out) 🚀

1.  **Clean Up:** Run `pkill -f ./server && pkill -f python3`
2.  **Terminal 1 (Server):** Start the server in **smart mode**.
    ```bash
    ./server
    ```

3.  **Terminals 2, 3, & 4 (Fast Workers):** Start three fast workers.
    ```bash
    python3 worker.py
    ```

4.  **Terminal 5 (The Straggler):** Start the slow worker.
    ```bash
    python3 straggler.py
    ```
5.  **Observe:** The server in Terminal 1 will print **`TIMEOUT!`** after ~2 seconds and then **`SERVER: Broadcasted new model...`**. This is the **successful outcome**, proving your solution works.
6.  **Clean Up:** Press `Ctrl+C` in all terminals.

---
## 4. How to Run the eBPF Profiler

This is a two-stage process: first, you collect the raw performance data, and second, you analyze that data to produce the statistical summary and histogram.

### Stage A: Collect Latency Data (3 Terminals)

1.  **Terminal 1 (The Profiler):** Start the eBPF latency script with `sudo`. It will create `latency_data.csv` and start recording.
    ```bash
    sudo python3 tcp_latency.py
    ```
    *Let this run for about 15-20 seconds to collect a good sample of data.*

2.  **Terminal 2 (The Server):** While the profiler is running, start your C++ server in the background.
    ```bash
    ./server &
    ```

3.  **Terminal 3 (The Workload):** Start a Python worker to generate traffic.
    ```bash
    python3 worker.py
    ```

4.  **Stop Collection:** After 15-20 seconds, go to **Terminal 1** and press `Ctrl+C` to stop the profiler.
5.  **Clean Up:** Stop the other processes with `pkill -f ./server && pkill -f python3`.

### Stage B: Analyze Data and Generate Graph (1 Terminal)

1.  **Run Analysis:** Now that you have the `latency_data.csv` file, run the analysis script.
    ```bash
    python3 analyze_latency.py
    ```
2.  **Observe the Result:** The script will print a statistical summary (mean, median, etc.) to your terminal.
3.  **View the Graph:** The script will also create the final histogram image named `latency_histogram.png`. Open this file to see your final statistical result.
