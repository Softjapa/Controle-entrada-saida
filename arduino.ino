#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>

#define SS_PIN 10    
#define RST_PIN 9    

MFRC522 mfrc522(SS_PIN, RST_PIN);  
LiquidCrystal_I2C lcd(0x27, 16, 2);  

String respostaPython = "";
bool aguardandoResposta = false;

unsigned long tempoEspera = 0;
const unsigned long timeoutResposta = 3000; // 3 segundos

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Aproxime o");
  lcd.setCursor(0,1);
  lcd.print("cartao...");
}

void scrollMessage(String msg) {
  int len = msg.length();
  int windowSize = 16; // tamanho do display (16 colunas)

  if (len <= windowSize) {
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print(msg);
    delay(3000);
  } else {
    for (int i = 0; i <= len - windowSize; i++) {
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print(msg.substring(i, i + windowSize));
      delay(300);
    }
    delay(2000);
  }
}

void loop() {
  if (aguardandoResposta) {
    if (Serial.available()) {
      char c = Serial.read();
      if (c == '\n') {
        scrollMessage(respostaPython);
        respostaPython = "";
        aguardandoResposta = false;
        lcd.clear();
        lcd.setCursor(0,0);
        lcd.print("Aproxime o");
        lcd.setCursor(0,1);
        lcd.print("cartao...");
      } else {
        respostaPython += c;
      }
    }
    if (millis() - tempoEspera > timeoutResposta) {
      aguardandoResposta = false;
      respostaPython = "";
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("Tempo esgotado");
      delay(2000);
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("Aproxime o");
      lcd.setCursor(0,1);
      lcd.print("cartao...");
    }
    return;  
  }

  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  String uidStr = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(mfrc522.uid.uidByte[i], HEX);
    if (i != mfrc522.uid.size - 1) uidStr += " ";
  }
  uidStr.toUpperCase();

  Serial.println(uidStr); // envia UID para Python
  aguardandoResposta = true;
  tempoEspera = millis();

  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Esperando resp");
}
