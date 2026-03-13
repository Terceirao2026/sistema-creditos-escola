import os
from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import sqlite3


app = Flask(__name__)

app.secret_key = "segredo123"
SENHA_ADMIN = "admin123"

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def home():
    return "/register.html"


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        nome = request.form["nome"]
        turma = request.form["turma"]
        senha = request.form["senha"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # verificar se nome já existe
        cursor.execute("SELECT * FROM usuarios WHERE nome=?", (nome,))
        usuario = cursor.fetchone()

        if usuario:
            conn.close()
            return render_template("register.html", erro="Usuário já existe")

        # cadastrar novo usuário
        cursor.execute(
            "INSERT INTO usuarios (nome, turma, senha) VALUES (?, ?, ?)",
            (nome, turma, senha)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")




@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        nome = request.form["nome"]
        senha = request.form["senha"]

        # login admin
        if senha == SENHA_ADMIN:
            return redirect("/admin")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE nome=? AND senha=?",
            (nome, senha)
        )

        usuario = cursor.fetchone()

        conn.close()

        if usuario:
            session["usuario_id"] = usuario[0]
            return redirect("/dashboard")

    return render_template("login.html")





@app.route("/dashboard")
def dashboard():

    if "usuario_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT nome, turma, creditos FROM usuarios WHERE id=?",
        (session["usuario_id"],)
    )

    usuario = cursor.fetchone()

    cursor.execute(
        "SELECT valor, motivo, data FROM historico WHERE usuario_id=? ORDER BY data DESC",
        (session["usuario_id"],)
    )

    historico = cursor.fetchall()

    # pegar reservas do usuario
    cursor.execute(
        """
        SELECT produtos.nome, reservas.quantidade, reservas.status
        FROM reservas
        JOIN produtos ON reservas.produto_id = produtos.id
        WHERE reservas.usuario_id=?
        """,
        (session["usuario_id"],)
    )

    reservas = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        nome=usuario[0],
        turma=usuario[1],
        creditos=usuario[2],
        historico=historico,
        reservas=reservas
    )

@app.route("/admin_reservas")
def admin_reservas():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # reservas da tabela
    cursor.execute("""
SELECT reservas.id, usuarios.nome, usuarios.turma,
produtos.nome, reservas.quantidade, reservas.status
FROM reservas
JOIN usuarios ON usuarios.id = reservas.usuario_id
JOIN produtos ON produtos.id = reservas.produto_id
ORDER BY reservas.id DESC
""")

    reservas = cursor.fetchall()

    # resumo de produtos reservados
    cursor.execute("""
SELECT produtos.nome, SUM(reservas.quantidade)
FROM reservas
JOIN produtos ON produtos.id = reservas.produto_id
GROUP BY produtos.nome
""")

    resumo = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_reservas.html",
        reservas=reservas,
        resumo=resumo
    )

@app.route("/admin_produtos")
def admin_produtos():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos WHERE ativo=1 ORDER BY id DESC")
    produtos = cursor.fetchall()

    conn.close()

    return render_template("admin_produtos.html", produtos=produtos)

@app.route("/adicionar_produto", methods=["POST"])
def adicionar_produto():

    nome = request.form["nome"]
    preco = float(request.form["preco"])

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO produtos (nome, preco, ativo) VALUES (?, ?, 1)",
        (nome, preco)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_produtos")

