#include <stdio.h>
#include <string.h>
#include "aes.c"

void handleHelp(char*);
void handlePing(char*);
void handleTextMsg(char*);
void handleAESMsg(char *);
void handleSettings(char*);
void handleFreq(char*);
void handleBW(char*);
void handleSF(char*);
void handleCR(char*);
void handleTX(char*);
void handleAP(char*);
void handleAES(char*);
void handlePassword(char*);

vector<string> userStrings;
int cmdCount = 0;

struct myCommand {
  void (*ptr)(char *); // Function pointer
  char name[12];
  char help[48];
};

myCommand cmds[] = {
  {handleHelp, "help", "Shows this help."},
  {handleSettings, "lora", "Gets the current LoRa settings."},
  {handleFreq, "fq", "Gets/sets the working frequency."},
  {handleBW, "bw", "Gets/sets the working bandwidth."},
  {handleSF, "sf", "Gets/sets the spreading factor."},
  {handleCR, "cr", "Gets/sets the working coding rate."},
  {handleTX, "tx", "Gets/sets the Transmission Power."},
  {handleAP, "ap", "Gets/sets the auto-ping rate."},
  {handleAES, "aes", "Gets/sets the AES mode."},
  {handlePassword, "pwd", "Gets/sets the AES password."},
  {handlePing, "p", "Sends a ping packet."},
};

void handleHelp(char *param) {
  sprintf(msg, "Available commands: %d\n", cmdCount);
  Serial1.print(msg);
  for (int i = 0; i < cmdCount; i++) {
    sprintf(msg, " . %s: %s", cmds[i].name, cmds[i].help);
    Serial1.println(msg);
  }
}

void evalCmd(char *str, string fullString) {
  uint8_t ix, iy = strlen(str);
  for (ix = 0; ix < iy; ix++) {
    char c = str[ix];
    // lowercase the keyword
    if (c >= 'A' && c <= 'Z') str[ix] = c + 32;
  }
  Serial1.print("Evaluating: `");
  Serial1.print(fullString.c_str());
  Serial1.println("`");
  for (int i = 0; i < cmdCount; i++) {
    if (strcmp(str, cmds[i].name) == 0) {
      cmds[i].ptr((char*)fullString.c_str());
      return;
    }
  }
  sprintf(msg, "{\"type\":\"error\", \"msg\":\"Unknown command: `%s`\"}\n", str);
  Serial.print(msg); Serial1.print(msg);
  handleHelp("");
}

void handleCommands(string str1) {
  char kwd[32];
  int i = sscanf((char*)str1.c_str(), "/%s", kwd);
  if (i > 0) evalCmd(kwd, str1);
  // else handleTextMsg((char*)str1.c_str());
}

void handleSettings(char *param) {
  handleFreq("/fq");
  handleBW("/bw");
  handleSF("/sf");
  handleCR("/cr");
  handleTX("/tx");
  handleAP("/ap");
}

void handlePing(char *param) {
  sendMode();
  delay(100);
  char what[64];
  sprintf(what, "This is a not so short PING from %s", myName);
  if (needAES) handleAESMsg(what);
  else handleTextMsg(what);
  listenMode();
  lastPing = millis();
  // whether a manual ping or automatic
}

void handleAESMsg(char *what) {
  fillRandom(myIV, 16);
  Serial.println("IV:");
  Serial1.println("IV:");
  hexDump(myIV, 16);
  int16_t ln = strlen(what);
  int16_t olen = encryptCBC((uint8_t*)what, ln, myPWD, myIV);
  sendMode();
  delay(100);
  uint32_t t0 = millis();
  LoRa.beginPacket();
  LoRa.write(myIV, 16);
  LoRa.write(encBuf, olen);
  LoRa.endPacket();
  uint32_t t1 = millis() - t0;
  sprintf(msg, "{\"type\":\"info\", \"msg\":\"Encrypted message sent in %d ms\"}\n", t1);
  Serial.print(msg); Serial1.print(msg);
  listenMode();
}

void handleTextMsg(char *what) {
  sendMode();
  delay(100);
  uint32_t t0 = millis();
  LoRa.beginPacket();
  LoRa.write((uint8_t*)what, strlen(what));
  LoRa.endPacket();
  uint32_t t1 = millis() - t0;
  sprintf(msg, "{\"type\":\"info\", \"msg\":\"Message `%s` sent in %d ms\"}\n", what, t1);
  Serial.print(msg); Serial1.print(msg);
  listenMode();
}

