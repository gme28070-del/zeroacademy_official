import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Configuração da ligação ao Neon Postgres usando a variável automática da Vercel
DATABASE_URL = os.environ.get("POSTGRES_URL")

def obter_conexao():
    # Adiciona sslmode=require para garantir a ligação segura exigida pelo Neon
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def inicializar_banco():
    """Cria as tabelas iniciais caso não existam no Postgres"""
    conexao = obter_conexao()
    cursor = conexao.cursor()
    
    # Tabela de Alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            usuario VARCHAR(50) UNIQUE NOT NULL,
            senha VARCHAR(100) NOT NULL
        );
    """)
    
    # Tabela de Módulos
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

# Executa a criação das tabelas quando a API inicia
try:
    inicializar_banco()
except Exception as e:
    print(f"Erro ao inicializar o banco de dados: {e}")

# Credenciais temporárias do Administrador
ADMIN_USER = "root"
ADMIN_PASS = "toor"

@app.route('/api/login', methods=['POST'])
def login():
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
        
    return jsonify({"status": "erro", "mensagem": "Credenciais inválidas!"}), 401

@app.route('/api/admin/cadastrar-aluno', methods=['POST'])
def cadastrar_aluno():
    dados = request.get_json()
    nome = dados.get("nome")
    usuario = dados.get("usuario")
    senha = dados.get("senha") # Em produção, o ideal é usar hash (ex: bcrypt), mas vamos simplificar para o teste
    
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
        return jsonify({"status": "sucesso", "mensagem": f"Aluno {nome} registado com sucesso!"})
    except psycopg2.IntegrityError:
        return jsonify({"status": "erro", "mensagem": "Este usuário já existe!"}), 400
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/admin/criar-modulo', methods=['POST'])
def criar_modulo():
    dados = request.get_json()
    titulo = dados.get("titulo")
    tipo_recurso = dados.get("tipo_recurso")
    conteudo = dados.get("conteudo")
    
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO modulos (titulo, tipo_recurso, conteudo) VALUES (%s, %s, %s)",
            (titulo, tipo_recurso, conteudo)
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        return jsonify({"status": "sucesso", "mensagem": f"Módulo '{titulo}' implantado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500