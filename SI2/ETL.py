import os
import sys
import mysql.connector as mysql
import pyodbc
import csv
from datetime import datetime


TAXA_CAMBIO_USD_EUR = 0.95  

# MySQL 
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PWD  = os.getenv("MYSQL_PWD",  "Pitucho15122005!") 
MYSQL_DB   = os.getenv("MYSQL_DB",   "tp_g2")             

# SQL Server 
MSSQL_HOST   = os.getenv("MSSQL_HOST", "localhost")
MSSQL_PORT   = int(os.getenv("MSSQL_PORT", "1433"))
MSSQL_USER   = os.getenv("MSSQL_USER", "sa")
MSSQL_PWD    = os.getenv("MSSQL_PWD",  "Pitucho15122005!")  
MSSQL_DB     = os.getenv("MSSQL_DB",   "Trabalho")          
MSSQL_DRIVER = os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")

CSV_FILE_PATH = r"C:\Users\joaop\Desktop\ISEC\SI2\Trabalho Pratica\dados_atualizado.csv"


# LIGAÇÕES
def get_mysql_conn():
    return mysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PWD,
        database=MYSQL_DB, autocommit=True, charset="utf8mb4"
    )

def get_mssql_conn():
    conn_str = (
        f"DRIVER={{{MSSQL_DRIVER}}};SERVER={MSSQL_HOST},{MSSQL_PORT};"
        f"DATABASE={MSSQL_DB};UID={MSSQL_USER};PWD={MSSQL_PWD};"
        f"TrustServerCertificate=Yes;"
    )
    return pyodbc.connect(conn_str)

# DIMENSÕES
def get_or_create_dim_tempo(cur, data_chegada):
    if isinstance(data_chegada, datetime):
        data_chegada = data_chegada.date()
        
    cur.execute("SELECT id_data FROM dim_data WHERE data = ?", (data_chegada,))
    row = cur.fetchone()
    if row:
        return row[0]

    id_data_sk = int(data_chegada.strftime('%Y%m%d'))
    
    dia = data_chegada.day
    mes = data_chegada.month
    ano = data_chegada.year
    nome_mes = data_chegada.strftime('%B') 
    
    trimestre = (mes - 1) // 3 + 1
    semestre = 1 if mes <= 6 else 2

    cur.execute("SELECT id_data FROM dim_data WHERE id_data = ?", (id_data_sk,))
    if cur.fetchone():
        return id_data_sk

    cur.execute("""
        INSERT INTO dim_data (id_data, data, ano, mes, dia, nome_mes, trimestre, semestre)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (id_data_sk, data_chegada, ano, mes, dia, nome_mes, trimestre, semestre))
    
    return id_data_sk

def get_or_create_dim_barco(cur, barco):
    cur.execute("SELECT id_barco FROM dim_barco WHERE nome_barco = ? AND tipo_barco = ?", 
                (barco["nome"], barco["tipo"]))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO dim_barco (nome_barco, tipo_barco, empresa_barco, tamanho)
        VALUES (?, ?, ?, ?)
    """, (barco["nome"], barco["tipo"], barco["empresa"], barco["tamanho"]))
    
    cur.execute("SELECT @@IDENTITY") 
    return cur.fetchone()[0]

def get_or_create_dim_condutor(cur, condutor):
    cur.execute("SELECT id_condutor FROM dim_condutor WHERE nome_condutor = ? AND certificacao = ?", 
                (condutor["nome"], condutor["certificacao"]))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO dim_condutor (nome_condutor, certificacao, idade, genero)
        VALUES (?, ?, ?, ?)
    """, (condutor["nome"], condutor["certificacao"], condutor["idade"], condutor["genero"]))
    
    cur.execute("SELECT @@IDENTITY")
    return cur.fetchone()[0]

def get_or_create_dim_localizacao(cur, local):
    cur.execute("SELECT id_localizacao FROM dim_localizacao WHERE cidade = ? AND pais = ?", 
                (local["cidade"], local["pais"]))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO dim_localizacao (nome_porto, cidade, pais)
        VALUES (?, ?, ?)
    """, (local["porto"], local["cidade"], local["pais"]))
    
    cur.execute("SELECT @@IDENTITY")
    return cur.fetchone()[0]

# LEITURA DO CSV
def carregar_dados_csv():
    dados_csv = {}
    print(f"A carregar CSV de: {CSV_FILE_PATH}")
    
    try:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';') 
            
            for row in reader:
                try:
                    id_viagem = int(row['idviagem'])
                    
                    sexo_raw = row['sexo'].lower().strip()
                    genero = 'H' if sexo_raw == 'h' else 'M' if sexo_raw == 'm' else 'O'

                    taxa = float(row['taxa'].replace(',', '.'))
                    peso = float(row['peso'].replace(',', '.'))
                    teu_total = float(row.get('capacidadeteu', 0))

                    dados_csv[id_viagem] = {
                        'receita_taxas': taxa,
                        'num_contentores': int(row['numerocontentares']),
                        'peso_total': peso,
                        'teu_total': teu_total,
                        'genero_condutor': genero
                    }
                except ValueError:
                    continue 
                    
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: Não encontrei o ficheiro no caminho: {CSV_FILE_PATH}")
        sys.exit()
    
    print(f"CSV carregado. {len(dados_csv)} registos prontos.")
    return dados_csv

