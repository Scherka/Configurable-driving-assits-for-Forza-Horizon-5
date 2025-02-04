import socket
import struct
from multiprocessing import Queue


def udp_listener(telemetry_queue, acceleration_queue, PORT):
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("UDP socket created")
    try:
        # Configuration
        HOST = "127.0.0.1"  # Listen on localhost
        udp_socket.bind((HOST, PORT))
        print(f"Listening for UDP packets on {HOST}:{PORT}...")
        while True:
            # Receive data from the socket
            data, addr = udp_socket.recvfrom(1024)  # Buffer size is 1024 bytes
            default_format = '<iI27f4i20f5ii19fH6B4b'  # Unpack the data using the specified data format
            unpacked = struct.unpack(default_format, data)
            # Extract the relevant values
            telemetry_data = {
                "TireCombinedSlipFrontLeft":  unpacked[45] * 100,
                "TireCombinedSlipFrontRight":  unpacked[46] * 100,
                "TireCombinedSlipRearLeft":  unpacked[47] * 100,
                "TireCombinedSlipRearRight":  unpacked[48] * 100,
                "DriveTrainType":  unpacked[56],
                "Gear": unpacked[84],
                "Speed": unpacked[64]}
            # Send data to the queue if the game is not paused
            if unpacked[0] == 1:
                telemetry_queue.put((telemetry_data, 'data')) # Data for the input adjustment
                acceleration_queue.put(unpacked[64]) # Data for the acceleration time calculator


    except KeyboardInterrupt:
        print("\nStopping the server.")
    except Exception as e:
        print(f"An error occurred: {e}")
        telemetry_queue.put((str(e), 'error'))
    finally:
        udp_socket.close()