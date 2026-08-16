# Sistema de Gestão Integrada para Vending Machines

Uma solução de dados end-to-end desenvolvida para otimizar a gestão de stock, a telemetria e a logística de reabastecimento de uma rede de máquinas de venda automática (VendingPLUS). O projeto abrange desde a modelação da base de dados relacional até à visualização de métricas de negócio, passando pela automatização de regras complexas de roteamento logístico.

### 🛠️ Tecnologias e Ferramentas
*   **Base de Dados:** Oracle SQL, PL/SQL
*   **Integração de Dados:** Python (ETL)
*   **Business Intelligence:** Microsoft Power BI

### ⚙️ Arquitetura e Funcionalidades Core
1. **Modelação e Telemetria (Oracle SQL):**
   * Modelação ER e esquema físico focado na gestão de máquinas, compartimentos de produtos, armazéns logísticos e pagamentos digitais.
   * Criação de *views* complexas (ex: monitorização temporal de reabastecimentos, alertas de máquinas offline e deteção de anomalias de consumo).

2. **Automatização e Lógica de Negócio (PL/SQL):**
   * **Triggers:** Atualização automática de volumes de stock pós-venda, prevenção de abastecimentos inválidos e alertas de rutura crítica de produtos.
   * **Functions & Procedures:** Algoritmos de cálculo de distância linear (geolocalização) para planear rotas de reabastecimento de veículos elétricos e identificar a máquina com stock mais próxima do utilizador.

3. **Pipeline de Dados e Analytics:**
   * Script `ETL.py` desenvolvido para extração, transformação e carregamento dos dados transacionais e logísticos.
   * `Dashboard.pbix` iterativo em Power BI para exploração visual de vendas mensais, eficiência das rotas de veículos e estado operacional das máquinas.

### 📂 Estrutura do Repositório
*   `/SI2/SQL.txt`: Scripts DDL e DML da base de dados, bem como todas as *Views* e rotinas PL/SQL (Funções, Procedimentos e Triggers).
*   `/SI2/ETL.py`: Pipeline Python para processamento dos dados.
*   `/SI2/Dashboard.pbix`: Dashboard analítico de visualização de dados.
*   `/SI2/relatorio.pdf`: Documentação exaustiva da arquitetura e cálculos de parâmetros físicos.
*   `/SI2/Apresentação.pdf`: Apresentação visual da solução desenvolvida.
