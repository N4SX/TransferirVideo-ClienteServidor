from flask import Flask, request, send_file, jsonify
import os
import cv2
import uuid
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
MEDIA_ROOT = "media_server"
DB_NAME = "videos.db"
os.makedirs(MEDIA_ROOT, exist_ok=True)

# --- BANCO DE DADOS ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            original_name TEXT NOT NULL,
            original_ext TEXT NOT NULL,
            mime_type TEXT,
            size_bytes INTEGER,
            duration_sec REAL,
            fps REAL,
            width INTEGER,
            height INTEGER,
            filter TEXT,
            created_at TEXT NOT NULL,
            path_original TEXT NOT NULL,
            path_processed TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- FUNÇÕES AUXILIARES ---
def aplicar_filtro(video_path, filtro, saida_path):
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Garante que o diretório de saída exista
    os.makedirs(os.path.dirname(saida_path), exist_ok=True)
    
    # Define se o vídeo de saída terá cor ou não
    is_color = True
    if filtro == "grayscale" or filtro == "canny":
        is_color = True # Manter 3 canais para compatibilidade

    out = cv2.VideoWriter(saida_path, fourcc, fps, (w, h), is_color)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if filtro == "grayscale":
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_GRAY2BGR) # Converte de volta para 3 canais
        elif filtro == "pixel":
            processed_frame = cv2.resize(frame, (64, 64), interpolation=cv2.INTER_LINEAR)
            processed_frame = cv2.resize(processed_frame, (w, h), interpolation=cv2.INTER_NEAREST)
        elif filtro == "canny":
            edges = cv2.Canny(frame, 100, 200)
            processed_frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR) # Converte de volta para 3 canais
        else:
            processed_frame = frame

        out.write(processed_frame)

    cap.release()
    out.release()

def extrair_metadados(video_path, file):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    return {
        "size_bytes": os.path.getsize(video_path),
        "duration_sec": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "mime_type": file.mimetype
    }

# --- ENDPOINTS DA API ---
@app.route("/upload", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        return jsonify({"error": "Arquivo não enviado"}), 400
    
    file = request.files["file"]
    filtro = request.form.get("filter", "grayscale")
    
    # Estrutura de pastas
    now = datetime.now()
    video_id = str(uuid.uuid4())
    _, ext = os.path.splitext(file.filename)
    
    # Caminho relativo para armazenamento
    relative_path = os.path.join(now.strftime('%Y/%m/%d'), 'videos', video_id)
    full_path = os.path.join(MEDIA_ROOT, relative_path)
    os.makedirs(full_path, exist_ok=True)
    
    original_dir = os.path.join(full_path, 'original')
    processed_dir = os.path.join(full_path, 'processed', filtro)
    os.makedirs(original_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    path_original = os.path.join(original_dir, f"video{ext}")
    path_processed = os.path.join(processed_dir, f"video{ext}")
    
    file.save(path_original)

    # Processamento e extração de metadados
    aplicar_filtro(path_original, filtro, path_processed)
    metadata = extrair_metadados(path_original, file)
    
    # Salvar no banco de dados
    conn = get_db_connection()
    conn.execute(
        '''
        INSERT INTO videos (id, original_name, original_ext, mime_type, size_bytes, duration_sec, fps, width, height, filter, created_at, path_original, path_processed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (video_id, file.filename, ext, metadata['mime_type'], metadata['size_bytes'], metadata['duration_sec'], metadata['fps'], metadata['width'], metadata['height'], filtro, now.isoformat(), path_original, path_processed)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Vídeo processado com sucesso!",
        "id": video_id,
        "filter": filtro
    }), 201

@app.route("/historico", methods=["GET"])
def get_historico():
    conn = get_db_connection()
    videos = conn.execute('SELECT id, original_name, filter, created_at FROM videos ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in videos])

@app.route("/video/<video_id>/<tipo>", methods=["GET"])
def get_video(video_id, tipo):
    conn = get_db_connection()
    video = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
    conn.close()

    if not video:
        return "Vídeo não encontrado", 404

    if tipo == "original":
        path = video["path_original"]
    elif tipo == "processed":
        path = video["path_processed"]
    else:
        return "Tipo de vídeo inválido", 400

    if not os.path.exists(path):
        return "Arquivo não encontrado no disco", 404
        
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)