void handleFreq(char *param) {
  if (strcmp("/fq", param) == 0) {
    // no parameters
    sprintf(msg, "{\"type\":\"info\", \"msg\":\"Frequency: %.3f MHz\"}\n", (myFreq / 1e6));
    Serial.print(msg); Serial1.print(msg);
  } else {
    // fq xxx.xxx set frequency
    // float value = sscanf(param, "%*s %f", &value);
    float value = atof(param + 3);
    if (value < 150.0 || value > 960.0) {
      // freq range 150MHz to 960MHz
      // Your chip might not support all...
      sprintf(msg, "{\"type\":\"error\", \"msg\":\"Invalid frequency: %.3f MHz\"}\n", value);
      Serial.print(msg); Serial1.print(msg);
      return;
    }
    myFreq = (uint32_t)(value * 1e6);
    sprintf(msg, "{\"type\":\"system\", \"msg\":\"Frequency set to: %.3f MHz\"}\n", (myFreq / 1e6));
    Serial.print(msg); Serial1.print(msg);
    LoRa.sleep();
    LoRa.setFrequency(myFreq);
    listenMode();
  }
#if defined(TRUST_BUT_VERIFY)
  checkFreq();
#endif
}

void handleBW(char* param) {
  if (strcmp("/bw", param) == 0) {
    // no parameters
    sprintf(msg, "{\"type\":\"info\", \"msg\":\"BW: %d, ie %.1f KHz\"}\n", bw, myBWs[bw]);
    Serial.print(msg); Serial1.print(msg);
  } else {
    int value = atoi(param + 3);
    // bw xxxx set BW
    if (value > 9) {
      sprintf(msg, "{\"type\":\"error\", \"msg\":\"BW value incorrect: %d!\"}\n", value);
      Serial.print(msg); Serial1.print(msg);
      return;
    }
    bw = value;
    LoRa.sleep();
    LoRa.setSignalBandwidth(myBWs[bw] * 1e3);
    listenMode();
    sprintf(msg, "{\"type\":\"system\", \"msg\":\"BW set to: %d, ie %d KHz\"}\n", bw, myBWs[bw]);
    Serial.print(msg); Serial1.print(msg);
  }
#if defined(TRUST_BUT_VERIFY)
  checkBW();
#endif
}

void handleSF(char* param) {
  if (strcmp("/sf", param) == 0) {
    // no parameters
    sprintf(msg, "{\"type\":\"info\", \"msg\":\"SF: %d\"}\n", sf);
    Serial.print(msg); Serial1.print(msg);
    return;
  } else {
    int value = atoi(param + 3);
    // sf xxxx set sf
    if (value < 6 || value > 12) {
      sprintf(msg, "{\"type\":\"error\", \"msg\":\"SF value incorrect: %d!\"}\n", value);
      Serial.print(msg); Serial1.print(msg);
      return;
    }
    sf = value;
    LoRa.sleep();
    LoRa.setSpreadingFactor(sf);
    listenMode();
    sprintf(msg, "{\"type\":\"system\", \"msg\":\"SF set to: %d\"}\n", sf);
    Serial.print(msg); Serial1.print(msg);
  }
#if defined(TRUST_BUT_VERIFY)
  checkSF();
#endif
}

void handleCR(char* param) {
  if (strcmp("/cr", param) == 0) {
    // no parameters
    sprintf(msg, "{\"type\":\"info\", \"msg\":\"CR: 4/%d\"}\n", cr);
    Serial.print(msg); Serial1.print(msg);
    return;
  } else {
    int value = atoi(param + 3);
    // cr xxxx set CR
    if (value < 5 || value > 8) {
      sprintf(msg, "{\"type\":\"error\", \"msg\":\"CR value incorrect: %d!\"}\n", value);
      Serial.print(msg); Serial1.print(msg);
      return;
    }
    cr = value;
    LoRa.sleep();
    LoRa.setCodingRate4(cr);
    listenMode();
    sprintf(msg, "{\"type\":\"system\", \"msg\":\"CR set to: 4/%d\"}\n", cr);
    Serial.print(msg); Serial1.print(msg);
  }
#if defined(TRUST_BUT_VERIFY)
  checkCR();
#endif
}

void handleTX(char* param) {
  if (strcmp("/tx", param) == 0) {
    // no parameters
    sprintf(msg, "{\"type\":\"info\", \"msg\":\"TX: %d\"}\n", txPower);
    Serial.print(msg); Serial1.print(msg);
    return;
  }
  int value = atoi(param + 3);
  // bw xxxx set BW
  if (value < 5 || value > 8) {
    sprintf(msg, "{\"type\":\"error\", \"msg\":\"TX value incorrect: %d!\"}\n", value);
    Serial.print(msg); Serial1.print(msg);
    return;
  }
  txPower = value;
  LoRa.sleep();
  LoRa.setTxPower(txPower);
  listenMode();
  sprintf(msg, "{\"type\":\"system\", \"msg\":\"TX set to: %d\"}\n", txPower);
  Serial.print(msg); Serial1.print(msg);
  return;
}

