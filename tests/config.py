import os

class Config:
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://towerdb_user:"
        "afv3K6q3bN24gO8G0ohwspbBEnodHtSa"
        "@dpg-d0vg35vdiees73csea30-a.oregon-postgres.render.com"
        ":5432/equipe_db?sslmode=require"
    )
    SECRET_KEY = "uma_senha_supersecreta"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