@app.route("/desativar_produto/<int:id>")
def desativar_produto(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE produtos SET ativo=0 WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_produtos")


@app.route("/admin")
def admin():

    buscar = request.args.get("buscar")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if buscar:
        cursor.execute(
            "SELECT id, nome, turma, creditos, senha FROM usuarios WHERE nome LIKE ?",
            ("%" + buscar + "%",)
        )
    else:
        cursor.execute(
            """SELECT id, nome, turma, creditos, senha FROM usuarios""")

    usuarios = cursor.fetchall()

    conn.close()

    return render_template("admin.html", usuarios=usuarios)




@app.route("/adicionar_credito", methods=["POST"])
def adicionar_credito():

    usuario_id = request.form["usuario_id"]
    valor = request.form["valor"]
    motivo = request.form["motivo"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # adicionar créditos
    cursor.execute(
        "UPDATE usuarios SET creditos = creditos + ? WHERE id=?",
        (valor, usuario_id)
    )

    # salvar no histórico
    cursor.execute(
        "INSERT INTO historico (usuario_id, valor, motivo) VALUES (?, ?, ?)",
        (usuario_id, valor, motivo)
    )

    conn.commit()
    conn.close()

  
    return redirect("/admin")




@app.route("/remover_credito", methods=["POST"])
def remover_credito():

    usuario_id = request.form["usuario_id"]
    valor = int(request.form["valor"])
    motivo = request.form["motivo"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET creditos = creditos - ? WHERE id=?",
        (valor, usuario_id)
    )

    cursor.execute(
        "INSERT INTO historico (usuario_id, valor, motivo) VALUES (?, ?, ?)",
        (usuario_id, -valor, motivo)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")




@app.route("/comprar")
def comprar():

    if "usuario_id" not in session:
        return redirect("/login")

    return render_template("comprar.html")

from werkzeug.utils import secure_filename

import uuid




@app.route("/enviar_comprovante", methods=["POST"])
def enviar_comprovante():

    if "usuario_id" not in session:
        return redirect("/login")

    creditos = request.form["creditos"]

    arquivo = request.files["comprovante"]

    nome = str(uuid.uuid4()) + "_" + secure_filename(arquivo.filename)

    caminho = os.path.join("uploads", nome)

    arquivo.save(caminho)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO comprovantes (usuario_id, arquivo, creditos) VALUES (?, ?, ?)",
        (session["usuario_id"], nome, creditos)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")




@app.route("/conta")
def conta():

    if "usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["usuario_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT nome, turma, creditos FROM usuarios WHERE id=?", (usuario_id,))
    dados = cursor.fetchone()

    usuario = {
        "nome": dados[0],
        "turma": dados[1],
        "creditos": dados[2]
    }

    return render_template("conta.html", usuario=usuario)




@app.route("/mudar_senha", methods=["GET", "POST"])
def mudar_senha():

    if "usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        nova_senha = request.form["nova_senha"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE usuarios SET senha=? WHERE id=?",
            (nova_senha, session["usuario_id"])
        )

        conn.commit()
        conn.close()

        return redirect("/conta")

    return render_template("mudar_senha.html")




@app.route("/comprovantes")
def ver_comprovantes():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT comprovantes.id, usuarios.nome, comprovantes.arquivo, comprovantes.data
    FROM comprovantes
    JOIN usuarios ON usuarios.id = comprovantes.usuario_id
    ORDER BY comprovantes.data DESC
    """)

    dados = cursor.fetchall()

    conn.close()

    return render_template("comprovantes.html", comprovantes=dados)






@app.route("/suporte")
def suporte():

    if "usuario_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, status, data
    FROM tickets
    WHERE usuario_id=?
    ORDER BY id DESC
    """,(session["usuario_id"],))

    tickets = cursor.fetchall()

    conn.close()

    return render_template("suporte.html", tickets=tickets)





@app.route("/suporte_admin", methods=["GET","POST"])
def suporte_admin():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        resposta = request.form["resposta"]
        msg_id = request.form["msg_id"]

        cursor.execute(
        "UPDATE suporte SET resposta=? WHERE id=?",
        (resposta,msg_id)
        )

        conn.commit()

    cursor.execute("SELECT id,nome,mensagem,resposta FROM suporte ORDER BY id ASC")

    mensagens = cursor.fetchall()

    conn.close()

    return render_template("suporte_admin.html", mensagens=mensagens)

from flask import send_from_directory




@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory("uploads", filename)





@app.route("/admin_comprovantes")
def admin_comprovantes():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT comprovantes.id, usuarios.nome, comprovantes.arquivo,
           comprovantes.creditos, comprovantes.status
    FROM comprovantes
    JOIN usuarios ON usuarios.id = comprovantes.usuario_id
    """)

    dados = cursor.fetchall()

    conn.close()

    return render_template("admin_comprovantes.html", comprovantes=dados)




@app.route("/aprovar", methods=["POST"])
def aprovar():

    id = request.form["id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # pegar usuário e créditos do comprovante
    cursor.execute(
        "SELECT usuario_id, creditos FROM comprovantes WHERE id=?",
        (id,)
    )

    dados = cursor.fetchone()

    usuario_id = dados[0]
    creditos = dados[1]

    # adicionar créditos
    cursor.execute(
"UPDATE usuarios SET creditos = creditos + ? WHERE id=?",
(creditos, usuario_id)
)

# salvar histórico
    cursor.execute(
"INSERT INTO historico (usuario_id, valor, motivo) VALUES (?, ?, ?)",
(usuario_id, creditos, "Compra de créditos")
)

    # marcar comprovante como aprovado
    cursor.execute(
        "UPDATE comprovantes SET status='aprovado' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_comprovantes")




@app.route("/recusar", methods=["POST"])
def recusar():

    id = request.form["id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE comprovantes SET status='recusado' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_comprovantes")




@app.route("/excluir_usuario", methods=["POST"])
def excluir_usuario():

    usuario_id = request.form["usuario_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # apagar histórico do usuário
    cursor.execute(
        "DELETE FROM historico WHERE usuario_id=?",
        (usuario_id,)
    )

    # apagar comprovantes
    cursor.execute(
        "DELETE FROM comprovantes WHERE usuario_id=?",
        (usuario_id,)
    )

    # apagar usuário
    cursor.execute(
        "DELETE FROM usuarios WHERE id=?",
        (usuario_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")





@app.route("/historico/<int:usuario_id>")
def ver_historico(usuario_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
    "SELECT valor, motivo, data FROM historico WHERE usuario_id=? ORDER BY id DESC",
    (usuario_id,)
)

    historico = cursor.fetchall()

    conn.close()

    return render_template("historico_admin.html", historico=historico)





@app.route("/alterar_senha", methods=["POST"])
def alterar_senha():

    usuario_id = request.form["usuario_id"]
    nova_senha = request.form["nova_senha"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET senha=? WHERE id=?",
        (nova_senha, usuario_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")




@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/ver_suporte")
def ver_suporte():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM suporte ORDER BY id DESC")

    mensagens = cursor.fetchall()

    conn.close()

    return render_template("ver_suporte.html", mensagens=mensagens)




@app.route("/abrir_ticket", methods=["POST"])
def abrir_ticket():

    if "usuario_id" not in session:
        return redirect("/login")

    mensagem = request.form["mensagem"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    usuario = session["usuario_id"]

    cursor.execute("""
INSERT INTO tickets (usuario_id, status, fechamento)
VALUES (?, 'aberto', 0)
""",(usuario,))

    ticket_id = cursor.lastrowid

    # primeira mensagem
    cursor.execute("""
    INSERT INTO ticket_mensagens (ticket_id,autor,mensagem)
    VALUES (?,?,?)
    """,(ticket_id,"aluno",mensagem))

    conn.commit()
    conn.close()

    return redirect("/suporte")




@app.route("/ticket/<int:ticket_id>")
def ver_ticket(ticket_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT autor,mensagem,data
    FROM ticket_mensagens
    WHERE ticket_id=?
    ORDER BY id ASC
    """,(ticket_id,))

    mensagens = cursor.fetchall()

    conn.close()

    admin = False

    if "admin" in session:
        admin = True

    return render_template(
        "ticket_chat.html",
        mensagens=mensagens,
        ticket_id=ticket_id,
        admin=admin
    )




