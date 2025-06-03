import os

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:luft%40123@localhost:5432/equipe_db"
    SECRET_KEY = "uma_senha_supersecreta"
    SQLALCHEMY_TRACK_MODIFICATIONS = False