import socket
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

def get_virtual_ip(server_host, server_port):
    """Conecta ao servidor VPN e obtém um IP virtual."""
    print("Conectando ao servidor VPN...")
    
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations("./VPN_SERVER/server.crt")

    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.connect((server_host, server_port))
    conn = context.wrap_socket(raw_socket, server_hostname=server_host)

    try:
        conn.send(b"Conectado ao servidor VPN!")
        virtual_ip = conn.recv(1024).decode('utf-8')
        print(f"Recebido IP virtual: {virtual_ip}")
    except Exception as e:
        print(f"Erro ao obter IP virtual: {e}")
        return None
    finally:
        conn.close()  # Fecha o socket SSL
        return virtual_ip

def login_google(driver, email, senha):
    """Faz login na conta do Google."""
    driver.get("https://accounts.google.com/signin")
    
    # Espera o campo de email e insere o email
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "identifier"))).send_keys(email)
    driver.find_element(By.XPATH, '//*[@id="identifierNext"]').click()

    # Espera o campo de senha e insere a senha
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(senha)
    driver.find_element(By.XPATH, '//*[@id="passwordNext"]').click()

    # Espera o login ser completado
    WebDriverWait(driver, 10).until(EC.url_contains("myaccount"))
    print(f"Login bem-sucedido para {email}")

def save_cookies(driver, filename):
    """Salva cookies do navegador em um arquivo."""
    with open(filename, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)

def load_cookies(driver, filename):
    """Carrega cookies do arquivo no navegador."""
    try:
        with open(filename, 'rb') as filehandler:
            cookies = pickle.load(filehandler)
            for cookie in cookies:
                driver.add_cookie(cookie)
    except FileNotFoundError:
        print("Arquivo de cookies não encontrado. Realizando login.")

def abrir_video_youtube_com_proxy(video_url, server_host, server_port, email=None, senha=None):
    """Abre uma aba do Chrome com um IP virtual do servidor VPN como proxy e faz login no YouTube."""
    proxy_address = get_virtual_ip(server_host, server_port)

    if proxy_address is None:
        print("Falha ao obter um IP virtual. Saindo da função.")
        return

    print(f"Abrindo aba com proxy: {proxy_address}")

    # Configura o ChromeOptions com o proxy
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--proxy-server={proxy_address}')
    chrome_options.add_argument("--ignore-certificate-errors")  # Ignorar erros de certificado
    chrome_options.add_argument("--start-maximized")  # Inicia maximizado
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36")  # Atualiza para a versão correta do Chrome

    # Inicializa o driver do Chrome com as opções definidas
    driver = webdriver.Chrome(options=chrome_options)

    # Carrega cookies se disponíveis
    driver.get("https://www.youtube.com")  # Necessário acessar para adicionar cookies
    load_cookies(driver, 'cookies.pkl')

    # Atualiza a página para aplicar os cookies
    driver.refresh()

    # # Verifica se já estamos logados
    # if not any(cookie['name'] == 'G_AUTHUSER_H' for cookie in driver.get_cookies()):
    #     # Se o cookie de autenticação não está presente, faz login
    #     login_google(driver, email, senha)
    #     save_cookies(driver, 'cookies.pkl')  # Salva cookies após o login

    # Acesse o vídeo no YouTube
    driver.get(video_url)

    # Espera o carregamento do vídeo
    time.sleep(5)  # Espera um pouco para o vídeo carregar

    # Tenta reproduzir o vídeo simulando um clique no botão de play
    try:
        play_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-large-play-button")))
        play_button.click()
        print("Clique no botão de play realizado com sucesso.")
    except Exception as e:
        print(f"Erro ao reproduzir o vídeo: {e}")

    # Manter a aba aberta por um tempo (ajuste conforme necessário)
    time.sleep(60)  # Tempo em segundos para manter a aba aberta
    driver.quit()  # Fecha a aba após o tempo

def main():
    # Carrega as credenciais do arquivo JSON
    # with open('youtube_accounts.json') as f:
    #     contas = json.load(f)

    video_url = "https://www.youtube.com/watch?v=ye2jqnxaz2U"#input("Digite a URL do vídeo do YouTube: ")
    quantidade_abas = 2#int(input("Digite a quantidade de abas que deseja abrir: "))

    # # Verifica se a quantidade de abas é maior que a quantidade de contas
    # if quantidade_abas > len(contas):
    #     print(f"Erro: Você solicitou {quantidade_abas} abas, mas só tem {len(contas)} contas disponíveis.")
    #     return

    server_host = '127.0.0.1'  # Endereço do servidor VPN
    server_port = 8443  # Porta do servidor VPN

    threads = []

    for i in range(quantidade_abas):
        # email = contas[i]['email']
        # senha = contas[i]['senha']
        # thread = threading.Thread(target=abrir_video_youtube_com_proxy, args=(video_url, server_host, server_port, email, senha))
        thread = threading.Thread(target=abrir_video_youtube_com_proxy, args=(video_url, server_host, server_port))
        threads.append(thread)
        thread.start()  # Inicia a thread

    # Aguarda todas as threads terminarem
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
