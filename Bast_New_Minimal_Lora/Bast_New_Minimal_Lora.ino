#undef max
#undef min
#include <string>
#include <vector>
#include <cstring>

using namespace std;
template class basic_string<char>; // https://github.com/esp8266/Arduino/issues/1136
// Required or the code won't compile!

namespace std _GLIBCXX_VISIBILITY(default) {
_GLIBCXX_BEGIN_NAMESPACE_VERSION
void __throw_length_error(char const*) {}
void __throw_bad_alloc() {}
void __throw_out_of_range(char const*) {}
void __throw_logic_error(char const*) {}
void __throw_out_of_range_fmt(char const*, ...) {}
}

#include <SPI.h>
#include <LoRa.h>
#include "LoRaHelper.h"
#include "Commands.h"
#include <LoRandom.h>

int counter = 0;
union uidConverter {
  char b[12];
  int32_t i[3];
};

// Uncomment the next line if you want to run the AES self-test
//#define AES_Self_Test

void setup() {
  Serial.begin(115200);
  Serial1.begin(115200);
  while (!Serial);
  cmdCount = sizeof(cmds) / sizeof(myCommand);
  sprintf(msg, "{\"type\":\"title\", \"msg\":\"UniBaster Minimal LoRa\"}\n");
  Serial.print(msg); Serial1.print(msg);
  sprintf(msg, "{\"type\":\"cmdCount\", \"msg\":%d}", cmdCount);
  Serial.print(msg); Serial1.print(msg);
  strcpy(myName, "Unihiker");
  sprintf(msg, "{\"type\":\"myName\", \"msg\":%s}", myName);
  Serial.print(msg); Serial1.print(msg);

  Serial1.print("Setting up LoRa ");
  LoRa.setPins(SS, RFM_RST, RFM_DIO0);
  if (!LoRa.begin(myFreq)) {
    sprintf(msg, "{\"type\":\"error\", \"msg\":\"Starting LoRa failed!\"}\n");
    Serial.print(msg); Serial1.print(msg);
    delay(500);
    while (1);
  } else {
    sprintf(msg, "{\"type\":\"system\", \"msg\":\"Started LoRa @ %.3f MHz\"}\n", (myFreq / 1e6));
    Serial.print(msg); Serial1.print(msg);
#if defined(TRUST_BUT_VERIFY)
    checkFreq();
#endif
  }
  LoRa.sleep();
  pinMode(RFM_SWITCH, OUTPUT);
  digitalWrite(RFM_SWITCH, 1);
  LoRa.setTxPower(txPower, PA_OUTPUT_PA_BOOST_PIN);
  LoRa.setSpreadingFactor(sf);
#if defined(TRUST_BUT_VERIFY)
  checkSF();
#endif
  LoRa.setSignalBandwidth(myBWs[bw] * 1e3);
#if defined(TRUST_BUT_VERIFY)
  checkBW();
#endif
  LoRa.setCodingRate4(cr);
#if defined(TRUST_BUT_VERIFY)
  checkCR();
#endif
  LoRa.setPreambleLength(preamble);
  delay(1000);
  pinMode(PIN_PA28, OUTPUT);
  digitalWrite(PIN_PA28, HIGH);
  if (needAES) {
    needAES = checkPWD();
  } else {
    memset(myPWD, 0, 16);
  }
}

void loop() {
  if (apFreq > 0) {
    if (millis() - lastPing >= apFreq) {
      sprintf(msg, "{\"type\":\"system\", \"msg\":\"Autoping\"}\n");
      Serial.print(msg); Serial1.print(msg);
      handlePing("");
    }
  }
  int packetSize = LoRa.parsePacket();
  if (packetSize) onReceive(packetSize);
  // DIO0 callback doesn't seem to work,
  // we have to do it by hand for now anyway
  if (Serial.available()) {
    // incoming from user
    char incoming[256];
    memset(incoming, 0, 256);
    uint8_t ix = 0;
    while (Serial.available()) {
      char c = Serial.read();
      Serial1.write(c);
      delay(25);
      if (c == 13 || c == 10) {
        // cr / lf: we want to buffer lines and treat them one by one
        // when we're done receiving.
        if (ix > 0) {
          // only if we have a line to save:
          // if we receive CR + LF, the second byte would give us
          // an empty line.
          incoming[ix] = 0;
          string nextLine = string(incoming);
          userStrings.push_back(nextLine);
          ix = 0;
        }
      } else incoming[ix++] = c;
    }
    // if you don't terminate your last command with CR and/or LF,
    // not my problem... ;-)
    // But seriously I should add whatever is left to userStrings...
  }
  if (Serial1.available()) {
    // incoming from user
    char incoming[256];
    memset(incoming, 0, 256);
    uint8_t ix = 0;
    while (Serial1.available()) {
      char c = Serial1.read();
      delay(25);
      if (c == 13 || c == 10) {
        // cr / lf: we want to buffer lines and treat them one by one
        // when we're done receiving.
        if (ix > 0) {
          // only if we have a line to save:
          // if we receive CR + LF, the second byte would give us
          // an empty line.
          incoming[ix] = 0;
          string nextLine = string(incoming);
          userStrings.push_back(nextLine);
          ix = 0;
        }
      } else incoming[ix++] = c;
    }
    // if you don't terminate your last command with CR and/or LF,
    // not my problem... ;-)
    // But seriously I should add whatever is left to userStrings...
  }
  if (userStrings.size() > 0) {
    uint8_t ix, iy = userStrings.size();
    for (ix = 0; ix < iy; ix++) {
      handleCommands(userStrings[ix]);
    }
    userStrings.resize(0);
  }
}
