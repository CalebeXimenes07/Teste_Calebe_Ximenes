# Projeto de Análise de Dados ANS (ETL + Docker)

Este projeto consiste em uma solução completa de Engenharia de Dados e Backend para processamento, análise e visualização de dados contábeis públicos da ANS (Agência Nacional de Saúde Suplementar).

O pipeline realiza a extração automática (ETL), tratamento de inconsistências financeiras e disponibilização dos dados via API REST e Dashboard Interativo, tudo orquestrado via Docker para garantir reprodutibilidade.

## Como Executar o Projeto

### Pré-requisitos
* Docker e Docker Compose instalados.
* Python 3.10 ou superior.
* Git.

### Instalação
Clone este repositório para sua máquina local:

```bash
git clone https://github.com/CalebeXimenes07/Teste_Calebe_Ximenes.git
cd Teste_Calebe_Ximenes
```

### Passo a Passo

1. **Subir a Infraestrutura**
   No terminal, dentro da pasta do projeto, execute o comando abaixo. Isso subirá o banco de dados MySQL 8.0 e a interface de gerenciamento Adminer.
   ```bash
   docker-compose up -d
   ```

2. **Instalar Dependências**
   Instale as bibliotecas Python necessárias listadas no requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

3. **Executar o Processamento (ETL)**
   Execute o script principal. Ele baixará os dados brutos, tratará as inconsistências e carregará as informações limpas no banco de dados.
   ```bash
   python main.py
   ```

4. **Executar a API**
   Inicie o servidor Flask:
   ```bash
   python api.py
   ```
   O servidor iniciará em http://localhost:5000.

5. **Visualizar a Interface**
   Abra o arquivo `index.html` diretamente em seu navegador para interagir com o Dashboard.

6. **Visualizar o Banco (Opcional)**
   Acesse http://localhost:8080 (Adminer) com as seguintes credenciais:
   * Servidor: mysql_ans
   * Usuário: root
   * Senha: root
   * Porta Interna: 3306 (Porta Externa: 3307)

---

## Decisões Técnicas e Arquitetura

Abaixo estão as justificativas para as escolhas técnicas adotadas durante o desenvolvimento visando performance, escalabilidade e governança de dados.

### 1. Processamento e Web Scraping
* Decisão: Processamento em memória com Pandas.
* Justificativa: Dado o volume significativo das demonstrações contábeis, o Pandas oferece vetorialização eficiente para limpeza de strings e conversão de tipos, superando a performance de iterações manuais em arquivos CSV.

### 2. Qualidade de Dados (Data Quality)
* Decisão: Filtragem automática na camada de ETL.
* Justificativa: O script remove automaticamente linhas com valores negativos inválidos ou campos obrigatórios ausentes. Isso garante que as estatísticas reflitam a realidade financeira sem distorções (Saneamento na origem).

### 3. Infraestrutura como Código
* Decisão: Orquestração via Docker Compose.
* Justificativa: Garante a imutabilidade do ambiente. O uso de containers elimina o problema de "funciona na minha máquina", padronizando a versão do banco de dados (MySQL 8.0) independente do sistema operacional do host. A porta 3307 foi mapeada para evitar conflitos locais.

### 4. API e Backend
* Framework: Flask. Escolhido pela arquitetura minimalista e baixo overhead para microsserviços.
* Estratégia de Performance: Pré-cálculo. Os dados agregados (somas e médias por operadora) são processados durante o ETL e persistidos na tabela estatisticas_operadoras. A API apenas lê o resultado pronto, reduzindo a latência da resposta para o frontend.
* Paginação: Offset-based, ideal para dados históricos e estáveis.

### 5. Tipagem no Banco de Dados
* Decisão: Uso de DECIMAL(20,2) para valores monetários.
* Justificativa: O tipo FLOAT pode introduzir erros de arredondamento em somas financeiras grandes. O DECIMAL garante a precisão exata dos centavos exigida em sistemas contábeis/bancários.

---

## Estrutura do Projeto

* main.py: Script principal de ETL (Extração, Transformação e Carga).
* api.py: Servidor Flask com endpoints RESTful.
* index.html: Interface web desenvolvida em Vue.js (Consumo da API).
* ans_api_collection.json: Coleção do Postman para testes de integração.
* docker-compose.yml: Definição da infraestrutura.
* requirements.txt: Lista de dependências do Python.

---
Desenvolvido por: Calebe Ximenes
