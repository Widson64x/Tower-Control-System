import os

class Config:
    # --- CONEXÃO PARA O BANCO DE DADOS LOCAL (COM SENHA CORRIGIDA) ---
    # A senha "luft@123" foi codificada para "luft%40123"
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres:luft%40123"
        "@localhost:5432/tower_control"
    )

    SECRET_KEY = os.environ.get('SECRET_KEY') or "uma_senha_supersecreta"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False