from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave-secreta-simples"
DB_NAME = "consultas.db"

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            data TEXT NOT NULL,   -- formato YYYY-MM-DD
            hora TEXT NOT NULL,   -- formato HH:MM
            medico TEXT NOT NULL,
            UNIQUE (data, medico) -- impede 2 consultas com o mesmo médico no mesmo dia
        );
        """
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return redirect(url_for("agendar"))

#a escolha dos métodos indica o que a página pode fazer
@app.route("/agendar", methods=["GET", "POST"])
def agendar():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()
        data_str = request.form.get("data", "").strip()
        hora_str = request.form.get("hora", "").strip()
        medico = request.form.get("medico", "").strip()

        # 1) Valida campos obrigatórios
        if not (nome and data_str and hora_str and medico):
            flash("Preencha todos os campos obrigatórios (nome, data, hora e médico).")
            return redirect(url_for("agendar"))

        # 2) Valida formato da data e se é dia útil (segunda a sexta)
        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Data inválida.")
            return redirect(url_for("agendar"))

        # weekday(): 0 = segunda, 6 = domingo
        if data_obj.weekday() > 4:
            flash("Agendamentos só podem ser feitos de segunda a sexta-feira.")
            return redirect(url_for("agendar"))

        # 3) Valida hora (entre 08:00 e 16:00 como início)
        try:
            hora_obj = datetime.strptime(hora_str, "%H:%M").time()
        except ValueError:
            flash("Hora inválida.")
            return redirect(url_for("agendar"))

        if not (8 <= hora_obj.hour <= 16 and hora_obj.minute == 0):
            flash("Horários permitidos: início entre 08:00 e 16:00, de 1 em 1 hora.")
            return redirect(url_for("agendar"))

        # 4) Insere no banco (vai falhar se já existir consulta daquele médico no dia)
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO agendamentos (nome, email, telefone, data, hora, medico)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nome, email, telefone, data_str, hora_str, medico),
            )
            conn.commit()
            flash("Consulta agendada com sucesso!")
        except sqlite3.IntegrityError:
            flash("Já existe um agendamento para esse médico nesta data.")
        finally:
            conn.close()

        return redirect(url_for("agendar"))

    # GET
    return render_template("agendar.html")


@app.route("/lista")
def listar_agendamentos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM agendamentos
        ORDER BY data ASC, medico ASC, hora ASC
        """
    )
    agendamentos = cur.fetchall()
    conn.close()
    return render_template("lista.html", agendamentos=agendamentos)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
