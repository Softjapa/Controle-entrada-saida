import subprocess
import time
import os

caminho_interface = os.path.abspath("Interface.py")
caminho_registro = os.path.abspath("Registro.py")

subprocess.Popen(["python", caminho_interface])
time.sleep(2)  

subprocess.Popen(["python", caminho_registro])

print("Sistema de controle de acesso iniciado com sucesso!")
