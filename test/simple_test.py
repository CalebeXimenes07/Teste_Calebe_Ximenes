import pandas as pd
from sqlalchemy import create_engine

def test_db_content():
    engine = create_engine("mysql+mysqlconnector://root:root@localhost:3307/ans_contabil_intuitivecare")
    
    print("Iniciando teste de integridade...")
    try:
        df = pd.read_sql("SELECT COUNT(*) as total FROM estatisticas_operadoras", engine)
        total = df['total'][0]
        
        if total > 0:
            print(f"Sucesso: {total} registros encontrados no banco de dados.")
        else:
            print("Falha: O banco de dados está vazio.")
            
    except Exception as e:
        print(f"Erro ao conectar ou consultar o banco: {e}")

if __name__ == "__main__":
    test_db_content()