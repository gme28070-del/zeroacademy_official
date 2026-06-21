import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DATABASE_URL = os.environ.get("POSTGRES_URL")

ADMIN_USER = "killerdevost"
ADMIN_PASS = "toor"


def obter_conexao():
    if not DATABASE_URL:
        raise Exception("Variável POSTGRES_URL não configurada nas Environment Variables da Vercel.")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def inicializar_banco():
    """Cria as tabelas iniciais caso não existam — chamado sob demanda, não no import."""
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            usuario VARCHAR(50) UNIQUE NOT NULL,
            senha VARCHAR(100) NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modulos (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(150) NOT NULL,
            tipo_recurso VARCHAR(50) NOT NULL,
            conteudo TEXT NOT NULL
        );
    """)
    conexao.commit()
    cursor.close()
    conexao.close()


# ── Rota de setup (chame uma vez após o deploy) ──────────────────────────────
@app.route('/api/setup', methods=['GET'])
def setup():
    """Inicializa o banco manualmente. Acesse /api/setup uma vez após o deploy."""
    try:
        inicializar_banco()
        return jsonify({"status": "sucesso", "mensagem": "Banco inicializado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


# ── Health check ─────────────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def health():
    """Verifica se a API está no ar e se o banco responde."""
    try:
        conn = obter_conexao()
        conn.close()
        return jsonify({"status": "ok", "banco": "conectado"})
    except Exception as e:
        return jsonify({"status": "ok", "banco": "erro", "detalhe": str(e)}), 200


# ── Login ─────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"status": "erro", "mensagem": "Dados não enviados"}), 400

        usuario = dados.get("username")
        senha = dados.get("password")

        if usuario == ADMIN_USER and senha == ADMIN_PASS:
            return jsonify({
                "status": "sucesso",
                "tipo": "admin",
                "mensagem": "Autenticado como Administrador!",
                "redirecionar": "/admin-dashboard.html"
            })

        conexao = obter_conexao()
        cursor = conexao.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM alunos WHERE usuario = %s AND senha = %s", (usuario, senha))
        aluno = cursor.fetchone()
        cursor.close()
        conexao.close()

        if aluno:
            return jsonify({
                "status": "sucesso",
                "tipo": "aluno",
                "mensagem": f"Bem-vindo, {aluno['nome']}!",
                "redirecionar": "/student-dashboard.html"
            })

        return jsonify({"status": "erro", "mensagem": "Credenciais inválidas!"}), 401

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500


# ── Admin: Alunos ─────────────────────────────────────────────────────────────
@app.route('/api/admin/listar-alunos', methods=['GET'])
def listar_alunos():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT usuario, nome FROM alunos ORDER BY id DESC")
        alunos = cursor.fetchall()
        cursor.close()
        conexao.close()
        return jsonify({"status": "sucesso", "alunos": alunos})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/admin/cadastrar-aluno', methods=['POST'])
def cadastrar_aluno():
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Dados em falta"}), 400

    nome    = dados.get("nome")
    usuario = dados.get("usuario")
    senha   = dados.get("senha")

    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO alunos (nome, usuario, senha) VALUES (%s, %s, %s)",
            (nome, usuario, senha)
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        return jsonify({"status": "sucesso", "mensagem": f"Aluno {nome} registrado com sucesso!"})
    except psycopg2.IntegrityError:
        return jsonify({"status": "erro", "mensagem": "Este usuário já existe!"}), 400
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/admin/deletar-aluno', methods=['POST'])
def deletar_aluno():
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Dados em falta"}), 400

    usuario = dados.get("usuario")
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM alunos WHERE usuario = %s", (usuario,))
        conexao.commit()
        cursor.close()
        conexao.close()
        return jsonify({"status": "sucesso", "mensagem": f"Usuário {usuario} removido com sucesso!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


# ── Admin: Módulos ────────────────────────────────────────────────────────────
@app.route('/api/admin/criar-modulo', methods=['POST'])
def criar_modulo():
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Dados em falta"}), 400

    titulo       = dados.get("titulo")
    tipo_recurso = dados.get("tipo_recurso") or dados.get("tipoRecurso")
    conteudo     = dados.get("conteudo")

    if conteudo:
        conteudo = conteudo.strip()

    if not titulo or not tipo_recurso or not conteudo:
        return jsonify({"status": "erro", "mensagem": "Todos os campos são obrigatórios."}), 400

    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO modulos (titulo, tipo_recurso, conteudo) VALUES (%s, %s, %s)",
            (titulo, tipo_recurso.lower(), conteudo)
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        return jsonify({"status": "sucesso", "mensagem": f"Módulo '{titulo}' implantado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/admin/editar-modulo', methods=['POST'])
def editar_modulo():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"status": "erro", "mensagem": "Dados em falta"}), 400

        modulo_id = dados.get('id')
        titulo = dados.get('titulo')
        tipo_recurso = dados.get('tipo_recurso') or dados.get('tipoRecurso')
        conteudo = dados.get('conteudo')

        if conteudo:
            conteudo = conteudo.strip()

        if not modulo_id or not titulo or not tipo_recurso or not conteudo:
            return jsonify({"status": "erro", "mensagem": "Todos os campos são obrigatórios para a edição."}), 400

        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE modulos SET titulo = %s, tipo_recurso = %s, conteudo = %s WHERE id = %s",
            (titulo, tipo_recurso.lower(), conteudo, modulo_id)
        )
        conexao.commit()
        cursor.close()
        conexao.close()

        return jsonify({"status": "sucesso", "mensagem": f"Módulo '{titulo}' atualizado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500


@app.route('/api/admin/deletar-modulo', methods=['POST'])
def deletar_modulo():
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Dados em falta"}), 400

    id_modulo = dados.get("id")
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM modulos WHERE id = %s", (id_modulo,))
        conexao.commit()
        cursor.close()
        conexao.close()
        return jsonify({"status": "sucesso", "mensagem": "Módulo removido com sucesso!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


# ── Aluno: Módulos ────────────────────────────────────────────────────────────
@app.route('/api/aluno/listar-modulos', methods=['GET'])
def listar_modulos():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, titulo, tipo_recurso, conteudo FROM modulos ORDER BY id ASC")
        modulos = cursor.fetchall()
        cursor.close()
        conexao.close()
        return jsonify({"status": "sucesso", "modulos": modulos})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500