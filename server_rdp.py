# server_rdp_fixed.py
import socket
import threading
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import struct
import time

class RemoteDesktopServer:
    def __init__(self, host='0.0.0.0', port=5002):
        self.host = host
        self.port = port
        self.quality = 50
        
    def capture_screen(self):
        """Captura la pantalla"""
        try:
            # Capturar pantalla con PIL
            screenshot = ImageGrab.grab()
            screenshot = screenshot.convert('RGB')
            
            # Convertir a numpy array
            img_np = np.array(screenshot)
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            # Comprimir imagen
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            success, encoded_img = cv2.imencode('.jpg', img_np, encode_param)
            
            if success:
                return encoded_img.tobytes()
            return None
            
        except Exception as e:
            print(f"Error capturando pantalla: {e}")
            return None
    
    def handle_mouse_command(self, command):
        """Procesa comandos del mouse"""
        try:
            if command.startswith('click:'):
                _, x, y = command.split(':')
                x, y = int(x), int(y)
                pyautogui.click(x, y)
                print(f"Click en {x}, {y}")
                
            elif command.startswith('move:'):
                _, x, y = command.split(':')
                x, y = int(x), int(y)
                pyautogui.moveTo(x, y)
                
            elif command.startswith('right_click:'):
                _, x, y = command.split(':')
                x, y = int(x), int(y)
                pyautogui.rightClick(x, y)
                
        except Exception as e:
            print(f"Error en comando mouse: {e}")
    
    def handle_keyboard_command(self, command):
        """Procesa comandos del teclado"""
        try:
            if command.startswith('type:'):
                text = command[5:]
                pyautogui.write(text)
            elif command == 'enter':
                pyautogui.press('enter')
            elif command == 'backspace':
                pyautogui.press('backspace')
                
        except Exception as e:
            print(f"Error en comando teclado: {e}")
    
    def handle_client(self, client_socket, client_address):
        """Maneja la conexión con el cliente"""
        print(f"Conexión aceptada desde {client_address}")
        
        try:
            while True:
                # Capturar y enviar pantalla
                screen_data = self.capture_screen()
                if screen_data:
                    try:
                        # Enviar tamaño primero
                        size = len(screen_data)
                        client_socket.sendall(struct.pack(">L", size))
                        # Enviar datos
                        client_socket.sendall(screen_data)
                    except:
                        break
                
                # Verificar comandos
                try:
                    client_socket.settimeout(0.1)
                    data = client_socket.recv(1024).decode('utf-8')
                    if data:
                        if data.startswith('mouse:'):
                            self.handle_mouse_command(data)
                        elif data.startswith('keyboard:'):
                            self.handle_keyboard_command(data[9:])
                        elif data == 'quit':
                            break
                except socket.timeout:
                    pass
                except:
                    break
                
                time.sleep(0.1)  # 10 FPS
                
        except Exception as e:
            print(f"Error con cliente {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"Conexión cerrada: {client_address}")
    
    def start_server(self):
        """Inicia el servidor"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print(f"Servidor RDP escuchando en {self.host}:{self.port}")
            
            while True:
                client_socket, client_address = server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            print(f"Error del servidor: {e}")
        finally:
            server_socket.close()

if __name__ == "__main__":
    print("Iniciando servidor de escritorio remoto...")
    server = RemoteDesktopServer()
    server.start_server()