# MAIN 
def main():
    metricas_viagens = carregar_dados_csv()

    print("2 - A ligar às Bases de Dados...")
    try:
        mysql_conn  = get_mysql_conn()
        sqlsrv_conn = get_mssql_conn() 
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return

    try:
        mysql_cur = mysql_conn.cursor(dictionary=True)
        sqlsrv_cur = sqlsrv_conn.cursor()

        print("3 - A consultar viagens no MySQL...")
        
        mysql_cur.execute("""
            SELECT 
                v.idviagem,
                v.datachegada,
                v.datapartida,
                v.tipoviagem,
                b.nomebarco,
                b.tipobarco,
                b.tamanhobarco,
                emp.nomeempresabarco,
                c.nomecondutor,
                c.certificacao,
                c.idadecondutor,
                lo.cidade as cidade_origem,
                lo.pais as pais_origem,
                'Porto de ' + lo.cidade as nome_porto_origem

            FROM viagem v
            JOIN barco b ON v.barco_idbarco = b.idbarco
            JOIN empresabarco emp ON b.empresabarco_idempresabarco = emp.idempresabarco
            JOIN condutor c ON v.condutor_idcondutor = c.idcondutor
            JOIN localizacao lo ON v.localizacao_idlocalizacao = lo.idlocalizacao
            JOIN localizacao ld ON v.localizacao_idlocalizacao1 = ld.idlocalizacao 
            
            WHERE v.status = 'concluida' 
              AND (ld.cidade = 'figfoz' OR ld.cidade LIKE '%Figueira%')
        """)

        rows = mysql_cur.fetchall()
        print(f"Viagens encontradas no MySQL para processar: {len(rows)}")

        if len(rows) == 0:
            print("ERRO: Nenhuma viagem encontrada. Confirma se tens dados na BD 'tp_g2'.")
            return

        count_inseridos = 0

        for r in rows:
            id_viagem_mysql = r['idviagem']
            if id_viagem_mysql not in metricas_viagens:
                continue

            metricas = metricas_viagens[id_viagem_mysql]

            id_tempo = get_or_create_dim_tempo(sqlsrv_cur, r['datachegada'])

            dados_barco = {
                "nome": r['nomebarco'], "tipo": r['tipobarco'],
                "empresa": r['nomeempresabarco'], "tamanho": r['tamanhobarco']
            }
            id_barco = get_or_create_dim_barco(sqlsrv_cur, dados_barco)

            dados_condutor = {
                "nome": r['nomecondutor'], "certificacao": r['certificacao'],
                "idade": r['idadecondutor'], "genero": metricas['genero_condutor']
            }
            id_condutor = get_or_create_dim_condutor(sqlsrv_cur, dados_condutor)

            dados_local = {
                "cidade": r['cidade_origem'], "pais": r['pais_origem'], "porto": r['nome_porto_origem']
            }
            id_local = get_or_create_dim_localizacao(sqlsrv_cur, dados_local)

            duracao = (r['datachegada'] - r['datapartida']).days
            if duracao < 0: duracao = 0
            receita_final = metricas['receita_taxas'] * TAXA_CAMBIO_USD_EUR

            sqlsrv_cur.execute("""
                INSERT INTO fato_viagem (
                    id_viagem, receita_taxas, num_contentores, peso_total_contentores, 
                    duracao_viagem, teu_total, tipo_viagem,
                    dim_localizacao_id_localizacao, dim_condutor_id_condutor, 
                    dim_barco_id_barco, dim_data_id_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_viagem_mysql, receita_final, metricas['num_contentores'],
                metricas['peso_total'], duracao, metricas['teu_total'], r['tipoviagem'],
                id_local, id_condutor, id_barco, id_tempo
            ))
            
            count_inseridos += 1
            if count_inseridos % 100 == 0:
                print(f"... {count_inseridos} inseridos")
                sqlsrv_conn.commit()

        sqlsrv_conn.commit()
        print(f"SUCESSO! Total de viagens carregadas no Data Mart: {count_inseridos}")

    except Exception as e:
        print(f"ERRO: {e}")
        if 'sqlsrv_conn' in locals(): sqlsrv_conn.rollback()
    finally:
        if 'mysql_conn' in locals() and mysql_conn.is_connected(): mysql_conn.close()
        if 'sqlsrv_conn' in locals(): sqlsrv_conn.close()

if __name__ == "__main__":
    main()