@app.route("/responder_ticket", methods=["POST"])
def responder_ticket():

    mensagem = request.form["mensagem"]
    ticket_id = request.form["ticket_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO ticket_mensagens (ticket_id,autor,mensagem) VALUES (?,?,?)",
        (ticket_id,"aluno",mensagem)
    )

    conn.commit()
    conn.close()

    return redirect(f"/ticket/{ticket_id}")




@app.route("/admin_tickets")
def admin_tickets():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT tickets.id,
COALESCE(usuarios.nome, tickets.nome),
tickets.status
FROM tickets
LEFT JOIN usuarios ON usuarios.id = tickets.usuario_id
    ORDER BY tickets.id DESC
    """)

    tickets = cursor.fetchall()

    conn.close()

    return render_template("admin_tickets.html", tickets=tickets)




@app.route("/admin_responder_ticket", methods=["POST"])
def admin_responder_ticket():

    mensagem = request.form["mensagem"]
    ticket_id = request.form["ticket_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO ticket_mensagens (ticket_id,autor,mensagem) VALUES (?,?,?)",
        (ticket_id,"admin",mensagem)
    )

    conn.commit()
    conn.close()

    return redirect(f"/admin_ticket/{ticket_id}")




@app.route("/fechar_ticket/<int:ticket_id>")
def fechar_ticket(ticket_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
    "UPDATE tickets SET status='fechado' WHERE id=?",
    (ticket_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_tickets")




@app.route("/admin_ticket/<int:ticket_id>")
def admin_ticket(ticket_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT autor,mensagem,data
    FROM ticket_mensagens
    WHERE ticket_id=?
    ORDER BY id ASC
    """,(ticket_id,))

    mensagens = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_ticket_chat.html",
        mensagens=mensagens,
        ticket_id=ticket_id
    )



@app.route("/digitando", methods=["POST"])
def digitando_rota():
    global digitando
    digitando = True
    return ""

@app.route("/ver_digitando")
def ver_digitando():
    global digitando
    d = digitando
    digitando = False
    return {"digitando": d}



@app.route("/limpar_tickets_fechados")
def limpar_tickets_fechados():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM tickets WHERE status='fechado'")
    ids = cursor.fetchall()

    for ticket in ids:
        cursor.execute(
            "DELETE FROM ticket_mensagens WHERE ticket_id=?",
            (ticket[0],)
        )

    cursor.execute("DELETE FROM tickets WHERE status='fechado'")

    conn.commit()
    conn.close()

    return redirect("/admin_tickets")





