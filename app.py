import json
from flask import Flask, jsonify, request, render_template, Response

app = Flask(__name__)
app.json.ensure_ascii = False  # mantém acentos no JSON

# ---------------------------------------------------------------------------
# Base de dados em memória (os valores de população são estimativas aproximadas
# do IBGE; confira/atualize se precisar de números oficiais).
# ---------------------------------------------------------------------------
municipios_nordeste_dataset = {
    "metadados": {
        "regiao": "Nordeste",
        "pais": "Brasil",
        "total_municipios": 30,
        "fonte_dados_populacao": "IBGE",
    },
    "municipios": {
        "Fortaleza": {"id_ibge": 2304400, "estado": "Ceará", "sigla_uf": "CE", "capital": True, "populacao_estimada": 2582360},
        "Salvador": {"id_ibge": 2927408, "estado": "Bahia", "sigla_uf": "BA", "capital": True, "populacao_estimada": 2559945},
        "São Luís": {"id_ibge": 2111300, "estado": "Maranhão", "sigla_uf": "MA", "capital": True, "populacao_estimada": 1115932},
        "Teresina": {"id_ibge": 2211001, "estado": "Piauí", "sigla_uf": "PI", "capital": True, "populacao_estimada": 871126},
        "Natal": {"id_ibge": 2408102, "estado": "Rio Grande do Norte", "sigla_uf": "RN", "capital": True, "populacao_estimada": 896708},
        "João Pessoa": {"id_ibge": 2507507, "estado": "Paraíba", "sigla_uf": "PB", "capital": True, "populacao_estimada": 825796},
        "Recife": {"id_ibge": 2611606, "estado": "Pernambuco", "sigla_uf": "PE", "capital": True, "populacao_estimada": 1661017},
        "Maceió": {"id_ibge": 2704302, "estado": "Alagoas", "sigla_uf": "AL", "capital": True, "populacao_estimada": 957916},
        "Aracaju": {"id_ibge": 2800308, "estado": "Sergipe", "sigla_uf": "SE", "capital": True, "populacao_estimada": 664908},
        "Juazeiro do Norte": {"id_ibge": 2307304, "estado": "Ceará", "sigla_uf": "CE", "capital": False, "populacao_estimada": 276264},
        "Sobral": {"id_ibge": 2312908, "estado": "Ceará", "sigla_uf": "CE", "capital": False, "populacao_estimada": 212437},
        "Caucaia": {"id_ibge": 2303709, "estado": "Ceará", "sigla_uf": "CE", "capital": False, "populacao_estimada": 368918},
        "Feira de Santana": {"id_ibge": 2910800, "estado": "Bahia", "sigla_uf": "BA", "capital": False, "populacao_estimada": 624107},
        "Vitória da Conquista": {"id_ibge": 2933307, "estado": "Bahia", "sigla_uf": "BA", "capital": False, "populacao_estimada": 343643},
        "Camaçari": {"id_ibge": 2905701, "estado": "Bahia", "sigla_uf": "BA", "capital": False, "populacao_estimada": 304302},
        "Juazeiro": {"id_ibge": 2918407, "estado": "Bahia", "sigla_uf": "BA", "capital": False, "populacao_estimada": 237821},
        "Imperatriz": {"id_ibge": 2105302, "estado": "Maranhão", "sigla_uf": "MA", "capital": False, "populacao_estimada": 259980},
        "Caxias": {"id_ibge": 2103000, "estado": "Maranhão", "sigla_uf": "MA", "capital": False, "populacao_estimada": 165525},
        "Timon": {"id_ibge": 2112209, "estado": "Maranhão", "sigla_uf": "MA", "capital": False, "populacao_estimada": 174465},
        "Parnaíba": {"id_ibge": 2207702, "estado": "Piauí", "sigla_uf": "PI", "capital": False, "populacao_estimada": 153482},
        "Picos": {"id_ibge": 2208007, "estado": "Piauí", "sigla_uf": "PI", "capital": False, "populacao_estimada": 83090},
        "Mossoró": {"id_ibge": 2408003, "estado": "Rio Grande do Norte", "sigla_uf": "RN", "capital": False, "populacao_estimada": 264577},
        "Parnamirim": {"id_ibge": 2403251, "estado": "Rio Grande do Norte", "sigla_uf": "RN", "capital": False, "populacao_estimada": 267036},
        "Campina Grande": {"id_ibge": 2504009, "estado": "Paraíba", "sigla_uf": "PB", "capital": False, "populacao_estimada": 413830},
        "Olinda": {"id_ibge": 2609600, "estado": "Pernambuco", "sigla_uf": "PE", "capital": False, "populacao_estimada": 393115},
        "Jaboatão dos Guararapes": {"id_ibge": 2607901, "estado": "Pernambuco", "sigla_uf": "PE", "capital": False, "populacao_estimada": 706867},
        "Caruaru": {"id_ibge": 2604106, "estado": "Pernambuco", "sigla_uf": "PE", "capital": False, "populacao_estimada": 369343},
        "Petrolina": {"id_ibge": 2611101, "estado": "Pernambuco", "sigla_uf": "PE", "capital": False, "populacao_estimada": 354317},
        "Arapiraca": {"id_ibge": 2700300, "estado": "Alagoas", "sigla_uf": "AL", "capital": False, "populacao_estimada": 234696},
        "Nossa Senhora do Socorro": {"id_ibge": 2804805, "estado": "Sergipe", "sigla_uf": "SE", "capital": False, "populacao_estimada": 187733},
    },
}

