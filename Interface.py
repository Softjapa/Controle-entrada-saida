import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import csv
from datetime import datetime

import Banco  

ARQ_MENSAGEM = "mensagem_atual.txt"
BANCO_DADOS = "seu_banco.db" 

def gerar_relatorio_mensal_csv(usuario_id, ano, mes, arquivo_saida):
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()

    data_inicio = f"{ano}-{mes:02d}-01"
    data_fim = f"{ano + 1}-01-01" if mes == 12 else f"{ano}-{mes + 1:02d}-01"

    cursor.execute("""
    SELECT r.data, r.hora_entrada, r.hora_saida, u.nome
    FROM registros r
    JOIN usuarios u ON r.usuario_id = u.id
    WHERE r.usuario_id=? AND r.data >= ? AND r.data < ?
          AND r.hora_entrada IS NOT NULL AND r.hora_saida IS NOT NULL
    ORDER BY r.data
    """, (usuario_id, data_inicio, data_fim))

    registros = cursor.fetchall()
    conn.close()

    total_segundos = 0
    linhas = []
    for data, hora_entrada, hora_saida, nome in registros:
        h_entrada = datetime.strptime(hora_entrada, "%H:%M:%S")
        h_saida = datetime.strptime(hora_saida, "%H:%M:%S")
        diff = (h_saida - h_entrada).total_seconds()
        if diff < 0:
            diff = 0
        total_segundos += diff
        h = int(diff // 3600)
        m = int((diff % 3600) // 60)
        s = int(diff % 60)
        tempo_trabalhado = f"{h}h {m}m {s}s" if diff > 0 else "Erro"
        linhas.append([data, hora_entrada, hora_saida, tempo_trabalhado])

    total_horas = int(total_segundos // 3600)
    total_minutos = int((total_segundos % 3600) // 60)
    total_segundos_restantes = int(total_segundos % 60)

    with open(arquivo_saida, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Nome", nome if registros else "Desconhecido"])
        writer.writerow(["Mês", f"{ano}-{mes:02d}"])
        writer.writerow(["Dias Registrados", len(linhas)])
        writer.writerow([])
        writer.writerow(["Data", "Entrada", "Saída", "Tempo no expediente"])
        writer.writerows(linhas)
        writer.writerow([])
        writer.writerow(["Total de horas no mês", f"{total_horas}h {total_minutos}m {total_segundos_restantes}s"])

    print("\nRelatório de ponto")
    print(f"Nome: {nome if registros else 'Desconhecido'}")
    print(f"Mês: {ano}-{mes:02d}")
    print(f"Dias Registrados: {len(linhas)}\n")
    print(f"{'Data':<12} | {'Entrada':<10} | {'Saída':<10} | {'Tempo no expediente':<20}")
    print("-" * 65)
    for linha in linhas:
        print(f"{linha[0]:<12} | {linha[1]:<10} | {linha[2]:<10} | {linha[3]:<20}")
    print("-" * 65)
    print(f"Total de horas no mês: {total_horas}h {total_minutos}m {total_segundos_restantes}s\n")
    print(f"Relatório gerado em: {arquivo_saida}")



class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Acesso RFID")

        self.frame_usuarios = ttk.Frame(root)
        self.frame_usuarios.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        ttk.Label(self.frame_usuarios, text="Usuários").pack()
        self.tree_usuarios = ttk.Treeview(self.frame_usuarios, columns=("ID", "Nome", "UID"), show="headings", height=15)
        for col in ("ID", "Nome", "UID"):
            self.tree_usuarios.heading(col, text=col)
            self.tree_usuarios.column(col, width=120)
        self.tree_usuarios.pack()
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.on_usuario_selecionado)

        ttk.Button(self.frame_usuarios, text="Adicionar Usuário", command=self.adicionar_usuario).pack(pady=5)
        ttk.Button(self.frame_usuarios, text="Editar Usuário", command=self.editar_usuario).pack(pady=5)
        ttk.Button(self.frame_usuarios, text="Excluir Usuário", command=self.excluir_usuario).pack(pady=5)
        ttk.Button(self.frame_usuarios, text="Gerar Relatório Mensal", command=self.gerar_relatorio).pack(pady=5)

        self.frame_registros = ttk.Frame(root)
        self.frame_registros.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(self.frame_registros, text="Registros de Entrada/Saída").pack()
        self.tree_registros = ttk.Treeview(self.frame_registros, columns=("ID", "Nome", "UID", "Data", "Entrada", "Saída"), show="headings")
        for col in ("ID", "Nome", "UID", "Data", "Entrada", "Saída"):
            self.tree_registros.heading(col, text=col)
            self.tree_registros.column(col, width=100)
        self.tree_registros.pack(fill=tk.BOTH, expand=True)

        ttk.Button(self.frame_registros, text="Atualizar Registros", command=self.atualizar_registros).pack(pady=5)

        self.label_mensagem = ttk.Label(root, text="Aguardando leitura...", font=("Arial", 14), foreground="black")
        self.label_mensagem.pack(side=tk.BOTTOM, pady=10)

        self.atualizar_usuarios()
        self.atualizar_registros()
        self.atualizar_registros_periodicamente()
        self.atualizar_mensagem_arquivo()

    def atualizar_usuarios(self):
        for i in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(i)
        usuarios = Banco.listar_usuarios()
        for u in usuarios:
            self.tree_usuarios.insert('', 'end', values=u)

    def atualizar_registros(self):
        for i in self.tree_registros.get_children():
            self.tree_registros.delete(i)
        registros = Banco.listar_registros()
        for r in registros:
            self.tree_registros.insert('', 'end', values=r)

    def atualizar_registros_periodicamente(self):
        self.atualizar_registros()
        self.root.after(2000, self.atualizar_registros_periodicamente)

    def atualizar_mensagem_arquivo(self):
        try:
            with open(ARQ_MENSAGEM, "r", encoding="utf-8") as f:
                msg = f.read()
        except FileNotFoundError:
            msg = "Aguardando leitura..."
        self.label_mensagem.config(text=msg)
        self.root.after(500, self.atualizar_mensagem_arquivo)

    def on_usuario_selecionado(self, event):
        pass

    def adicionar_usuario(self):
        nome = simpledialog.askstring("Nome", "Digite o nome do usuário:", parent=self.root)
        if not nome:
            return
        uid = simpledialog.askstring("UID", "Digite o UID do cartão:", parent=self.root)
        if not uid:
            return
        sucesso = Banco.adicionar_usuario(nome, uid)
        if sucesso:
            messagebox.showinfo("Sucesso", "Usuário adicionado!")
            self.atualizar_usuarios()
        else:
            messagebox.showerror("Erro", "UID já existe!")

    def editar_usuario(self):
        selecionado = self.tree_usuarios.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um usuário para editar.")
            return
        valores = self.tree_usuarios.item(selecionado, 'values')
        usuario_id = valores[0]
        nome_atual = valores[1]
        uid_atual = valores[2]

        novo_nome = simpledialog.askstring("Editar Nome", "Digite o novo nome:", initialvalue=nome_atual, parent=self.root)
        if not novo_nome:
            return
        novo_uid = simpledialog.askstring("Editar UID", "Digite o novo UID:", initialvalue=uid_atual, parent=self.root)
        if not novo_uid:
            return

        sucesso = Banco.alterar_usuario(usuario_id, novo_nome, novo_uid)
        if sucesso:
            messagebox.showinfo("Sucesso", "Usuário alterado!")
            self.atualizar_usuarios()
        else:
            messagebox.showerror("Erro", "UID já existe!")

    def excluir_usuario(self):
        selecionado = self.tree_usuarios.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um usuário para excluir.")
            return
        valores = self.tree_usuarios.item(selecionado, 'values')
        usuario_id = valores[0]
        nome = valores[1]
        if messagebox.askyesno("Confirmação", f"Deseja excluir o usuário '{nome}'?"):
            Banco.excluir_usuario(usuario_id)
            self.atualizar_usuarios()

    def gerar_relatorio(self):
        selecionado = self.tree_usuarios.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um usuário para gerar o relatório.")
            return

        valores = self.tree_usuarios.item(selecionado, 'values')
        usuario_id = int(valores[0])
        nome = valores[1]

        ano = simpledialog.askinteger("Ano", "Digite o ano do relatório (ex: 2025):", parent=self.root)
        if not ano:
            return
        mes = simpledialog.askinteger("Mês", "Digite o mês (1 a 12):", parent=self.root, minvalue=1, maxvalue=12)
        if not mes:
            return

        nome_arquivo = f"relatorio_{nome}_{ano}_{mes:02d}.csv"

        try:
            gerar_relatorio_mensal_csv(usuario_id, ano, mes, nome_arquivo)
            messagebox.showinfo("Relatório", f"Relatório gerado com sucesso:\n{nome_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{e}")


if __name__ == "__main__":
    Banco.criar_banco()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
