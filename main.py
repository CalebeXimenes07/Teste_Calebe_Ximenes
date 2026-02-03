"""
Script de ETL - Teste Técnico Estágio Intuitive Care
Autor: Calebe Ximenes
Objetivo: Extrair, transformar e carregar dados contábeis da API  ANS.

"""

import os
import requests
import zipfile
import pandas as pd
import io
import sqlalchemy
import pymysql
from sqlalchemy import create_engine, types
import cryptography
from urllib.parse import urljoin

URL_API_ANS = 'https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/'
API_ANS = requests.get(URL_API_ANS)
PASTA_DESTINO = "ansdata"

if API_ANS.status_code == 200:
    print("Localizando repositório mais recente")
    tabelas = pd.read_html(io.StringIO(API_ANS.text))
    df = tabelas[0]
    
    # Busca dentro da API apenas os diretórios que seja o ano mais recente para que o código não fique obsoleto futuramente.
    df_anos = df[df['Name'].str.contains(r'^\d{4}/', na=False)].copy()
    df_anos = df_anos.sort_values(by='Name', ascending=False)
    ultimo_ano = df_anos.iloc[0]['Name']
    
NOVA_URL = urljoin(URL_API_ANS, ultimo_ano)
NOVA_API_ANS = requests.get(NOVA_URL)

if NOVA_API_ANS.status_code == 200:
    lista_final = []
    tabela_zips = pd.read_html(io.StringIO(NOVA_API_ANS.text))
    df_zips = tabela_zips[0]
    df_trimestres = df_zips[df_zips['Name'].str.contains(r'.*\.zip$', na=False, case=False)].copy()
    df_trimestres = df_trimestres.sort_values(by='Name', ascending=False)
     
    df_para_baixar = df_trimestres.head(3)
    
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    
    if not df_para_baixar.empty:
        for nome_arquivo in df_para_baixar['Name']:
            nome_arquivo = nome_arquivo.strip()
            caminho = os.path.join(PASTA_DESTINO, nome_arquivo)
            
            if not os.path.exists(caminho):
                url_download = urljoin(NOVA_URL, nome_arquivo)
                download = requests.get(url_download)
                if download.status_code == 200:
                    with open(caminho, "wb") as arquivo:
                        arquivo.write(download.content)
                        print(f"{nome_arquivo} baixado com sucesso.")
                else:
                    print(f"Erro ao baixar: {nome_arquivo}")
            else:
                        print(f"Arquivo {nome_arquivo} já está baixado.")        
    else:
        print("Não há arquivos a serem baixados.")
    
    nome_saida_consolidado = "consolidado_despesas.csv"
    caminho_final_consolidado = os.path.join(PASTA_DESTINO, nome_saida_consolidado)
    
    # Pula o reprocessamento lento dos arquivos ZIP se o CSV consolidado já tiver sido criado
    if os.path.exists(caminho_final_consolidado):
        print("Arquivo consolidado já existe, pulando processamento de CSV...")
    
    else:
        for arquivo_zip in os.listdir(PASTA_DESTINO):
            pasta_zips = os.path.join(PASTA_DESTINO, arquivo_zip)
            if arquivo_zip.endswith('.zip'):
                with zipfile.ZipFile(pasta_zips, 'r') as ziparch:
                    arquivos_internos = ziparch.namelist()
                    
                    # Unifica as colunas de arquivos CSV, TXT e XLSX em um mapa padronizado
                    MAPA_DE_COLUNAS = {
                        'DATA': 'DataOrigem',
                        'REG_ANS': 'CNPJ', # REG_ANS usado como ID temporariamente até o enriquecimento ser feito
                        'DESCRICAO': 'RazaoSocial',
                        'VL_SALDO_FINAL': 'ValorDespesas'
                    }

                    
                    for arq_int in arquivos_internos:    
                        if arq_int.lower().endswith(('.csv', '.txt', '.xlsx')):
                            with ziparch.open(arq_int) as x:
                                
                                if arq_int.lower().endswith(('.csv', '.txt')):
                                    df_trimestres = pd.read_csv(x, sep=None, engine='python', encoding='utf-8')
                            
                                elif arq_int.lower().endswith('.xlsx'):
                                    df_trimestres = pd.read_excel(x)
                                        
                                df_trimestres.columns = [col.upper().strip() for col in df_trimestres.columns]
                                df_trimestres = df_trimestres.rename(columns=MAPA_DE_COLUNAS)

                                # Filtra apenas contas do grupo 4 (Despesas com eventos/sinistros), de acordo com padrão da ANS
                                if 'CD_CONTA_CONTABIL' in df_trimestres.columns:
                                    df_trimestres = df_trimestres[df_trimestres['CD_CONTA_CONTABIL'].astype(str).str.startswith('4')]
                                    
                                df_trimestres['DataOrigem'] = pd.to_datetime(df_trimestres['DataOrigem'],errors='coerce')

                                df_trimestres['Ano'] = df_trimestres['DataOrigem'].dt.year
                                df_trimestres['Trimestre'] = df_trimestres['DataOrigem'].dt.quarter

                                # Faz o tratamento do separador decimal brasileiro (vírgula) e converte para float para realizar cálculos sem erro
                                df_trimestres['ValorDespesas'] = pd.to_numeric(
                                    df_trimestres['ValorDespesas'].astype(str).str.replace(',', '.').str.strip(), 
                                    errors='coerce'
                                )
                                
                                # Remove linhas com valores zerados, negativos ou campos obrigatórios nulos
                                df_trimestres = df_trimestres.dropna(subset=['CNPJ', 'RazaoSocial' ,'ValorDespesas'])
                                df_trimestres = df_trimestres[df_trimestres['ValorDespesas'] > 0].copy()

                                colunas_finais = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']
                                df_limpo = df_trimestres[[c for c in colunas_finais if c in df_trimestres.columns]]

                                lista_final.append(df_limpo)

                                print(f"Lido: {arq_int}")
                                
                                
        if lista_final:
            df_final = pd.concat(lista_final, ignore_index=True)
            nome_zip_consolidado = "consolidado_despesas.zip"
            caminho_zip = os.path.join(PASTA_DESTINO, nome_zip_consolidado)
            df_final.to_csv((caminho_final_consolidado), index=False, sep=';', encoding='utf-8')
            with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                
                # Na compactação o arcname evita que o ZIP considere pastas do sistema, mantendo apenas o arquivo
                zf.write(caminho_final_consolidado, arcname=nome_saida_consolidado)
                print(f"Arquivo {nome_saida_consolidado} compactado no ZIP: {nome_zip_consolidado} com sucesso.")
                
