#!/usr/bin/python3
from bcc import BPF

# 1. The C program that will be loaded into the kernel
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>

// The data structure to hold event information
struct data_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
};

// The communication channel to send data from kernel to user-space
BPF_PERF_OUTPUT(events);

// The function that runs when the kernel's tcp_sendmsg is called
int trace_tcp_sendmsg(struct pt_regs *ctx) {
    struct data_t data = {};
    
    // Get the process ID and command name
    data.pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    
    // Send the data to the user-space program
    events.perf_submit(ctx, &data, sizeof(data));
    
    return 0;
}
"""

# 2. The Python program that controls everything
try:
    # Compile the C program and load it into the kernel
    b = BPF(text=bpf_text)

    # Attach our C function to the kernel's tcp_sendmsg function
    b.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg")

    print("Tracing TCP send operations... Press Ctrl+C to end.")

    # Function to print the data received from the kernel
    def print_event(cpu, data, size):
        event = b["events"].event(data)
        print(f"PID: {event.pid:<10} COMM: {event.comm.decode():<16} Sent TCP data")

    # Open the communication channel and start polling for data
    b["events"].open_perf_buffer(print_event)
    while True:
        b.perf_buffer_poll()

except KeyboardInterrupt:
    print("Detaching...")
    exit()