# Project Het-Sync: A Latency-Aware Parameter Server

![C++](https://img.shields.io/badge/C%2B%2B-17-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Linux API](https://img.shields.io/badge/Linux%20API-epoll%2C%20sockets-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

This is the source code repository for Project Het-Sync, an ultra-high-performance non-blocking TCP server written in C++ to simulate a parameter server for distributed machine learning. Its innovative aspect is a timeout-based latency-aware aggregation policy to overcome the performance cost of "straggler" nodes on heterogeneous networks.

This project showcases an end-to-end systems design and analysis workflow: creating from ground up a complex network service utilizing low-level Linux APIs, creating a proprietary communication protocol, building a benchmarking set, and conducting a quantitative analysis to demonstrate the efficacy of the system.

![Performance Graph](Performance_Graph.png)
_(Final benchmark results demonstrating the success of the Het-Sync server.)_

---

## Summary of Content

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Key Differentiators](#3-key-differentiators)
4. [Solution Approach](#4-solution-approach)
5. [Architecture and Core Components](#5-architecture-and-core-components)
6. [Quantitative Results and Analysis](#6-quantitative-results-and-analysis)
7. [Technical Stack](#7-technical-stack)
8. [Setup & Usage](#8-setup--usage)
9. [Future Work](#9-future-work)

---

## 1. Project Overview

As the size of the machine learning models grows, the learning process is increasingly parallelized on collections of computers. One key bottleneck in this process is synchronization: all the "worker" machines must regularly combine their updates with the central "parameter server." The performance of this combination directly limits the end-to-end training speed.

Project Het-Sync solves the problem related to synchronization bottlenecks. It provides an implementation on C++ of a parameter server tolerant to "straggler" nodes—slow workers potentially caused by network congestion or hardware heterogeneity. The server makes rational choices about the timing of the steps of the training and thus ensures the pace of the overall high-performance cluster is not held up by a minority of slower workers.

## 2. Problem Statement

The particular issue at hand is the **Straggler Bottleneck in Synchronous Parallel Distributed Training**. A naive implementation of the parameter server uses a rigid synchronous barrier that results in waiting forever on the slow worker on each iteration. That means the drastic decline in throughput because cost-prohibitive high-performance nodes sit idle.

The model is to optimize this idle time and system throughput (updates per second) maximization subject to:

- **Concurrency:** The server must handle connections from numerous workers simultaneously.
- **Network Heterogeneity:** The system must remain performant even when some workers have high latency.
- **Correctness:** The server must safely aggregate data from multiple concurrent sources without race conditions.

## 3. Key Differentiators

In contrast to high-level implementations that depend on pre-existing frameworks, Project Het-Sync is developed from the foundational level to illustrate a fundamental comprehension of systems programming. The primary benefits associated with this project include:

- **Low-Level C++ Implementation:** The server is written entirely in C++17 using fundamental Linux APIs, showcasing the ability to build high-performance services without relying on third-party networking libraries.

- **High-Performance Non-Blocking Architecture:** The server is built on a single-threaded, event-driven architecture using the `epoll` API. This allows it to manage thousands of concurrent connections with minimal resource overhead, avoiding the scalability limitations of a simpler thread-per-client model.

- **Latency-Aware Policy:** The core innovation is the timeout-based synchronization barrier. The server does not wait indefinitely for all workers. It intelligently proceeds with the data it has if a round takes too long, ensuring system-wide progress is never halted by a single straggler.

## 4. Solution Approach

The fundamental resolution involves dismantling the rigid synchronous dependence. Rather than awaiting an indefinite period for the complete participation of all workers, the server implements a **latency-aware, timeout-based synchronization barrier.**

The server's policy is as follows:

1.  When the first gradient for a new training round arrives, a countdown timer is started.
2.  The server will then wait for one of two conditions to be met, whichever comes first:
    a. All expected workers submit their gradients.
    b. The timer expires.
3.  Upon either condition, the server immediately aggregates whatever gradients it has received and broadcasts the updated model back to the participating workers.

This ensures that system-wide progress is never halted by a single slow or unresponsive node, trading the contribution of the straggler for a massive gain in overall system throughput and robustness.

## 5. Architecture and Core Components

1.  **C++ `epoll` Server (`server.cpp`):** A unified executable that can run in two modes ("smart" and "naive") for benchmarking. It manages all client connections, state, and the core aggregation logic in a non-blocking event loop.
2.  **Custom Wire Protocol:** A simple but robust length-prefix wire protocol (8-byte header specifying payload length) is used for communication between the C++ server and Python workers.
3.  **Python Workers (`worker.py`, `straggler.py`):** Lightweight Python clients that simulate the behavior of workers in a distributed training job.
4.  **Python Benchmarking Suite (`plot_results.py`):** A script to generate the final performance graph.

## 6. Quantitative Results and Analysis

The effectiveness of the Het-Sync server was demonstrated by comparing it to a naive synchronous server that waits forever for all workers.

![Performance Graph](finalResults.png)

### Performance Comparison Table

| % of Stragglers | Naive Server Throughput (updates/sec) | Het-Sync Server Throughput (updates/sec) |
| :-------------- | :------------------------------------ | :--------------------------------------- |
| 0%              | 4.9                                   | 4.8                                      |
| 25%             | **0.0**                               | 4.5                                      |
| 50%             | **0.0**                               | 4.6                                      |
| 75%             | **0.0**                               | 4.3                                      |

### Analysis

The results are conclusive. The graph and table clearly show that the **Naive Server's throughput collapses to zero** in the presence of even a single straggler. In contrast, the **Het-Sync server's throughput remains high and stable**, proving that its latency-aware policy successfully mitigates the straggler problem. This demonstrates a clear and dramatic improvement in system robustness and performance.

---

## 7. Technical Stack

- **Core Logic:** C++17
- **Linux APIs:** `epoll`, Berkeley Sockets (`socket`, `bind`, `listen`, `accept`), `fcntl`
- **Concurrency:** `std::mutex` for thread-safe aggregation
- **Benchmarking & Visualization:** Python 3.10+, NumPy, Matplotlib
- **Build System:** `make`

---

## 8. Setup & Usage

1.  Clone the repository.
2.  Ensure you have the necessary dependencies: `g++`, `make`, `python3-pip`.
3.  Install Python libraries: `pip install numpy matplotlib`.
4.  Build the C++ server:
    ```bash
    make
    ```
5.  To run the full manual demonstration showing the timeout in action, use five separate terminals as described in the "How_T0_Run" file instructions.

---

## 9. Future Work

- **Adaptive Timeouts:** The current timeout is static. A more advanced implementation could dynamically adjust the timeout based on the historical latency statistics of the workers.
- **Stale Gradients:** Instead of completely ignoring a straggler's gradient, the server could incorporate "stale gradients" from previous rounds, weighting them less.
- **Efficient Serialization:** The current implementation uses raw byte transfers. Using a dedicated serialization library like Google Protocol Buffers would create a more robust and extensible wire protocol.
