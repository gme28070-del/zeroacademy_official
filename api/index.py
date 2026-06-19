from flask import Flask, request, jsonify

app = Flask(__name__)

# Usuário administrador temporário para testes
ADMIN_USER = "root"
ADMIN_PASS = "toor"  # Altere para a senha que desejar

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Dados não enviados"}), 400
        
    usuario = dados.get("username")
    senha = dados.get("password")
    
    # Verifica se é o administrador
    if usuario == ADMIN_USER and senha == ADMIN_PASS:
        return jsonify({
            "status": "sucesso",
            "tipo": "admin",
            "mensagem": "Autenticado como Administrador!",
            "redirecionar": "/admin-dashboard.html" # Página que criaremos depois
        })
        
    # Se não for o admin, por enquanto retorna erro (depois buscaremos os alunos aqui)
    return jsonify({"status": "erro", "mensagem": "Credenciais inválidas!"}), 401