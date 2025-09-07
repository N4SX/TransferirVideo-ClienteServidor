# Sistema Cliente/Servidor em Camadas (Processamento de Vídeos)

#Este trabalho compõe a primeira unidade da disciplina de Sistemas Distribuidos 2025.2

## Descrição
Este projeto implementa um sistema **cliente/servidor em três camadas** para envio, processamento e armazenamento de vídeos.  
O cliente (Tkinter) permite selecionar vídeos, escolher filtros e enviá-los ao servidor.  
O servidor (Flask + OpenCV) recebe os vídeos, aplica filtros, organiza em disco e registra metadados em um banco SQLite.  

##  Arquitetura
- **Cliente (Tkinter)**
  - Seleciona e envia vídeos via HTTP.
  - Permite escolher filtros (`grayscale`, `pixel`, `canny`).
  - Exibe histórico de vídeos enviados.
  - Baixa e abre o vídeo original ou processado.

- **Servidor (Flask + OpenCV)**
  - Recebe vídeos do cliente.
  - Aplica filtros de processamento.
  - Salva vídeos em diretórios organizados por **data** e **UUID**.
  - Registra metadados no **SQLite**.

- **Banco de Dados (SQLite)**
  - Tabela `videos` com campos como:
    - `id`, `original_name`, `mime_type`, `size_bytes`, `duration_sec`, `fps`, `width`, `height`, `filter`, `created_at`, `path_original`, `path_processed`.

---

## Organização dos Arquivos
```
media_server/
├─ {yyyy}/{mm}/{dd}/
│  └─ videos/{uuid}/
│     ├─ original/video.{ext}
│     ├─ processed/{filtro}/video.{ext}
```

---

## Tecnologias
- Python 3
- Flask (API HTTP)
- Tkinter (Cliente gráfico)
- OpenCV (Processamento de vídeo)
- SQLite (Banco de dados)

---

## Como Executar

### 1. Clonar o repositório
```bash
git clone https://github.com/usuario/repositorio.git
cd repositorio
```

### 2. Instalar dependências
No servidor e no cliente:
```bash
pip install flask opencv-python requests
```

### 3. Executar o Servidor
```bash
python servidor.py
```
- O servidor será iniciado em `http://0.0.0.0:5000`.

### 4. Executar o Cliente
Edite o arquivo `cliente.py` e configure o IP do servidor:
```python
SERVER_URL = "http://<IP_DO_SERVIDOR>:5000"
```

Depois, execute:
```bash
python cliente.py
```

---

## Fluxo de Funcionamento
1. O cliente seleciona um vídeo e escolhe o filtro.
2. O vídeo é enviado ao servidor.
3. O servidor processa e salva o original e o filtrado.
4. Os metadados são registrados no banco.
5. O cliente pode visualizar histórico, baixar e abrir os vídeos.

---

## Desenvolvido por:
  ## James Sousa
  ## Vanderlei Carvalho
  ## David Natan




