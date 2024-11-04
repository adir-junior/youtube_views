import socket
import ssl

def vpn_client(host: str, port: int) -> None:
    """
    Tests connection to the VPN server.

    This function is used solely for testing the connection to the VPN server. It
    creates a secure connection to the server, sends a "Hello, VPN Server!" message,
    and prints the received response.

    Parameters:
        host (str): The hostname or IP address of the VPN server.
        port (int): The port number on which the VPN server is listening.
    """
    
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations("server.crt")

    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.connect((host, port))
    conn = context.wrap_socket(raw_socket, server_hostname=host)

    try:
        conn.send(b"Hello, VPN Server!")
        data = conn.recv(1024)
        print(f"Received from server: {data}")
    finally:
        conn.close()

if __name__ == "__main__":
    vpn_client('127.0.0.1', 8443)