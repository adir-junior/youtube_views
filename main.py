import socket
import random
import ssl
import time
import threading
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import pickle
import requests

def get_virtual_ip(server_host:str, server_port:int) -> str:
    """
    Establishes a secure connection to a VPN server and retrieves a virtual IP address.

    Args:
        server_host (str): The hostname or IP address of the VPN server.
        server_port (int): The port number on which the VPN server is listening.

    Returns:
        str: The virtual IP address assigned by the VPN server if successful, otherwise None.
    """

    print("Connecting to VPN...")
    
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations("./VPN_SERVER/server.crt")

    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.connect((server_host, server_port))
    conn = context.wrap_socket(raw_socket, server_hostname=server_host)

    try:
        conn.send(b"Connection successful")
        virtual_ip = conn.recv(1024).decode('utf-8')
        print(f"Recived virtual IP: {virtual_ip}")

        return virtual_ip
        
    except Exception as e:
        print(f"Error to get virtual IP: {e}")
        return None
    
    finally:
        conn.close()

def open_youtube_with_proxy(video_url:str, server_host:str, server_port:int, watching_time:int) -> None:
    """
    Opens a YouTube video URL using a proxy server and plays the video.

    Args:
        video_url (str): The URL of the YouTube video to be opened.
        server_host (str): The hostname or IP address of the proxy server.
        server_port (int): The port number on which the proxy server is listening.
        watching_time (int): The amount of time (in seconds) to watch the video before closing the browser.

    Returns:
        None
    """

    proxy_address = get_virtual_ip(server_host, server_port)

    if proxy_address == '':
        print("Error to get proxy address")
        return

    print(f"Opening YouTube with proxy: {proxy_address}")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--proxy-server={proxy_address}')
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--proxy-bypass-list=*.local")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")  # Para sistemas sem GPU
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36")  # Atualiza para a versão correta do Chrome

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(video_url)

    except Exception as e:
        print(f"Error to get YouTube video: {e}")
        return

    time.sleep(5) 

    try:
        play_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-large-play-button")))
        play_button.click()
        print("Click on play button successfully.")
        
    except Exception as e:
        print(f"Error to click on play button: {e}")

    time.sleep(watching_time)
    driver.quit()

def main() -> str:

    """
    Main function of the script.

    This function starts a loop which opens several YouTube videos using different proxies.
    The videos and the number of times each video should be opened are defined in the videos dictionary.
    The server_host and server_port variables define the proxy server to be used.
    The open_youtube_with_proxy function is called in a separate thread for each video.
    The threads are stored in the threads list and started.
    After all threads have finished, the function waits for them to finish and then restarts the loop.

    Returns:
        str
    """

    with open('./videos_to_watch.json') as f: 
        videos = json.load(f)
    
    qnty_pages_for_each_video = 1

    server_host = "127.0.0.1"
    server_port = 8443  

    threads = []


    for video, settings in videos.items():
        duration = settings['duration'] + random.randint(0, settings['variation'])

        for _ in range(qnty_pages_for_each_video):
            thread = threading.Thread(target=open_youtube_with_proxy, args=(video, server_host, server_port, duration))
            threads.append(thread)
            thread.start()  

    for thread in threads:
        thread.join()

    return 'Done!'

def run_main():
    while True:
        main()

if __name__ == "__main__":
    run_main()
    # server_host = "127.0.0.1"
    # server_port = 8443
    # virtual_ip = get_virtual_ip(server_host, server_port)
    # print(virtual_ip)


#temos que abri o powershell como administrador   
# #usar este codigo  --> Set-Location -Path F:\youtube-gabriel\youtube_views\VPN_SERVER && python3 .\vpn_server.py