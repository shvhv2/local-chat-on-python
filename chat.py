import socket
import threading
import sys
import os

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        self.server_username = "Сервер"

    def broadcast(self, message, sender=None):
        with self.lock:
            for client in list(self.clients.values()):
                if client != sender:
                    try:
                        client.send(message.encode('utf-8'))
                    except:
                        pass
            # Сервер тоже видит сообщения
            if sender is not None:
                print(message, end='')

    def handle_client(self, client_socket):
        try:
            username = client_socket.recv(1024).decode('utf-8').strip()
            if not username:
                raise Exception("Invalid username")
            
            with self.lock:
                self.clients[username] = client_socket
            
            welcome_msg = f"\n{username} присоединился к чату. кол-во лбдей в чате: {len(self.clients)}\n"
            self.broadcast(welcome_msg, client_socket)
            
            while True:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:
                        break
                    full_msg = f"{username}> {message}\n"
                    self.broadcast(full_msg, client_socket)
                except:
                    break

        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            with self.lock:
                if username in self.clients:
                    del self.clients[username]
            leave_msg = f"\n{username} покинул чат. кол-во лбдей в чате: {len(self.clients)}\n"
            self.broadcast(leave_msg)
            client_socket.close()

    def run(self):
        print(f"\nСервер запущен на {HOST}:{PORT}")
        self.server_username = input("Введите ваше имя: ")
        print("Вы в чате. Пишите сообщения (/exit для выхода)\n")

        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.daemon = True
        accept_thread.start()

        try:
            while True:
                msg = input()
                if msg.lower() == '/exit':
                    break
                self.broadcast(f"{self.server_username}> {msg}\n")
        except KeyboardInterrupt:
            pass
        finally:
            self.server_socket.close()
            print("Сервер остановлен")

    def accept_connections(self):
        while True:
            try:
                client_socket, _ = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except:
                break

class ChatClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = ""

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    print("\nСоединение с сервером потеряно")
                    os._exit(0)
                print(message, end='')
            except:
                break

    def run(self):
        print("\nПодключение к чату...")
        self.username = input("Введите ваше имя: ")
        
        try:
            self.client_socket.connect((HOST, PORT))
            self.client_socket.send(self.username.encode('utf-8'))
            
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            print("\nВы в чате. Пишите сообщения (/exit для выхода)")
            while True:
                msg = input()
                if msg.lower() == '/exit':
                    break
                self.client_socket.send(msg.encode('utf-8'))
        except Exception as e:
            print(f"\nОшибка подключения: {e}")
        finally:
            self.client_socket.close()
            print("Отключено от сервера")

def main():
    global HOST, PORT
    HOST = get_local_ip()
    PORT = 5555

    print(f"\nВаш IP: {HOST}")
    choice = input("""
 _________________________________________________
|                 ЧАТ                             |
|           В локальной сети                      |
| Запустить чат [1] подключиться к чату [2]       |
|_________________________________________________|
""").strip()
    
    if choice == '1':
        server = ChatServer()
        server.run()
    elif choice == '2':
        server_ip = input(f"Введите IP сервера [{HOST}]: ").strip() or HOST
        HOST = server_ip
        client = ChatClient()
        client.run()
    else:
        print("Неверный выбор")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход...")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if os.name == 'nt':
            input("Нажмите Enter для выхода...")