URL_DADOS_CADASTRAIS = 'https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/'
DADOS_CADASTRAIS_ANS = requests.get(URL_DADOS_CADASTRAIS)

if DADOS_CADASTRAIS_ANS.status_code == 200:
    print("API de Dados Cadastrais conectada com sucesso.")
    tabela_dados_cadastrais = pd.read_html(io.StringIO(DADOS_CADASTRAIS_ANS.text))
    df_lista_arquivos = tabela_dados_cadastrais[0]
    filtro_cadastral = df_lista_arquivos[df_lista_arquivos['Name'].str.endswith('.csv', na=False)]
    
    if not filtro_cadastral.empty:
        nome_arquivo_cadastral = filtro_cadastral.iloc[0]['Name'].strip()
        caminho_arquivo_cadastral = os.path.join(PASTA_DESTINO, nome_arquivo_cadastral)
        url_download_dados_cadastrais = urljoin(URL_DADOS_CADASTRAIS, nome_arquivo_cadastral)
        
        if not os.path.exists(caminho_arquivo_cadastral):
            print("Baixando cadastro das operadoras..")
            conteudo_cadastral = requests.get(url_download_dados_cadastrais).content
            with open (caminho_arquivo_cadastral, 'wb') as x:
                x.write(conteudo_cadastral)
                
    df_cadastral = pd.read_csv(caminho_arquivo_cadastral, sep=';', encoding='utf-8', on_bad_lines='skip')
    df_consolidado = pd.read_csv(caminho_final_consolidado, sep=';', encoding='utf-8', on_bad_lines='skip')    
    df_cadastral.columns = [col.upper().strip() for col in df_cadastral.columns]      

    df_consolidado = df_consolidado.rename(columns={'CNPJ': 'REGISTRO_OPERADORA'})

    df_final = pd.merge(df_consolidado, df_cadastral[['REGISTRO_OPERADORA', 'CNPJ', 'UF', 'RAZAO_SOCIAL']], on='REGISTRO_OPERADORA', how='left')
    df_final['CNPJ'] = df_final['CNPJ'].fillna(0).astype(int).astype(str).str.zfill(14)
    df_final['RazaoSocial'] = df_final['RAZAO_SOCIAL']
    
    # Apagando o registro e deixando apenas o CNPJ
    df_final = df_final.drop(columns=['REGISTRO_OPERADORA', 'RAZAO_SOCIAL'])

    nome_arquivo_consolidado = 'arquivo_consolidado_enriquecido.csv'
    caminho_dados_enriquecidos = os.path.join(PASTA_DESTINO, nome_arquivo_consolidado)
    df_final.to_csv(caminho_dados_enriquecidos, index=False, sep=';', encoding='utf-8')

    df_para_estatisticas = df_final.dropna(subset=['UF'])

    

    df_estatisticas_agregadas = df_para_estatisticas.groupby(['CNPJ','RazaoSocial', 'UF']).agg(
    Total_Despesas=('ValorDespesas', 'sum'),
    Media_Trimestral=('ValorDespesas', 'mean'),
    Desvio_Padrao_Variabilidade=('ValorDespesas', 'std')
    ).reset_index()
    df_estatisticas_agregadas = df_estatisticas_agregadas.sort_values(by='Total_Despesas', ascending=False)
    
    nome_agregado = 'despesas_agregadas.csv'
    caminho_nome_agregado = os.path.join(PASTA_DESTINO, nome_agregado)
    df_estatisticas_agregadas.to_csv(caminho_nome_agregado, index=False, sep=';', encoding='utf-8')