void handleAP(char* param) {
  if (strcmp("/ap", param) == 0) {
    // no parameters
    if (apFreq == 0) {
      sprintf(msg, "{\"type\":\"info\", \"msg\":\"AutoPING: OFF\"}\n");
    } else {
      sprintf(msg, "{\"type\":\"system\", \"msg\":\"AutoPING: ON, every %d secs.\"}\n", (apFreq / 1000));
    }
    Serial.print(msg); Serial1.print(msg);
    return;
  }
  uint32_t value = atoi(param + 3);
  if (value > 0 && value < 10) {
    sprintf(msg, "{\"type\":\"error\", \"msg\":\"AP value incorrect: %d!\"}\n", value);
    Serial.print(msg); Serial1.print(msg);
    return;
  }
  apFreq = value * 1e3;
  if (apFreq == 0) {
    sprintf(msg, "{\"type\":\"system\", \"msg\":\"AutoPING set to: OFF\"}\n");
  } else {
    sprintf(msg, "{\"type\":\"system\", \"msg\":\"AutoPING set to: ON, every %d secs.\"}\n", (apFreq / 1000));
    lastPing = millis();
  }
  Serial.print(msg); Serial1.print(msg);
}

int16_t encryptCBC(uint8_t* myBuf, uint8_t olen, uint8_t* pKey, uint8_t* Iv) {
  uint8_t rounds = olen / 16;
  if (rounds == 0) rounds = 1;
  else if (olen - (rounds * 16) != 0) rounds += 1;
  uint8_t length = rounds * 16;
  memset(encBuf, (length - olen), length);
  memcpy(encBuf, myBuf, olen);
  struct AES_ctx ctx;
  AES_init_ctx_iv(&ctx, pKey, Iv);
  AES_CBC_encrypt_buffer(&ctx, encBuf, length);
  return length;
}

int16_t decryptCBC(uint8_t* myBuf, uint8_t olen, uint8_t* pKey, uint8_t* Iv) {
  memcpy(encBuf, myBuf, olen);
  struct AES_ctx ctx;
  AES_init_ctx_iv(&ctx, pKey, Iv);
  AES_CBC_decrypt_buffer(&ctx, encBuf, olen);
  return olen;
}

void handlePassword(char* param) {
  char pwd[33];
  memset(pwd, 0, 33);
  int i = sscanf(param, "%*s %s", pwd);
  if (i == -1) {
    // no parameters
    fillRandom(myPWD, 16);
    array2hex(myPWD, 16, msg);
    msg[33] = 0;
    Serial.print("Key phrase created. Set it on other devices with:\n/pwd ");
    Serial.println(msg);
    Serial.println("You can now turn AES on with /AES on");
    return;
  } else {
    // either 16 chars or 32 hex chars
    if (strlen(pwd) == 16) {
      memcpy(myPWD, pwd, 16);
      Serial.println("Password set from string.");
      return;
    } else if (strlen(pwd) == 32) {
      hex2array(pwd, myPWD, 32);
      Serial.println("Password set from hex string.");
      Serial.println(msg);
      return;
    }
    Serial.println("AES: wrong pwd size! It should be 16 bytes, or a 32-byte hex string!");
    return;
  }
}

void handleAES(char* param) {
  char sw[33];
  memset(sw, 0, 33);
  int i = sscanf(param, "%*s %s", sw);
  if (i == -1) {
    // no parameters
    Serial.print("AES mode: ");
    Serial1.print("AES mode: ");
    if (needAES) {
      Serial.println("ON");
      Serial1.println("ON");
    } else {
      Serial.println("OFF");
      Serial1.println("OFF");
    }
    return;
  } else {
    for (i = 0; i < strlen(sw); i++) {
      // UPPERCASE everything
      if (sw[i] >= 'a' && sw[i] <= 'z') sw[i] -= 32;
    }
    if (strcmp("ON", sw) == 0) {
      needAES = true;
      Serial.println("Turning AES ON");
      checkPWD();
    } else if (strcmp("OFF", sw) == 0) {
      needAES = false;
      Serial.println("Turning AES OFF");
    } else {
      Serial.print("Unknown parameter: "); Serial.println(sw);
    }
  }
}
