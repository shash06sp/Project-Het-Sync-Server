#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <mutex>
#include <chrono>
#include <algorithm>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sys/epoll.h>
#include <fcntl.h>
#include <cerrno>
#include <cstring>
#include <cstdio>
#include <fstream>

// --- Configuration ---
#define PORT 9999
#define MAX_EVENTS 10
#define NUM_WORKERS 4
#define TIMEOUT_MS 2000

// --- Global Shared State ---
std::vector<float> global_model(10, 0.0f);
std::mutex model_mutex;
int gradients_received_count = 0;
std::vector<int> participating_workers;
bool round_in_progress = false;
std::chrono::steady_clock::time_point round_start_time;

// --- Client State Management ---
struct ClientState
{
    uint64_t payload_size = 0;
    std::vector<char> buffer;
    bool reading_header = true;
};
std::map<int, ClientState> client_states;

void broadcast_model()
{
    std::vector<char> payload_buffer(global_model.size() * sizeof(float));
    memcpy(payload_buffer.data(), global_model.data(), payload_buffer.size());
    uint64_t payload_size_net = htobe64(payload_buffer.size());
    for (int worker_fd : participating_workers)
    {
        write(worker_fd, &payload_size_net, sizeof(uint64_t));
        write(worker_fd, payload_buffer.data(), payload_buffer.size());
    }
    std::cout << "SERVER: Broadcasted new model to " << participating_workers.size() << " workers." << std::endl;
}

void handle_client_data(int client_fd)
{
    ClientState &state = client_states.at(client_fd);
    while (true)
    {
        if (state.reading_header)
        {
            size_t bytes_to_read = 8 - state.buffer.size();
            std::vector<char> temp_buffer(bytes_to_read);
            ssize_t bytes_read = read(client_fd, temp_buffer.data(), bytes_to_read);
            if (bytes_read <= 0)
            {
                if (bytes_read < 0 && (errno == EAGAIN || errno == EWOULDBLOCK))
                {
                    break;
                }
                {
                    std::lock_guard<std::mutex> lock(model_mutex);
                    participating_workers.erase(std::remove(participating_workers.begin(), participating_workers.end(), client_fd), participating_workers.end());
                }
                close(client_fd);
                client_states.erase(client_fd);
                return;
            }
            state.buffer.insert(state.buffer.end(), temp_buffer.begin(), temp_buffer.begin() + bytes_read);
            if (state.buffer.size() == 8)
            {
                memcpy(&state.payload_size, state.buffer.data(), sizeof(uint64_t));
                state.payload_size = be64toh(state.payload_size);
                state.buffer.clear();
                state.reading_header = false;
            }
        }
        else
        {
            size_t bytes_to_read = state.payload_size - state.buffer.size();
            std::vector<char> temp_buffer(bytes_to_read);
            ssize_t bytes_read = read(client_fd, temp_buffer.data(), bytes_to_read);
            if (bytes_read <= 0)
            {
                if (bytes_read < 0 && (errno == EAGAIN || errno == EWOULDBLOCK))
                {
                    break;
                }
                {
                    std::lock_guard<std::mutex> lock(model_mutex);
                    participating_workers.erase(std::remove(participating_workers.begin(), participating_workers.end(), client_fd), participating_workers.end());
                }
                close(client_fd);
                client_states.erase(client_fd);
                return;
            }
            state.buffer.insert(state.buffer.end(), temp_buffer.begin(), temp_buffer.begin() + bytes_read);
            if (state.buffer.size() == state.payload_size)
            {
                std::vector<float> received_gradient(state.payload_size / sizeof(float));
                memcpy(received_gradient.data(), state.buffer.data(), state.payload_size);
                {
                    std::lock_guard<std::mutex> lock(model_mutex);
                    if (!round_in_progress && gradients_received_count == 0)
                    {
                        round_in_progress = true;
                        round_start_time = std::chrono::steady_clock::now();
                        std::cout << "SERVER: First gradient received. Round timer started." << std::endl;
                    }
                    for (size_t i = 0; i < global_model.size(); ++i)
                    {
                        global_model[i] += received_gradient[i];
                    }
                    gradients_received_count++;
                    std::cout << "SERVER: Aggregated gradient. Count is now " << gradients_received_count << "/" << NUM_WORKERS << std::endl;
                    if (gradients_received_count == NUM_WORKERS)
                    {
                        std::cout << "SERVER: Synchronization barrier reached! Broadcasting new model." << std::endl;
                        broadcast_model();
                        std::fill(global_model.begin(), global_model.end(), 0.0f);
                        gradients_received_count = 0;
                        round_in_progress = false;
                    }
                }
                state.buffer.clear();
                state.reading_header = true;
            }
        }
    }
}

int main(int argc, char *argv[])
{
    bool is_naive_mode = (argc > 1 && std::string(argv[1]) == "naive");
    int timeout_value = is_naive_mode ? -1 : TIMEOUT_MS;
    if (is_naive_mode)
    {
        std::cout << "--- RUNNING NAIVE SERVER MODE (INFINITE TIMEOUT) ---" << std::endl;
    }
    else
    {
        std::cout << "--- RUNNING HET-SYNC MODE (2s TIMEOUT) ---" << std::endl;
    }
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    bind(server_fd, (struct sockaddr *)&address, sizeof(address));
    listen(server_fd, 10);
    int epoll_fd = epoll_create1(0);
    struct epoll_event event;
    event.events = EPOLLIN;
    event.data.fd = server_fd;
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, server_fd, &event);
    struct epoll_event events[MAX_EVENTS];
    while (true)
    {
        int num_events = epoll_wait(epoll_fd, events, MAX_EVENTS, timeout_value);
        for (int i = 0; i < num_events; ++i)
        {
            if (events[i].data.fd == server_fd)
            {
                int new_socket = accept(server_fd, nullptr, nullptr);
                int flags = fcntl(new_socket, F_GETFL, 0);
                fcntl(new_socket, F_SETFL, flags | O_NONBLOCK);
                event.events = EPOLLIN;
                event.data.fd = new_socket;
                epoll_ctl(epoll_fd, EPOLL_CTL_ADD, new_socket, &event);
                client_states[new_socket] = ClientState();
                {
                    std::lock_guard<std::mutex> lock(model_mutex);
                    participating_workers.push_back(new_socket);
                }
            }
            else
            {
                handle_client_data(events[i].data.fd);
            }
        }
        if (num_events == 0 && !is_naive_mode)
        {
            if (round_in_progress)
            {
                auto elapsed = std::chrono::steady_clock::now() - round_start_time;
                if (std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count() >= TIMEOUT_MS)
                {
                    std::lock_guard<std::mutex> lock(model_mutex);
                    std::cout << "SERVER: TIMEOUT! Broadcasting with " << gradients_received_count << " gradients." << std::endl;
                    broadcast_model();
                    std::fill(global_model.begin(), global_model.end(), 0.0f);
                    gradients_received_count = 0;
                    round_in_progress = false;
                }
            }
        }
    }
    return 0;
}