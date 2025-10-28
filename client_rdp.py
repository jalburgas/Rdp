# client_rdp_fixed.py
import socket
import cv2
import numpy as np
import struct
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading

class RemoteDesktopClient:
    def __init__(self):
        self.server_host = 'localhost'
        self.server_port = 5002
        self.socket = None
        self.connected = False
        self.current_image = None
        
    def connect(self, host, port):
        """Conecta al servidor"""
        try:
            self.server_host = host
            self.server_port = port
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del servidor"""
        if self.socket:
            try:
                self.socket.send("quit".encode())
            except:
                pass
            self.socket.close()
            self.connected = False
    
    def receive_screen(self):
        """Recibe la pantalla del servidor"""
        try:
            # Recibir tamaño
            size_data = self.recv_all(4)
            if not size_data:
                return None
                
            size = struct.unpack(">L", size_data)[0]
            
            # Recibir datos de imagen
            img_data = self.recv_all(size)
            if not img_data:
                return None
            
            # Decodificar imagen
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
            
        except Exception as e:
            print(f"Error recibiendo pantalla: {e}")
            return None
    
    def recv_all(self, size):
        """Recibe todos los datos especificados"""
        data = b""
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def send_command(self, command):
        """Envía comando al servidor"""
        if self.connected:
            try:
                self.socket.send(command.encode())
            except:
                self.connected = False

class RDPClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cliente de Escritorio Remoto")
        self.root.geometry("1024x768")
        
        self.client = RemoteDesktopClient()
        self.scale_factor = 1.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz"""
        # Frame de conexión
        conn_frame = ttk.Frame(self.root)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(conn_frame, text="IP:").grid(row=0, column=0, padx=5)
        self.ip_entry = ttk.Entry(conn_frame, width=15)
        self.ip_entry.insert(0, "192.168.4.129")
        self.ip_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(conn_frame, text="Puerto:").grid(row=0, column=2, padx=5)
        self.port_entry = ttk.Entry(conn_frame, width=8)
        self.port_entry.insert(0, "5002")
        self.port_entry.grid(row=0, column=3, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Conectar", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=5)
        
        # Frame de pantalla
        screen_frame = ttk.Frame(self.root)
        screen_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas para mostrar pantalla remota
        self.canvas = tk.Canvas(screen_frame, bg="black", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind eventos
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Desconectado")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def toggle_connection(self):
        """Conecta/desconecta"""
        if not self.client.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        """Establece conexión"""
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        
        if self.client.connect(ip, port):
            self.connect_btn.config(text="Desconectar")
            self.ip_entry.config(state="disabled")
            self.port_entry.config(state="disabled")
            self.status_var.set(f"Conectado a {ip}:{port}")
            
            # Iniciar hilo de pantalla
            self.screen_thread = threading.Thread(target=self.screen_loop)
            self.screen_thread.daemon = True
            self.screen_thread.start()
        else:
            messagebox.showerror("Error", "No se pudo conectar al servidor")
    
    def disconnect(self):
        """Cierra conexión"""
        self.client.disconnect()
        self.connect_btn.config(text="Conectar")
        self.ip_entry.config(state="normal")
        self.port_entry.config(state="normal")
        self.status_var.set("Desconectado")
        self.canvas.delete("all")
    
    def screen_loop(self):
        """Loop principal para recibir pantalla"""
        while self.client.connected:
            try:
                img = self.client.receive_screen()
                if img is not None:
                    # Convertir para tkinter
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img_rgb)
                    
                    # Escalar si es necesario
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()
                    
                    if canvas_width > 10 and canvas_height > 10:
                        img_width, img_height = pil_img.size
                        
                        scale_x = canvas_width / img_width
                        scale_y = canvas_height / img_height
                        self.scale_factor = min(scale_x, scale_y)
                        
                        new_width = int(img_width * self.scale_factor)
                        new_height = int(img_height * self.scale_factor)
                        
                        if new_width > 0 and new_height > 0:
                            pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    self.current_image = ImageTk.PhotoImage(pil_img)
                    self.root.after(0, self.update_display)
                else:
                    break
                    
            except Exception as e:
                print(f"Error en screen_loop: {e}")
                break
        
        if self.client.connected:
            self.root.after(0, self.disconnect)
    
    def update_display(self):
        """Actualiza la pantalla en el canvas"""
        if self.current_image:
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)
    
    def on_click(self, event):
        """Maneja clic izquierdo"""
        if self.client.connected:
            x = int(event.x / self.scale_factor)
            y = int(event.y / self.scale_factor)
            self.client.send_command(f"mouse:click:{x}:{y}")
    
    def on_right_click(self, event):
        """Maneja clic derecho"""
        if self.client.connected:
            x = int(event.x / self.scale_factor)
            y = int(event.y / self.scale_factor)
            self.client.send_command(f"mouse:right_click:{x}:{y}")
    
    def on_mouse_move(self, event):
        """Maneja movimiento del mouse (para mostrar coordenadas)"""
        if self.client.connected:
            # Solo mostrar coordenadas, no enviar continuamente
            x = int(event.x / self.scale_factor)
            y = int(event.y / self.scale_factor)
            self.status_var.set(f"Conectado - X: {x}, Y: {y}")
    
    def run(self):
        """Inicia la aplicación"""
        try:
            self.root.mainloop()
        finally:
            if self.client.connected:
                self.client.disconnect()

if __name__ == "__main__":
    print("Iniciando cliente de escritorio remoto...")
    app = RDPClientGUI()
    app.run()