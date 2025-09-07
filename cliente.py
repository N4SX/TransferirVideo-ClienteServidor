import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import os
import webbrowser

SERVER_URL = "http://10.180.43.53:5000"
MEDIA_DIR = "media_cliente"

class ClienteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cliente de Vídeos")
        self.root.geometry("700x500")
        
        self.video_path = None
        self.filtro_var = tk.StringVar(value="grayscale")

        # Frame principal
        main_frame = tk.Frame(root)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # --- Seção de Upload ---
        upload_frame = ttk.LabelFrame(main_frame, text="Upload de Vídeo")
        upload_frame.pack(fill=tk.X, padx=5, pady=5)

        self.lbl_arquivo = tk.Label(upload_frame, text="Nenhum arquivo selecionado")
        self.lbl_arquivo.pack(side=tk.LEFT, padx=10)

        tk.Button(upload_frame, text="Selecionar Vídeo", command=self.selecionar_video).pack(side=tk.LEFT, padx=5)
        
        ttk.Combobox(upload_frame, textvariable=self.filtro_var, values=["grayscale", "pixel", "canny"], width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(upload_frame, text="Enviar ao Servidor", command=self.enviar_video).pack(side=tk.LEFT, padx=5)

        # --- Seção de Histórico ---
        history_frame = ttk.LabelFrame(main_frame, text="Histórico de Vídeos")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Button(history_frame, text="Atualizar Histórico", command=self.ver_historico).pack(pady=5)

        cols = ("ID", "Nome Original", "Filtro", "Data")
        self.tree = ttk.Treeview(history_frame, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Scrollbar para a Treeview
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Botões de Visualização ---
        view_buttons_frame = tk.Frame(history_frame)
        view_buttons_frame.pack(pady=5)
        tk.Button(view_buttons_frame, text="Ver Original", command=lambda: self.visualizar_video("original")).pack(side=tk.LEFT, padx=5)
        tk.Button(view_buttons_frame, text="Ver Processado", command=lambda: self.visualizar_video("processed")).pack(side=tk.LEFT, padx=5)

    def selecionar_video(self):
        self.video_path = filedialog.askopenfilename(
            title="Selecione um vídeo",
            filetypes=[("Arquivos de vídeo", "*.mp4 *.avi *.mov")]
        )
        if self.video_path:
            self.lbl_arquivo.config(text=os.path.basename(self.video_path))
            messagebox.showinfo("Selecionado", f"Arquivo: {os.path.basename(self.video_path)}")

    def enviar_video(self):
        if not self.video_path:
            messagebox.showwarning("Atenção", "Selecione um vídeo primeiro!")
            return
        
        filtro = self.filtro_var.get()
        files = {"file": (os.path.basename(self.video_path), open(self.video_path, "rb"))}
        data = {"filter": filtro}

        try:
            resp = requests.post(f"{SERVER_URL}/upload", files=files, data=data, timeout=300) # Timeout longo
            if resp.status_code == 201:
                messagebox.showinfo("Sucesso", "Vídeo enviado e processado com sucesso!")
                self.ver_historico()
            else:
                messagebox.showerror("Erro", f"Falha no envio: {resp.text}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")

    def ver_historico(self):
        try:
            resp = requests.get(f"{SERVER_URL}/historico")
            if resp.status_code == 200:
                # Limpa a Treeview antes de inserir novos dados
                for i in self.tree.get_children():
                    self.tree.delete(i)
                
                historico = resp.json()
                for v in historico:
                    self.tree.insert("", "end", values=(v['id'], v['original_name'], v['filter'], v['created_at']))
            else:
                messagebox.showerror("Erro", "Não foi possível obter o histórico do servidor.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível obter o histórico: {e}")

    def visualizar_video(self, tipo):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Atenção", "Selecione um vídeo no histórico primeiro!")
            return
        
        item_details = self.tree.item(selected_item)
        video_id = item_details['values'][0]
        
        try:
            resp = requests.get(f"{SERVER_URL}/video/{video_id}/{tipo}", stream=True)
            if resp.status_code == 200:
                # Salva o vídeo localmente para visualização
                video_path = os.path.join(MEDIA_DIR, f"{video_id}_{tipo}.mp4")
                with open(video_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                messagebox.showinfo("Download Concluído", f"Vídeo salvo em {video_path}. Abrindo player...")
                # Abre o vídeo com o player padrão do sistema
                webbrowser.open(os.path.realpath(video_path))
            else:
                messagebox.showerror("Erro", f"Não foi possível baixar o vídeo: {resp.text}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível baixar o vídeo: {e}")

if __name__ == "__main__":
    os.makedirs(MEDIA_DIR, exist_ok=True)
    root = tk.Tk()
    app = ClienteApp(root)
    root.mainloop()