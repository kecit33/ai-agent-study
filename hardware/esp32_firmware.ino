/*
 * AI 校园学习陪伴助手 —— ESP32 硬件联动固件（可选加分项，v2 双向联动）
 *
 * 下行（Web -> ESP32）：
 *   1. POST /remind  {"task":"...","message":"..."}  复习/番茄钟到点提醒：LED + 蜂鸣器 1.5s
 *   2. POST /focus   {"active":true,"minutes":25}     专注状态灯：专注中 LED 常亮，结束熄灭
 *
 * 上行（ESP32 -> Web）：
 *   3. 每 60s GET {SERVER_BASE}/api/hardware/status  学习状态看板：
 *      待复习任务数 / 待掌握错题数 / 专注状态，打印到串口（可接 OLED 显示）。
 *
 * 接线：LED -> GPIO 2（板载也可），蜂鸣器 -> GPIO 4（有源蜂鸣器）。
 * 烧录：Arduino IDE，开发板选 "ESP32 Dev Module"，安装 ESP32 支持包与 ArduinoJson。
 */

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ===== 修改为你的 WiFi / 引脚 / 服务器地址 =====
const char* SSID = "你的WiFi名";
const char* PASS = "你的WiFi密码";
const int LED_PIN = 2;
const int BUZZER_PIN = 4;
// Web 服务所在电脑的局域网地址（运行 python server.py 的那台）
const char* SERVER_BASE = "http://192.168.1.100:5000";
const bool ENABLE_POLL = true;          // 是否开启学习状态上行轮询
const unsigned long POLL_MS = 60000;    // 轮询周期
// ==============================================

WebServer server(80);
unsigned long lastPoll = 0;

void beepFlash(int ms) {
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(ms);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void handleRemind() {
  if (server.method() != HTTP_POST) { server.send(405, "text/plain", "Method Not Allowed"); return; }
  DynamicJsonDocument doc(512);
  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  String task = err ? "复习任务" : doc["task"] | "复习任务";
  beepFlash(1500);
  server.send(200, "application/json", "{\"ok\":true,\"task\":\"" + task + "\"}");
  Serial.println("已提醒：" + task);
}

void handleFocus() {
  if (server.method() != HTTP_POST) { server.send(405, "text/plain", "Method Not Allowed"); return; }
  DynamicJsonDocument doc(256);
  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  bool active = err ? false : doc["active"] | false;
  digitalWrite(LED_PIN, active ? HIGH : LOW);   // 专注中常亮，结束熄灭
  digitalWrite(BUZZER_PIN, LOW);
  server.send(200, "application/json", active ? "{\"ok\":true,\"focus\":true}" : "{\"ok\":true,\"focus\":false}");
  Serial.println(active ? "专注灯：常亮" : "专注灯：熄灭");
}

void pollStatus() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(String(SERVER_BASE) + "/api/hardware/status");
  int code = http.GET();
  if (code == 200) {
    DynamicJsonDocument doc(1024);
    if (!deserializeJson(doc, http.getString())) {
      // display 字段已由服务端拼好：待复习 N | 待掌握错题 N | 专注中/空闲
      Serial.println("[学习看板] " + String((const char*)doc["display"]));
      // 有待复习任务时短闪一下提示（不打扰，仅 150ms）
      if ((int)doc["pending_tasks"] > 0 && !((bool)doc["focus_active"])) {
        digitalWrite(LED_PIN, HIGH); delay(150); digitalWrite(LED_PIN, LOW);
      }
    }
  } else {
    Serial.printf("[学习看板] 拉取失败 HTTP %d\n", code);
  }
  http.end();
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
  server.on("/focus", handleFocus);
  server.begin();
  Serial.println("HTTP 服务已启动：/remind /focus");
}

void loop() {
  server.handleClient();
  if (ENABLE_POLL && millis() - lastPoll > POLL_MS) {
    lastPoll = millis();
    pollStatus();
  }
}
