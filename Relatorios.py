import sqlite3
import datetime
import csv

BANCO_DADOS = "seu_banco.db"  

def gerar_relatorio_mensal_csv(usuario_id, ano, mes, arquivo_saida):
    """
    Gera um relatório CSV das horas trabalhadas no mês para o usuário.
    Args:
        usuario_id (int): ID do usuário no banco.
        ano (int): Ano do relatório.
        mes (int): Mês do relatório.
        arquivo_saida (str): Caminho do arquivo CSV a ser gerado.
    """
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()

    data_inicio = f"{ano}-{mes:02d}-01"
    if mes == 12:
        data_fim = f"{ano+1}-01-01"
    else:
        data_fim = f"{ano}-{mes+1:02d}-01"

    cursor.execute("""
    SELECT r.data, r.hora_entrada, r.hora_saida, u.nome
    FROM registros r
    JOIN usuarios u ON r.usuario_id = u.id
    WHERE r.usuario_id=? AND r.data >= ? AND r.data < ? AND r.hora_entrada IS NOT NULL AND r.hora_saida IS NOT NULL
    ORDER BY r.data
    """, (usuario_id, data_inicio, data_fim))

    registros = cursor.fetchall()
    conn.close()

    total_segundos = 0
    linhas = []
    for data, hora_entrada, hora_saida, nome in registros:
        h_entrada = datetime.datetime.strptime(hora_entrada, "%H:%M:%S")
        h_saida = datetime.datetime.strptime(hora_saida, "%H:%M:%S")
        diff = (h_saida - h_entrada).total_seconds()
        if diff < 0:
            diff = 0
        total_segundos += diff
        linhas.append([data, hora_entrada, hora_saida, f"{int(diff//3600)}h {int((diff%3600)//60)}m"])

    total_horas = int(total_segundos // 3600)
    total_minutos = int((total_segundos % 3600) // 60)

    with open(arquivo_saida, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Nome", nome])
        writer.writerow(["Mês", f"{ano}-{mes:02d}"])
        writer.writerow([])
        writer.writerow(["Data", "Entrada", "Saída", "Tempo no expediente"])
        writer.writerows(linhas)
        writer.writerow([])
        writer.writerow(["Total de horas no mês", f"{total_horas}h {total_minutos}m"])

    print(f"Relatório gerado em: {arquivo_saida}")
