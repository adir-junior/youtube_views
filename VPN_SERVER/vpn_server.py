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
geo_ip_list = {
    'US': ['192.168.1.10', '192.168.1.11'],
    'UK': ['192.168.2.10', '192.168.2.11'],
    'BR': ['192.168.3.10', '192.168.3.11']
}


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

def assign_ip_based_on_location(location: str) -> str:
    """
    Assigns an IP address based on the desired geographical location.

    Args:
        location (str): The geographical location for the IP assignment.

    Returns:
        str: The assigned IP address.
    """
    if location in geo_ip_list and geo_ip_list[location]:
        ip = geo_ip_list[location].pop(0)  # Get the first IP from the list
        allocated_ips.add(ip)  # Add it to allocated IPs to avoid duplicates
        return ip
    else:
        return generate_random_ip()  # Fallback to random IP if not found

def enable_ip_forwarding() -> None:
    """
    Enables IP forwarding on Linux and macOS.
    """
    if platform.system() == 'Linux':
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
        logging.info("IP forwarding enabled on Linux.")
    elif platform.system() == 'Darwin':  # macOS
        subprocess.run(['sysctl', '-w', 'net.inet.ip.forwarding=1'], check=True)
        logging.info("IP forwarding enabled on macOS.")
    else:
        logging.error("OS doesn't support enabling IP forwarding.")

def handle_client(newsocket: socket.socket, fromaddr: tuple[str, int], location: str) -> None:
    """
    Handles a client connection by securing it with SSL, assigning a virtual IP,
    and enabling IP forwarding and NAT.
    """
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    try:
        conn = context.wrap_socket(newsocket, server_side=True)
        virtual_ip = assign_ip_based_on_location(location)  # Use location for IP assignment
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

        # Aqui você pode definir a localização desejada (por exemplo, 'US', 'UK', 'BR').
        location = 'US'  # Defina a localização conforme necessário
        client_thread = threading.Thread(target=handle_client, args=(newsocket, fromaddr, location))
        client_thread.start()

if __name__ == "__main__":
    enable_ip_forwarding()  
    start_vpn_server('127.0.0.1', 8443)