CAMPOS_OBRIGATORIOS = ["id_ibge", "estado", "sigla_uf", "capital", "populacao_estimada"]
CAMPOS_PERMITIDOS = set(CAMPOS_OBRIGATORIOS)


def municipios():
    return municipios_nordeste_dataset["municipios"]


def atualizar_total():
    municipios_nordeste_dataset["metadados"]["total_municipios"] = len(municipios())


def normalizar(dados):
    """Converte os tipos dos campos recebidos. Lança ValueError se inválido."""
    saida = {}
    if "id_ibge" in dados:
        saida["id_ibge"] = int(dados["id_ibge"])
    if "populacao_estimada" in dados:
        saida["populacao_estimada"] = int(dados["populacao_estimada"])
    if "estado" in dados:
        saida["estado"] = str(dados["estado"]).strip()
    if "sigla_uf" in dados:
        saida["sigla_uf"] = str(dados["sigla_uf"]).strip().upper()
    if "capital" in dados:
        valor = dados["capital"]
        saida["capital"] = valor if isinstance(valor, bool) else str(valor).lower() in ("true", "1", "sim", "on")
    return saida


# ---------------------------------------------------------------------------
# Página HTML
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", metadados=municipios_nordeste_dataset["metadados"])


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/municipios", methods=["GET"])
def listar_municipios():
    uf = request.args.get("uf")
    if uf:
        filtrados = {
            nome: dados
            for nome, dados in municipios().items()
            if dados["sigla_uf"].upper() == uf.strip().upper()
        }
        return jsonify(filtrados)
    return jsonify(municipios())


@app.route("/municipios/<nome>", methods=["GET"])
def consultar_municipio(nome):
    if nome not in municipios():
        return jsonify({"erro": f"Município '{nome}' não encontrado."}), 404
    return jsonify({nome: municipios()[nome]})


@app.route("/municipios", methods=["POST"])
def cadastrar_municipio():
    corpo = request.get_json(silent=True)
    if not corpo:
        return jsonify({"erro": "Envie um JSON válido."}), 400

    nome = str(corpo.get("nome", "")).strip()
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório."}), 400
    if nome in municipios():
        return jsonify({"erro": f"Município '{nome}' já cadastrado."}), 409

    faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in corpo]
    if faltando:
        return jsonify({"erro": "Campos obrigatórios ausentes.", "campos": faltando}), 400

    try:
        municipios()[nome] = normalizar(corpo)
    except (ValueError, TypeError):
        return jsonify({"erro": "Valores numéricos inválidos."}), 400

    atualizar_total()
    return jsonify({"mensagem": "Município cadastrado.", nome: municipios()[nome]}), 201


@app.route("/municipios/<nome>", methods=["PATCH"])
def atualizar_municipio(nome):
    if nome not in municipios():
        return jsonify({"erro": f"Município '{nome}' não encontrado."}), 404

    corpo = request.get_json(silent=True)
    if not corpo:
        return jsonify({"erro": "Envie um JSON válido."}), 400

    try:
        novos = normalizar({k: v for k, v in corpo.items() if k in CAMPOS_PERMITIDOS})
    except (ValueError, TypeError):
        return jsonify({"erro": "Valores numéricos inválidos."}), 400

    municipios()[nome].update(novos)
    return jsonify({"mensagem": "Município atualizado.", nome: municipios()[nome]})


@app.route("/municipios/<nome>", methods=["DELETE"])
def excluir_municipio(nome):
    if nome not in municipios():
        return jsonify({"erro": f"Município '{nome}' não encontrado."}), 404
    municipios().pop(nome)
    atualizar_total()
    return jsonify({"mensagem": f"Município '{nome}' removido."})


@app.route("/exportar-json", methods=["GET"])
def exportar_json():
    conteudo = json.dumps(municipios(), ensure_ascii=False, indent=2)
    return Response(
        conteudo,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=municipios_nordeste.json"},
    )


if __name__ == "__main__":
    app.run(debug=True)
