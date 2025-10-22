#!/usr/bin/python3
from bcc import BPF
import time

bpf_text = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>

BPF_HASH(start, u32);

struct data_t {
    u32 pid;
    u64 delta_ns;
    char comm[TASK_COMM_LEN];
};

BPF_PERF_OUTPUT(events);

int trace_tcp_sendmsg_entry(struct pt_regs *ctx) {
    u64 ts = bpf_ktime_get_ns();
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    start.update(&pid, &ts);
    return 0;
}

int trace_tcp_sendmsg_return(struct pt_regs *ctx) {
    u64 *tsp, delta;
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    tsp = start.lookup(&pid);
    if (tsp != 0) {
        delta = bpf_ktime_get_ns() - *tsp;
        struct data_t data = {};
        data.pid = pid;
        data.delta_ns = delta;
        bpf_get_current_comm(&data.comm, sizeof(data.comm));
        events.perf_submit(ctx, &data, sizeof(data));
        start.delete(&pid);
    }
    return 0;
}
"""

b = BPF(text=bpf_text)
b.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg_entry")
b.attach_kretprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg_return")

print("Profiling TCP send latency... Saving to latency_data.csv. Press Ctrl+C to end.")

# Open a file to save the data
with open("latency_data.csv", "w") as f:
    f.write("comm,pid,latency_ns\n") # Write header
    
    # Function to save the data
    def save_event(cpu, data, size):
        event = b["events"].event(data)
        f.write(f"{event.comm.decode()},{event.pid},{event.delta_ns}\n")

    b["events"].open_perf_buffer(save_event)
    try:
        while True:
            b.perf_buffer_poll()
    except KeyboardInterrupt:
        print("\nDetaching...")
        exit()