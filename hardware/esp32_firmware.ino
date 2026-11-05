/*
 * AI 校园学习陪伴助手 —— ESP32 硬件联动固件（可选加分项）
 *
 * 功能：ESP32 连接 WiFi 后启动 HTTP 服务，监听 Web 端下发的复习提醒
 *       （POST /remind，JSON: {"task":"...","message":"..."}），
 *       收到后点亮 LED 并触发蜂鸣器，在桌面形成实物提醒。
 *
 * 接线：LED -> GPIO 2（板载也可），蜂鸣器 -> GPIO 4（有源蜂鸣器）。
 * 烧录：用 Arduino IDE，选开发板 "ESP32 Dev Module"，装好 ESP32 支持包。
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// ===== 修改为你的 WiFi 与引脚 =====
const char* SSID = "你的WiFi名";
const char* PASS = "你的WiFi密码";
const int LED_PIN = 2;
const int BUZZER_PIN = 4;
// ================================

WebServer server(80);

void handleRemind() {
  if (server.method() != HTTP_POST) { server.send(405, "text/plain", "Method Not Allowed"); return; }
  String body = server.arg("plain");
  DynamicJsonDocument doc(512);
  DeserializationError err = deserializeJson(doc, body);
  String task = err ? "复习任务" : doc["task"] | "复习任务";

  // 点亮 LED + 蜂鸣器提醒 1.5 秒
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(1500);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  String msg = "已提醒：" + task;
  server.send(200, "application/json", "{\"ok\":true,\"task\":\"" + task + "\"}");
  Serial.println(msg);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  WiFi.begin(SSID, PASS);
  Serial.print("连接 WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi 已连接，IP: " + WiFi.localIP().toString());

  server.on("/remind", handleRemind);
  server.begin();
  Serial.println("HTTP 服务已启动，监听 /remind");
}

void loop() {
  server.handleClient();
}
