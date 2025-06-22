import os
import sqlite3
from datetime import datetime, date

BANCO_DADOS = os.path.join(os.path.dirname(__file__), "seu_banco.db")

def criar_banco():
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        uid TEXT UNIQUE NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uids_bloqueados (
        uid TEXT PRIMARY KEY
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        data DATE NOT NULL,
        hora_entrada TEXT,
        hora_saida TEXT,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    """)
    conn.commit()
    conn.close()

def adicionar_usuario(nome, uid):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nome, uid) VALUES (?, ?)", (nome, uid))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False  
    conn.close()
    return True

def alterar_usuario(usuario_id, novo_nome, novo_uid):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE usuarios SET nome=?, uid=? WHERE id=?", (novo_nome, novo_uid, usuario_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False  
    conn.close()
    return True

def excluir_usuario(usuario_id):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))
    conn.commit()
    conn.close()

def listar_usuarios():
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, uid FROM usuarios ORDER BY nome")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def buscar_usuario_por_uid(uid):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios WHERE uid=?", (uid,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado  

def registrar_ponto(uid):
    """
    Registra entrada ou saída para o UID no dia atual.
    Se não tem registro no dia, cria entrada.
    Se tem entrada e saída vazia, registra saída.
    Se já tem entrada e saída, cria novo registro (novo ponto).
    """
    usuario = buscar_usuario_por_uid(uid)
    if not usuario:
        mensagem = f"UID {uid} NÃO CADASTRADO"
        print(mensagem)
        return mensagem

    usuario_id, nome = usuario
    hoje = date.today().isoformat()
    agora = datetime.now().strftime("%H:%M:%S")

    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, hora_entrada, hora_saida FROM registros
        WHERE usuario_id=? AND data=?
        ORDER BY id DESC LIMIT 1
    """, (usuario_id, hoje))
    registro = cursor.fetchone()

    if not registro:
        cursor.execute("""
            INSERT INTO registros (usuario_id, data, hora_entrada, hora_saida)
            VALUES (?, ?, ?, NULL)
        """, (usuario_id, hoje, agora))
        conn.commit()
        conn.close()
        mensagem = f"ACESSO PERMITIDO: {nome}"
        print(f"Entrada registrada para {nome} ({uid}) às {agora}")
        return mensagem
    else:
        id_registro, hora_entrada, hora_saida = registro
        if hora_saida is None:
            cursor.execute("UPDATE registros SET hora_saida=? WHERE id=?", (agora, id_registro))
            conn.commit()
            conn.close()
            mensagem = f"ACESSO PERMITIDO: {nome}"
            print(f"Saída registrada para {nome} ({uid}) às {agora}")
            return mensagem
        else:
            cursor.execute("""
                INSERT INTO registros (usuario_id, data, hora_entrada, hora_saida)
                VALUES (?, ?, ?, NULL)
            """, (usuario_id, hoje, agora))
            conn.commit()
            conn.close()
            mensagem = f"ACESSO PERMITIDO: {nome}"
            print(f"Nova entrada registrada para {nome} ({uid}) às {agora}")
            return mensagem

def listar_registros():
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT r.id, u.nome, u.uid, r.data, r.hora_entrada, r.hora_saida
    FROM registros r
    JOIN usuarios u ON r.usuario_id = u.id
    ORDER BY r.data DESC, r.hora_entrada DESC
    """)
    registros = cursor.fetchall()
    conn.close()
    return registros

def calcular_banco_horas_mes(usuario_id, ano, mes):
    """
    Calcula total de horas trabalhadas no mês (ano, mes) para um usuário.
    """
    import datetime
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    data_inicio = f"{ano}-{mes:02d}-01"
    if mes == 12:
        data_fim = f"{ano+1}-01-01"
    else:
        data_fim = f"{ano}-{mes+1:02d}-01"
    cursor.execute("""
    SELECT hora_entrada, hora_saida FROM registros
    WHERE usuario_id=? AND data >= ? AND data < ? AND hora_entrada IS NOT NULL AND hora_saida IS NOT NULL
    """, (usuario_id, data_inicio, data_fim))
    registros = cursor.fetchall()
    total_segundos = 0
    for entrada, saida in registros:
        h_entrada = datetime.datetime.strptime(entrada, "%H:%M:%S")
        h_saida = datetime.datetime.strptime(saida, "%H:%M:%S")
        diff = (h_saida - h_entrada).total_seconds()
        if diff > 0:
            total_segundos += diff
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    conn.close()
    return f"{int(horas)}h {int(minutos)}m"
