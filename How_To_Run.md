# How to Build and Run Project Het-Sync

This guide provides step-by-step instructions on how to compile the C++ server and run the manual experiments to demonstrate the core functionality of the latency-aware policy.

---

## 1. Prerequisites

Before you begin, ensure your Ubuntu environment has the necessary tools installed.

#### System Tools

Open a terminal and install the C++ compiler (`g++`), `make`, and `bc` for calculations.

```bash
sudo apt-get update
sudo apt-get install build-essential make bc
```

#### Python Libraries

Install the required Python packages (`numpy` and `matplotlib`) using `pip`.

```bash
pip install numpy matplotlib
```

---

## 2. Build the C++ Server

The provided `Makefile` automates the compilation process.

1.  Open a terminal in the main project directory (where `Makefile` and `server.cpp` are located).
2.  Compile the code by running the `make` command.
    ```bash
    make
    ```
    This will create a single executable file named `server` in your directory.

---

## 3. Run the Manual Experiments

These two experiments are the definitive proof of the project. You will need **five separate terminal windows** to run them.

### Experiment 1: Proving the Naive Server Fails (Gets Stuck)

This test demonstrates the "straggler problem" that the project is designed to solve.

- **Terminal 1 (The Server):** Start the server in **naive mode**. It is designed to wait forever for all workers.

  ```bash
  ./server naive
  ```

  _You will see the output: `--- RUNNING NAIVE SERVER MODE (INFINITE TIMEOUT) ---`._

- **Terminals 2, 3, & 4 (The Fast Workers):** In each of these three separate terminals, start a fast worker.

  ```bash
  python3 worker.py
  ```

- **Terminal 5 (The Straggler):** In this terminal, start the slow worker.

  ```bash
  python3 straggler.py
  ```

- **Observe the Result:** Watch **Terminal 1**. The server will log that it received three gradients and then it will **get stuck**. It will never print a `"Broadcasted..."` message because it is waiting indefinitely for the straggler. This is the **successful outcome** of this test, as it proves the naive approach fails.

- **Clean Up:** Press `Ctrl+C` in all five terminals to stop the processes before moving to the next experiment.

### Experiment 2: Proving Your Het-Sync Server Succeeds (Times Out)

This test demonstrates your solution in action.

- **Clean Up (Just in case):** In any terminal, run this command to ensure no old processes are running.

  ```bash
  pkill -f ./server && pkill -f python3
  ```

- **Terminal 1 (The Server):** Start your server in **smart mode** (the default).

  ```bash
  ./server
  ```

  _You will see the output: `--- RUNNING HET-SYNC MODE (2s TIMEOUT) ---`._

- **Terminals 2, 3, & 4 (The Fast Workers):** In each of these three terminals, start a fast worker.

  ```bash
  python3 worker.py
  ```

- **Terminal 5 (The Straggler):** In this terminal, start the slow worker.

  ```bash
  python3 straggler.py
  ```

- **Observe the Result:** Watch **Terminal 1**. The server will receive three gradients, wait about **2 seconds**, and then correctly print a **`TIMEOUT!`** message, followed by a **`SERVER: Broadcasted new model...`** message. This cycle will repeat. This is the **successful outcome** of the test, proving your server does not get stuck.

- **Clean Up:** Press `Ctrl+C` in all terminals to stop the processes.
