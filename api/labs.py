import psycopg2
from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor

# Criamos o Blueprint para isolar as rotas dos laboratórios
labs_bp = Blueprint("labs", __name__)

# Banco de dados de flags estáticas no servidor (protegido contra F12)
FLAGS_DESAFIOS = {
    "powershell_bandit": "FLAG{PS_N4T1V0_M4ST3R_2026}",
}


@labs_bp.route("/api/labs/validar-flag", methods=["POST"])
def validar_flag():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"status": "erro", "mensagem": "Dados em falta"}), 400

        desafio = dados.get("desafio")
        flag_enviada = dados.get("flag")

        if not desafio or not flag_enviada:
            return (
                jsonify(
                    {"status": "erro", "mensagem": "Campos obrigatórios ausentes."}
                ),
                400,
            )

        flag_correta = FLAGS_DESAFIOS.get(desafio)

        if not flag_correta:
            return (
                jsonify({"status": "erro", "mensagem": "Desafio não encontrado."}),
                404,
            )

        if flag_enviada.strip() == flag_correta:
            return jsonify(
                {
                    "status": "sucesso",
                    "mensagem": "ACESSO CONCEDIDO! Flag correta. Comandos dominados com sucesso!",
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "erro",
                        "mensagem": "ACESSO NEGADO! Flag incorreta, inspecione melhor o ambiente.",
                    }
                ),
                403,
            )

    except Exception as e:
        return (
            jsonify({"status": "erro", "mensagem": f"Erro no servidor: {str(e)}"}),
            500,
        )