@app.route("/suporte_publico", methods=["GET","POST"])
def suporte_publico():

    if request.method == "POST":

        nome = request.form["nome"]
        mensagem = request.form["mensagem"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO tickets (usuario_id,nome,status)
        VALUES (NULL,?, 'aberto')
        """,(nome,))

        ticket_id = cursor.lastrowid

        cursor.execute("""
        INSERT INTO ticket_mensagens (ticket_id,autor,mensagem)
        VALUES (?,?,?)
        """,(ticket_id,"visitante",mensagem))

        conn.commit()
        conn.close()

        return redirect("/chat_publico/" + str(ticket_id))

    return render_template("suporte_publico.html")

@app.route("/chat_publico/<int:ticket_id>")
def chat_publico(ticket_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT autor,mensagem,data
    FROM ticket_mensagens
    WHERE ticket_id=?
    ORDER BY id ASC
    """,(ticket_id,))

    mensagens = cursor.fetchall()

    conn.close()

    return render_template(
        "chat_publico.html",
        mensagens=mensagens,
        ticket_id=ticket_id
    )

@app.route("/enviar_publico", methods=["POST"])
def enviar_publico():

    mensagem = request.form["mensagem"]
    ticket_id = request.form["ticket_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO ticket_mensagens (ticket_id,autor,mensagem)
    VALUES (?,?,?)
    """,(ticket_id,"visitante",mensagem))

    conn.commit()
    conn.close()

    return redirect(f"/chat_publico/{ticket_id}")

@app.route("/admin_suporte_publico")
def admin_suporte_publico():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, nome, status
    FROM tickets
    WHERE usuario_id IS NULL
    ORDER BY id DESC
    """)

    tickets = cursor.fetchall()

    conn.close()

    return render_template("admin_suporte_publico.html", tickets=tickets)

@app.route("/mensagens_publico/<int:ticket_id>")
def mensagens_publico(ticket_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT autor,mensagem,data
    FROM ticket_mensagens
    WHERE ticket_id=?
    ORDER BY id ASC
    """,(ticket_id,))

    mensagens = cursor.fetchall()

    conn.close()

    return {"mensagens": mensagens}

@app.route("/reservar")
def reservar():

    if "usuario_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos WHERE ativo=1")

    produtos = cursor.fetchall()

    conn.close()

    return render_template("reservar.html", produtos=produtos)

@app.route("/fazer_reserva", methods=["POST"])
def fazer_reserva():

    if "usuario_id" not in session:
        return redirect("/login")

    produto_id = request.form["produto_id"]
    quantidade = int(request.form["quantidade"])

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # pegar preço do produto
    cursor.execute(
        "SELECT preco FROM produtos WHERE id=?",
        (produto_id,)
    )

    produto = cursor.fetchone()

    if produto is None:
        conn.close()
        return "Produto não encontrado"

    preco = produto[0]

    # calcular valor total
    total = preco * quantidade

    # pegar créditos do usuário
    cursor.execute(
        "SELECT creditos FROM usuarios WHERE id=?",
        (session["usuario_id"],)
    )

    usuario = cursor.fetchone()
    creditos = usuario[0]

    

    # verificar se tem créditos suficientes
    if creditos < total:
        conn.close()
        return "Você não tem créditos suficientes para esta reserva."

    # descontar créditos
    cursor.execute(
        "UPDATE usuarios SET creditos = creditos - ? WHERE id=?",
        (total, session["usuario_id"])
    )

    # registrar no histórico
    cursor.execute(
    "INSERT INTO historico (usuario_id, valor, motivo) VALUES (?, ?, ?)",
    (
        session["usuario_id"],
        -total,
        "Reserva de produto"
    )
)

    # criar reserva
    cursor.execute(
        """
        INSERT INTO reservas (usuario_id, produto_id, quantidade, status)
        VALUES (?, ?, ?, 'pendente')
        """,
        (session["usuario_id"], produto_id, quantidade)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/entregar_reserva/<int:id>", methods=["POST"])
def entregar_reserva(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE reservas SET status='entregue' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_reservas")

@app.route("/excluir_reserva/<int:id>", methods=["POST"])
def excluir_reserva(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reservas WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin_reservas")


@app.route("/alterar_nome", methods=["POST"])
def alterar_nome():

    if "usuario_id" not in session:
        return redirect("/login")

    novo_nome = request.form["novo_nome"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET nome=? WHERE id=?",
        (novo_nome, session["usuario_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/conta")

@app.route("/confirmar_reserva/<int:reserva_id>", methods=["POST"])
def confirmar_reserva(reserva_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE reservas SET status='confirmado' WHERE id=?",
        (reserva_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_reservas")




if __name__ == "__main__":
    app.run(debug=True)