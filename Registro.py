import time
import serial
import Banco

PORTA_SERIAL = 'COM3'  
BAUDRATE = 9600
DELAY = 5  

ARQ_MENSAGEM = "mensagem_atual.txt"

ultimas_leituras = {}

def escrever_mensagem(msg):
    try:
        with open(ARQ_MENSAGEM, "w", encoding="utf-8") as f:
            f.write(msg)
    except Exception as e:
        print(f"Erro ao escrever mensagem no arquivo: {e}")

def escutar_serial():
    try:
        ser = serial.Serial(PORTA_SERIAL, BAUDRATE, timeout=1)
        print(f"Escutando {PORTA_SERIAL}...")
        while True:
            if ser.in_waiting:
                linha = ser.readline().decode('utf-8').strip()
                if linha:
                    uid = linha
                    agora = time.time()
                    if uid in ultimas_leituras and (agora - ultimas_leituras[uid]) < DELAY:
                        print(f"UID {uid} bloqueado temporariamente, aguarde.")
                    else:
                        ultimas_leituras[uid] = agora
                        resposta = Banco.registrar_ponto(uid)
                        print(resposta)
                        escrever_mensagem(resposta)
            time.sleep(0.1)
    except serial.SerialException as e:
        print(f"Erro na serial: {e}")
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        escrever_mensagem("Programa parado.")

if __name__ == "__main__":
    escrever_mensagem("Aguardando leitura...")
    escutar_serial()
