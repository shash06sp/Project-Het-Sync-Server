import socket
import struct
import numpy as np
import time 

# Server configuration
HOST = 'localhost'
PORT = 9999

def main():
    # Create and connect the socket ONCE.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        print("Worker: Connected to server.")

        for i in range(5):
            # Create a new fake gradient for each message
            gradient = np.ones(10, dtype=np.float32) * (i + 1)
            print(f"Worker: Created fake gradient of {gradient.nbytes} bytes for message #{i+1}.")

            # Get the size of the payload and pack the header
            payload_size = gradient.nbytes
            header = struct.pack('>Q', payload_size)

            # Send the header, then the payload
            print(f"Worker: Sending header for message #{i+1}...")
            sock.sendall(header)

            print(f"Worker: Sending payload for message #{i+1}...")
            sock.sendall(gradient.tobytes())
            print(f"Worker: Waiting to recieve aggregated model...")
            header_data = sock.recv(8)
            if not header_data:
                print("Worker: Server Disconnected. ")
                break
            payload_size = struct.unpack('>Q', header_data) [0]
            aggregated_gradient_bytes = sock.recv(payload_size)
            aggregated_gradient_= np.frombuffer(aggregated_gradient_bytes, dtype=np.float32)
            print(f"Worker: Received new model. First value is: {aggregated_gradient_[0]}")

            # Wait for a second to simulate work
            time.sleep(0.1)
        # ==========================================================

        print("Worker: Finished sending all gradients.")

if __name__ == '__main__':
    main()