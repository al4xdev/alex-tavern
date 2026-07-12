def start_server():
    import uvicorn
    # Executa o servidor uvicorn apontando para o app do main.py
    uvicorn.run("src.main:app", host="127.0.0.1", port=8889, log_level="info")