# A porta escolhida foi a 3307 para evitar conflito caso tenha algum banco internamente instalado
engine = create_engine('mysql+pymysql://root:root@localhost:3307/ans_contabil_intuitivecare')

dtype_mapa_agregado = {
    'CNPJ': types.CHAR(length=14), 
    'RazaoSocial': types.VARCHAR(length=255),
    'UF': types.CHAR(length=2),
    'Total_Despesas': types.DECIMAL(precision=20, scale=2),
    'Media_Trimestral': types.DECIMAL(precision=20, scale=2),
    'Desvio_Padrao_Variabilidade': types.DECIMAL(precision=20, scale=2)
}

dtype_mapa_consolidado = {
    'CNPJ': types.CHAR(length=14),
    'RazaoSocial': types.VARCHAR(length=255),
    'Trimestre': types.Integer(),
    'Ano': types.Integer(),
    'ValorDespesas': types.DECIMAL(precision=20, scale=2)
}

print("Carregando no banco de dados")

try:
    df_estatisticas_agregadas.to_sql(
        name='estatisticas_operadoras',
        con=engine,
        if_exists='replace',
        index=False,
        dtype=dtype_mapa_agregado,
        chunksize=1000        
    )
    print("Tabela: estatisticas_operadoras criada com sucesso!")
    
    df_final.to_sql(
        name='despesas_detalhadas', 
        con=engine, 
        if_exists='replace', 
        index=False,
        dtype=dtype_mapa_consolidado,
        chunksize=1000
    )
    print("Tabela despesas_detalhadas criada com sucesso!")
    
    with engine.connect() as connection:
        from sqlalchemy import text
        res = connection.execute(text("SELECT COUNT(*) FROM estatisticas_operadoras")).fetchone()
        print(f"\nSucesso!")
        print(f"Total de registros inseridos: {res[0]}")

except Exception as e:
    print(f"Erro na integração com o Banco: {e}")
    print("Verifique se o Docker está rodando com 'docker-compose up -d'")

