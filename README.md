Tower-Control-System/
│
├── app/
│   ├── __init__.py         # Application factory
│   ├── models.py           # Modelos do SQLAlchemy
│   ├── extensions.py       # Instâncias de db, migrate, login_manager, etc.
│   ├── config.py           # Configurações Flask
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── gestor.py       # Rotas específicas do gestor
│   │   └── auth.py         # Login, logout
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   └── gestor/
│   │       └── dashboard.html
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── utils/
│       ├── email.py
│       └── helpers.py
│
├── migrations/             # Alembic migrations
├── tests/                  # Testes unitários
├── requirements.txt
├── .env
├── run.py                  # Entrypoint
└── README.md

ChatGPT 06