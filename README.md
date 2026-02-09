# Teste Back-end - Análise de Dados ETL

## Como Executar o Projeto

### Pré-requisitos
* Docker e Docker Compose instalados.
* Python 3.10 ou superior.

### Passo a Passo
1. **Subir a Infraestrutura:** No terminal, dentro da pasta do projeto, execute: `docker-compose up -d`. Isso subirá o banco de dados MySQL 8.0 e a interface Adminer.
2. **Instalar Dependências:** Execute o comando: `pip install -r requirements.txt`.
3. **Executar o Processamento (ETL):** Execute: `python main.py`. Este script baixará, tratará e carregará os dados no banco.
4. **Executar a API:** Execute: `python api.py`. O servidor Flask iniciará em `http://localhost:5000`.
5. **Visualizar a Interface:** Abra o arquivo `index.html` diretamente em seu navegador.
6. **Visualizar o Banco (Opcional):** Acesse `http://localhost:8080` (Adminer) com as seguintes credenciais:
   - **Servidor:** mysql_ans | **Usuário:** root | **Senha:** root | **Porta Interna:** 3306 (Porta Externa: 3307)

## Decisões Técnicas e Trade-offs

Conforme solicitado no manual, abaixo estão as justificativas para as escolhas feitas durante o desenvolvimento:

### 1. Módulo 1 e 2: Web Scraping e Processamento
* **Trade-off:** Processamento em Memória x Escrita em Disco.
* **Decisão:** Optei por carregar e consolidar os dados em memória com a biblioteca Pandas.
* **Justificativa:** Como o volume de dados das demonstrações contábeis é significativo, o Pandas oferece uma manipulação de strings e conversão de tipos muito mais eficiente do que iterações manuais em arquivos CSV, garantindo a performance exigida.

### 2. Tratamento de Inconsistências (Pensamento Crítico)
* **Filtragem de Dados:** O script filtra automaticamente as contas de Despesas com Eventos e Sinistros e remove linhas com valores negativos ou campos obrigatórios ausentes.
* **Justificativa:** Dados contábeis brutos apresentam ruídos. A limpeza prévia garante que as estatísticas reflitam a realidade financeira sem distorções por erros de preenchimento.

### 3. Módulo 3: Infraestrutura com Docker
* **Trade-off:** Instalação Local vs. Conteinerização.
* **Decisão:** Uso de Docker Compose para orquestrar o MySQL 8.0 e o Adminer.
* **Justificativa:** Garante a portabilidade. Mapeei a porta externa para 3307 para evitar conflitos com serviços locais de banco de dados no host do avaliador.

### 4. Módulo 4: API e Interface Web (Backend e Frontend)

**Backend:**
* **4.2.1. Escolha do Framework:** Opção A (Flask). Justificativa: Escolhido por sua natureza minimalista e agilidade no setup de APIs RESTful, cumprindo os requisitos de praticidade e fácil manutenção sem o overhead de frameworks mais pesados.
* **4.2.2. Estratégia de Paginação:** Opção A (Offset-based). Justificativa: Considerando que os dados da ANS são históricos e estáveis, a paginação via LIMIT e OFFSET é eficiente e simplifica a implementação tanto no banco quanto no frontend.
* **4.2.3. Cache vs Queries Diretas:** Opção C (Pré-calcular e armazenar em tabela). Justificativa: Os cálculos de despesas são realizados durante o ETL e armazenados na tabela estatisticas_operadoras. Isso elimina o custo computacional de agregados em tempo real na rota /api/estatisticas.
* **4.2.4. Estrutura de Resposta:** Opção B (Dados + metadados). Justificativa: Retornar o total de registros e a página atual permite que o frontend gerencie os componentes de navegação de forma precisa.

**Frontend:**
* **4.3.1. Estratégia de Busca/Filtro:** Opção A (Busca no servidor). Justificativa: Garante que o processamento de grandes volumes de dados ocorra no banco de dados, evitando gargalos de memória e performance no navegador do usuário.
* **4.3.2. Gerenciamento de Estado:** Opção A (Props/Events simples). Justificativa: Dada a baixa complexidade de compartilhamento de dados entre componentes neste projeto, o uso de ferramentas como Pinia ou Vuex seria desnecessário.
* **4.3.3. Performance da Tabela:** Paginação Simples. Justificativa: A renderização de um número controlado de linhas por vez garante uma UX fluida e evita lentidão no processamento do DOM.
* **4.3.4. Tratamento de Erros e Loading:** Implementação de try/catch no Axios e estados reativos de carregamento. Optei por mensagens de erro específicas para facilitar o diagnóstico de falhas de conexão ou dados inexistentes.

### 5. Tipagem no Banco de Dados
* **Uso de DECIMAL(20,2):**
* **Justificativa:** Para campos financeiros, o uso de FLOAT é inadequado. O tipo DECIMAL garante a precisão exata para os centavos em cálculos contábeis de larga escala.

## Estrutura do Projeto
* **main.py:** Script de ETL (Download, Transformação e Carga).
* **api.py:** Servidor Flask com as rotas de API solicitadas.
* **index.html:** Interface web desenvolvida em Vue.js.
* **Teste_Calebe_Ximenes.postman_collection.json:** Coleção com exemplos de requisições e respostas.
* **docker-compose.yml:** Configuração da infraestrutura.
* **requirements.txt:** Dependências do projeto.

Desenvolvido por: Calebe Ximenes
