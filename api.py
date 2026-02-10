from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine
import pandas as pd

app = Flask(__name__)
CORS(app)

engine = create_engine('mysql+pymysql://root:root@localhost:3307/ans_contabil')

@app.route('/api/operadoras', methods=['GET'])
def list_operadoras():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit
    
    # Busca da tabela agregada
    query = f"SELECT CNPJ, RazaoSocial, UF FROM estatisticas_operadoras LIMIT {limit} OFFSET {offset}"
    df = pd.read_sql(query, engine)
    total_result = pd.read_sql("SELECT COUNT(*) as total FROM estatisticas_operadoras", engine)
    total = int(total_result['total'][0]) 
    
    return jsonify({"data": df.to_dict(orient='records'), "total": total, "page": page})

@app.route('/api/operadoras/<cnpj>', methods=['GET'])
def get_operadora(cnpj):
    # Detalhes de uma operadora específica
    query = f"SELECT * FROM estatisticas_operadoras WHERE CNPJ = '{cnpj}'"
    df = pd.read_sql(query, engine)
    return jsonify(df.to_dict(orient='records')[0] if not df.empty else {})

@app.route('/api/operadoras/<cnpj>/despesas', methods=['GET'])
def get_historico(cnpj):
    # Busca da tabela detalhada (Histórico por Trimestre/Ano)
    query = f"SELECT Ano, Trimestre, ValorDespesas FROM despesas_detalhadas WHERE CNPJ = '{cnpj}' ORDER BY Ano, Trimestre"
    df = pd.read_sql(query, engine)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/estatisticas', methods=['GET'])
def get_stats():
    # Top 5 operadoras por despesa total
    query = "SELECT RazaoSocial, Total_Despesas, UF FROM estatisticas_operadoras ORDER BY Total_Despesas DESC LIMIT 5"
    df = pd.read_sql(query, engine)
    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=False, port=5000)
