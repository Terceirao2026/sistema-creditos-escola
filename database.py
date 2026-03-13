import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# -------------------------
# USUÁRIOS
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE,
    turma TEXT,
    senha TEXT,
    creditos INTEGER DEFAULT 0
)
""")

# -------------------------
# HISTÓRICO
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    valor INTEGER,
    motivo TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------------------------
# COMPROVANTES
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS comprovantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    arquivo TEXT,
    creditos INTEGER,
    status TEXT DEFAULT 'pendente',
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------------------------
# TICKETS
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
id INTEGER PRIMARY KEY AUTOINCREMENT,
usuario_id INTEGER,
nome TEXT,
status TEXT DEFAULT 'aberto',
fechamento INTEGER DEFAULT 0,
data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------------------------
# CHAT DO TICKET
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS suporte (
id INTEGER PRIMARY KEY AUTOINCREMENT,
ticket_id INTEGER,
autor TEXT,
mensagem TEXT,
data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ticket_mensagens (
id INTEGER PRIMARY KEY AUTOINCREMENT,
ticket_id INTEGER,
autor TEXT,
mensagem TEXT,
data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS suporte_publico (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT,
email TEXT,
mensagem TEXT,
resposta TEXT,
status TEXT DEFAULT 'aberto',
data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------------------------
# PRODUTOS DA SEMANA
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT,
preco REAL,
ativo INTEGER DEFAULT 1
)
""")

# -------------------------
# RESERVAS DOS ALUNOS
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS reservas (
id INTEGER PRIMARY KEY AUTOINCREMENT,
usuario_id INTEGER,
produto_id INTEGER,
quantidade INTEGER,
status TEXT DEFAULT 'pendente',
data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Banco de dados criado corretamente!")