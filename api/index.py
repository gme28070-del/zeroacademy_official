from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/dados', methods=['GET'])
def obter_dados():
    return jsonify({
        "status": "sucesso",
        "mensagem": "Conexão estabelecida com o backend!"
    })