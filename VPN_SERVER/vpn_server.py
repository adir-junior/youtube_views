import os
import socket
import ssl
import random
import threading
import logging
import subprocess
import platform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

allocated_ips = set()

def generate_random_ip():
    """Gera um endereço IP aleatório na faixa 10.0.0.0/24."""
    while True:
        new_ip = f'10.0.0.{random.randint(2, 254)}'
        if new_ip not in allocated_ips:
            allocated_ips.add(new_ip)
            return new_ip

def check_root():
    """Verifica se o script está sendo executado como root."""
    if os.getpid() != 0:
        logging.error("Este script deve ser executado como root.")
        exit(1)

def enable_ip_forwarding():
    """Habilita o IP forwarding dependendo do sistema operacional."""
    if platform.system() == 'Linux':
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
        logging.info("IP forwarding habilitado no Linux.")
    elif platform.system() == 'Darwin':  # macOS
        subprocess.run(['sysctl', '-w', 'net.inet.ip.forwarding=1'], check=True)
        logging.info("IP forwarding habilitado no macOS.")
    else:
        logging.error("Sistema operacional não suportado para habilitar IP forwarding.")

def setup_iptables():
    """Configura IPTables para permitir NAT em Linux."""
    subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', 'eth0', '-j', 'MASQUERADE'], check=True)
    logging.info("Configuração do IPTables realizada.")

def handle_client(newsocket, fromaddr):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    
    try:
        conn = context.wrap_socket(newsocket, server_side=True)
        virtual_ip = generate_random_ip()
        logging.info(f"Assigned virtual IP {virtual_ip} to client {fromaddr}")

        # Configure IP forwarding and IPTables
        setup_iptables()  # Chame para configurar o NAT
        conn.sendall(virtual_ip.encode())
        
        data = conn.recv(1024)
        logging.info(f"Received: {data}")

    except Exception as e:
        logging.error(f"Error with client {fromaddr}: {e}")

    finally:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()

def start_vpn_server(host, port):
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
    #check_root()  # Verifica se o script está sendo executado como root
    enable_ip_forwarding()  # Habilite o IP forwarding no início
    start_vpn_server('127.0.0.1', 8443) 
