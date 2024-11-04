import time
import socket
import ssl
import random
import threading
import logging
import subprocess
import platform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

allocated_ips = set()

def generate_random_ip() -> str:
    """
    Generates a random IP address and adds it to the allocated_ips set.

    Returns:
        str: The generated random IP address.
    """

    while True:
        new_ip = f'192.168.{random.randint(2, 254)}.{random.randint(2, 254)}'
        if new_ip not in allocated_ips:
            allocated_ips.add(new_ip)
            return new_ip

def enable_ip_forwarding() -> None:
    """
    Enables IP forwarding on Linux and macOS.

    IP forwarding allows the VPN server to forward traffic between the VPN
    interface and the physical network interface. This is required for the VPN
    server to work.

    This function has no parameters and returns no value.

    On Linux, this function writes 1 to the /proc/sys/net/ipv4/ip_forward file.
    On macOS, this function uses the sysctl command to set the net.inet.ip.forwarding
    variable to 1. If the operating system is not Linux or macOS, a log error
    message is printed.

    Returns:
        None
    """

    if platform.system() == 'Linux':
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
        logging.info("IP forwarding habilited on Linux.")

    elif platform.system() == 'Darwin':  # macOS
        subprocess.run(['sysctl', '-w', 'net.inet.ip.forwarding=1'], check=True)
        logging.info("IP forwarding habilited on macOS.")
        
    else:
        logging.error("OS don`t support to enable IP forwarding.")

def setup_iptables() -> None:
    """
    Configure IPTables to enable packet forwarding from the VPN interface to
    the physical network interface (eth0).

    This function has no parameters and returns no value.

    The specific command run is:
        iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

    This command allows the VPN server to forward packets between the VPN
    interface and the physical network interface, allowing the client to access
    the network.

    Returns:
        None
    """
    subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', 'eth0', '-j', 'MASQUERADE'], check=True)


    logging.info("IpTables configuration done.")

def handle_client(newsocket: socket.socket, fromaddr: tuple[str, int]) -> None:
    """
    Handles a client connection by securing it with SSL, assigning a virtual IP,
    and enabling IP forwarding and NAT.

    Args:
        newsocket(socket): The socket object for the client connection.
        fromaddr(tuple): The address of the client.

    The function creates an SSL context, wraps the client socket, assigns a virtual 
    IP to the client, and configures IP forwarding and IPTables for packet forwarding.
    It sends the assigned virtual IP to the client and logs the received data. In 
    case of any error, it logs the error message and ensures the connection is 
    properly closed.

    Returns:
        None
    """

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    
    try:
        conn = context.wrap_socket(newsocket, server_side=True)
        virtual_ip = generate_random_ip()
        logging.info(f"Assigned virtual IP {virtual_ip} to client {fromaddr}")

        setup_iptables() 

        time.sleep(0.5)

        logging.info(f"Sending virtual IP {virtual_ip} to client {fromaddr}")
        conn.sendall(virtual_ip.encode())
        
        data = conn.recv(1024)
        logging.info(f"Received: {data}")

    except Exception as e:
        logging.error(f"Error with client {fromaddr}: {e}")

    finally:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()

def start_vpn_server(host: str, port: int) -> None:
    """
    Starts a VPN server on the specified host and port.

    This function creates an SSL context and binds a socket to the specified host
    and port. It then listens for incoming connections and, for each connection,
    creates a new thread to handle the client.

    The function has no return value and runs indefinitely.

    Args:
        host(str): The host on which the VPN server should listen.
        port(int): The port on which the VPN server should listen.

    Returns:
        None
    """

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    bindsocket = socket.socket()
    bindsocket.bind((host, port))
    bindsocket.listen(5)

    logging.info(f"VPN server listening on {host}:{port}")

    while True:
        newsocket, fromaddr = bindsocket.accept()
        logging.info(f"Connection from {fromaddr}")
        client_thread = threading.Thread(target=handle_client, args=(newsocket, fromaddr))
        client_thread.start()

if __name__ == "__main__":
    enable_ip_forwarding()  
    start_vpn_server('127.0.0.1', 8443)


#temos que abri o powershell como administrador   
# #usar este codigo  --> Set-Location -Path F:\youtube-gabriel\youtube_views\VPN_SERVER && python3 .\vpn_server.py