#!/usr/bin/python3
import serial, time, sys, requests, re, json, binascii
from os import path, remove, listdir
from unihiker import GUI
from pinpong.board import Board, I2C
from pinpong.libs.dfrobot_bme280 import BME280
from pinpong.libs.dfrobot_bme680 import DFRobot_BME680

scrollBuffer = []
screenOFF = False
eraseStatus = -1
SF = 12
BW = 7
CR = 5
apFreq = 0
myFreq = 863.0
myBWs = [7.8, 10.4, 15.63, 20.83, 31.25, 41.67, 62.5, 125, 250, 500]

Board("UNIHIKER").begin()
w = GUI()
w.clear()
w.draw_text(text="Loading...", x = 61, y = 91, font_size=18, color="#FFcccc")
w.draw_text(text="Loading...", x = 60, y = 90, font_size=18, color="#FF0000")
posY = 131

ls = listdir("/dev/")
fp = "/dev/"
Found = False
for x in ls:
  if x.startswith('ttyACM'):
    txt = f" - USB port: {x}"
    print(txt)
    w.draw_text(text=txt, x = 10, y = posY, font_size=12, color="#3333FF")
    posY += 20
    fp += x
    Found = True
    break
if Found == False:
  txt = "Couldn't find a port!"
  print(txt)
  w.draw_text(text=txt, x = 11, y = posY+1, font_size=12, color="#3333FF")
  w.draw_text(text=txt, x = 10, y = posY, font_size=12, color="#3333FF")
  sys.exit()
ss = serial.Serial(fp, 115200)

def logSys(txt):
  global ss, eraseStatus
  w.fill_rect(x=0, y=298, w=240, h=22, color = "#ffffff")
  if txt != '':
    w.draw_text(text=txt, x = 3, y = 298, font_size=12, color="#3333FF")
    w.draw_text(text=txt, x = 2, y = 297, font_size=12, color="#3333FF")
    print(txt)
    eraseStatus = time.time()

def sendPING():
  global ss
  logSys("Sending ping...")
  ss.write(b"/p\n")
  time.sleep(1)
  logSys("PING sent!")

def btnPING():
  print("btnPING")
  sendPING()

def displayBox(txt, leftPos, posY, wd, he, rd, fClr, fun = None):
  w.fill_round_rect(x=leftPos, y=posY, w=wd, h=he, r=rd, color="#ecf6fd")
  w.draw_round_rect(x=leftPos, y=posY, w=wd, h=he, r=rd, color=fClr)
  w.draw_round_rect(x=leftPos+1, y=posY+1, w=wd-2, h=he-2, r=rd, color=fClr)
  w.draw_round_rect(x=leftPos+2, y=posY+2, w=wd-4, h=he-4, r=rd, color=fClr)
  w.draw_text(text=txt, x = leftPos+10, y=posY+5, font_size=15, color=fClr, onclick=fun)

def setAP(v):
  global ss, apFreq
  apFreq = v
  logSys(f"Setting AP to {v}")
  cmd = f'/ap {v}\n'.encode('ascii')
  ss.write(bytes(cmd))
  time.sleep(1)
  drawMainMenu()

def setSF(v):
  global ss, SF
  SF = v
  logSys(f"Setting SF to {v}")
  cmd = f'/sf {v}\n'.encode('ascii')
  ss.write(bytes(cmd))
  time.sleep(1)
  drawMainMenu()

def setBW(v):
  global ss, BW, myBWs
  BW = v
  logSys(f"Setting SF to {v} / {myBWs[BW]} KHz")
  cmd = f'/bw {v}\n'.encode('ascii')
  ss.write(bytes(cmd))
  time.sleep(1)
  drawMainMenu()

def setCR(v):
  global ss, CR
  CR = v
  logSys(f"Setting CR to 4/{v}")
  cmd = f'/cr {v}\n'.encode('ascii')
  ss.write(bytes(cmd))
  time.sleep(1)
  drawMainMenu()

def goAP():
  global w, apFreq, posY
  w.clear()
  w.draw_text(text="Auto-PING", x = 31, y = 11, font_size=18, color="#FFcccc")
  w.draw_text(text="Auto-PING", x = 30, y = 10, font_size=18, color="#FF0000")
  displayBox(" OFF", 20, 60, 90, 40, 4, "#003e7f", lambda:setAP(0))
  displayBox(" 15 s", 120, 60, 90, 40, 4, "#003e7f", lambda:setAP(15))
  displayBox(" 30 s", 20, 110, 90, 40, 4, "#003e7f", lambda:setAP(30))
  displayBox(" 45 s", 120, 110, 90, 40, 4, "#003e7f", lambda:setAP(45))
  displayBox(" 60 s", 20, 160, 90, 40, 4, "#003e7f", lambda:setAP(60))
  displayBox(" 2 mn", 120, 160, 90, 40, 4, "#003e7f", lambda:setAP(120))
  displayBox(" esc", 20, 210, 90, 40, 4, "#003e7f", drawMainMenu)
  w.draw_text(text=f'AP is currently set to {apFreq}', x = 3, y = 298, font_size=12, color="#3333FF")
  w.draw_text(text=f'AP is currently set to {apFreq}', x = 2, y = 297, font_size=12, color="#3333FF")
  posY = 260
  lastInteraction = time.time()

def doSF():
  global w, SF, posY
  w.clear()
  w.draw_text(text="Select SF", x = 31, y = 11, font_size=18, color="#FFcccc")
  w.draw_text(text="Select SF", x = 30, y = 10, font_size=18, color="#FF0000")
  displayBox("  7 ", 20, 60, 60, 40, 4, "#003e7f", lambda:setSF(7))
  displayBox("  8 ", 90, 60, 60, 40, 4, "#003e7f", lambda:setSF(8))
  displayBox("  9 ", 160, 60, 60, 40, 4, "#003e7f", lambda:setSF(9))
  displayBox(" 10 ", 20, 110, 60, 40, 4, "#003e7f", lambda:setSF(10))
  displayBox(" 11 ", 90, 110, 60, 40, 4, "#003e7f", lambda:setSF(11))
  displayBox(" 12 ", 160, 110, 60, 40, 4, "#003e7f", lambda:setSF(12))
  displayBox("  esc", 20, 160, 80, 40, 4, "#003e7f", drawMainMenu)
  w.draw_text(text=f'SF is currently set to {SF}', x = 30, y = 298, font_size=12, color="#3333FF")
  w.draw_text(text=f'SF is currently set to {SF}', x = 2, y = 297, font_size=12, color="#3333FF")
  posY = 210
  lastInteraction = time.time()

def doBW():
  global w, BW, myBWs, posY
  w.clear()
  w.draw_text(text="Select BW", x = 31, y = 11, font_size=18, color="#FFcccc")
  w.draw_text(text="Select BW", x = 30, y = 10, font_size=18, color="#FF0000")
  displayBox(" 7.8", 20, 60, 60, 40, 4, "#003e7f", lambda:setBW(0))
  displayBox("10.4", 90, 60, 60, 40, 4, "#003e7f", lambda:setBW(1))
  displayBox("15.6", 160, 60, 60, 40, 4, "#003e7f", lambda:setBW(2))
  displayBox("20.8", 20, 110, 60, 40, 4, "#003e7f", lambda:setBW(3))
  displayBox("31.2", 90, 110, 60, 40, 4, "#003e7f", lambda:setBW(4))
  displayBox("41.7", 160, 110, 60, 40, 4, "#003e7f", lambda:setBW(5))
  displayBox("62.5", 20, 160, 60, 40, 4, "#003e7f", lambda:setBW(6))
  displayBox("125", 90, 160, 60, 40, 4, "#003e7f", lambda:setBW(7))
  displayBox("250", 160, 160, 60, 40, 4, "#003e7f", lambda:setBW(8))
  displayBox("500", 20, 210, 60, 40, 4, "#003e7f", lambda:setBW(9))
  displayBox("  esc", 90, 210, 80, 40, 4, "#003e7f", drawMainMenu)
  w.draw_text(text=f'BW is currently set to {myBWs[BW]} KHz', x = 3, y = 298, font_size=12, color="#3333FF")
  w.draw_text(text=f'BW is currently set to {myBWs[BW]} KHz', x = 2, y = 297, font_size=12, color="#3333FF")
  posY = 260
  lastInteraction = time.time()

def doCR():
  global w, CR, posY
  w.clear()
  w.draw_text(text="Select CR", x = 31, y = 11, font_size=18, color="#FFcccc")
  w.draw_text(text="Select CR", x = 30, y = 10, font_size=18, color="#FF0000")
  displayBox(" 4/5", 20, 60, 60, 40, 4, "#003e7f", lambda:setCR(5))
  displayBox(" 4/6", 90, 60, 60, 40, 4, "#003e7f", lambda:setCR(6))
  displayBox(" 4/7", 160, 60, 60, 40, 4, "#003e7f", lambda:setCR(7))
  displayBox(" 4/8", 20, 110, 60, 40, 4, "#003e7f", lambda:setCR(8))
  displayBox("  esc", 90, 110, 80, 40, 4, "#003e7f", drawMainMenu)
  w.draw_text(text=f'CR is currently set to 4/{CR}', x = 3, y = 298, font_size=12, color="#3333FF")
  w.draw_text(text=f'CR is currently set to 4/{CR}', x = 2, y = 297, font_size=12, color="#3333FF")
  posY = 160
  lastInteraction = time.time()

def drawMainMenu():
  global w, posY
  w.clear()
  w.draw_text(text="LoRa Manayer", x = 31, y = 11, font_size=18, color="#FFcccc")
  w.draw_text(text="LoRa Manayer", x = 30, y = 10, font_size=18, color="#FF0000")
  #w.add_button(x=60, y=100, w=100, h=30, text="PING", origin='center', onclick = sendPING)
  displayBox("ping", 20, 60, 60, 40, 4, "#003e7f", btnPING)
  displayBox(" AP", 90, 60, 60, 40, 4, "#003e7f", goAP)
  displayBox(" SF", 160, 60, 60, 40, 4, "#003e7f", doSF)
  displayBox("BW", 20, 110, 60, 40, 4, "#003e7f", doBW)
  displayBox(" CR", 90, 110, 60, 40, 4, "#003e7f", doCR)
  displayBox("OFF", 160, 110, 60, 40, 4, "#1d0902", drawBlackScreen)
  posY = 160
  lastInteraction = time.time()

def drawBlackScreen():
  global screenOFF, lastInteraction, w
  screenOFF = True
  w.clear()
  w.fill_rect(x=0, y=0, w=240, h=320, color = "#000000")
  w.add_button(x=120, y=288, w=100, h=30, text="wake up", origin='left', onclick=drawMainMenu)
  lastInteraction = time.time()

def screenON():
  global screenOFF
  print("Screen on!")
  screenOFF = False
  drawMainMenu()

w.draw_text(text=f" - Frequency {myFreq}", x = 10, y = posY, font_size=12, color="#3333FF")
posY += 20
cmd = f'/fq {myFreq}\n'.encode('ascii')
ss.write(bytes(cmd))
time.sleep(1)

w.draw_text(text=f" - SF {SF}", x = 10, y = posY, font_size=12, color="#3333FF")
posY += 20
cmd = f'/sf {SF}\n'.encode('ascii')
ss.write(bytes(cmd))
time.sleep(1)

w.draw_text(text=f" - BW {BW}", x = 10, y = posY, font_size=12, color="#3333FF")
posY += 20
cmd = f'/bw {BW}\n'.encode('ascii')
ss.write(bytes(cmd))
time.sleep(1)

w.draw_text(text=f" - CR 4/{CR}", x = 10, y = posY, font_size=12, color="#3333FF")
posY += 20
cmd = f'/cr {CR}\n'.encode('ascii')
ss.write(bytes(cmd))
time.sleep(1)

w.draw_text(text=f" - Autoping {apFreq}", x = 10, y = posY, font_size=12, color="#3333FF")
posY += 20
cmd = f'/ap {apFreq}\n'.encode('ascii')
ss.write(bytes(cmd))
drawMainMenu()

lastInteraction = time.time()
buffer = ''
while True:
  n = ss.in_waiting
  while n > 0:
    incoming = ss.read(n).replace(b'\r', b'')
    try:
      buffer += incoming.decode('ascii')
    except:
      print(incoming)
    time.sleep(0.5)
    n = ss.in_waiting
  if buffer.count('\n') > 0:
    # we have lines
    if screenOFF == True:
      screenON()
      lastInteraction = time.time()
    buffer = buffer.split('\n')
    j = len(buffer)-1
    for i in range(0, j):
      s = buffer[i]
      if s != '':
        try:
          obj = json.loads(s)
          t=obj.get('type')
          m=obj.get('msg')
          if t == None or m == None:
            print(s)
            scrollBuffer.append(s)
          else:
            if t == 'incoming':
              m = binascii.a2b_base64(m)
              try:
                obj = json.loads(m)
                m = '\n'
                scrollBuffer.append(t)
                for x in obj.keys():
                  m += '    ' + x + ': ' + obj[x] + '\n'
                  scrollBuffer.append(x + ': ' + obj[x])
              except:
                scrollBuffer.append(f"{t}:\t{m}")
                pass
            print(f"{t}:\t{m}")
        except:
          print(f"Not JSON: '{s}'")
    buffer = buffer[j]
    nLines = int((320-posY-22) / 18)
    if len(scrollBuffer) > nLines:
      scrollBuffer.reverse()
      while len(scrollBuffer) > nLines:
        scrollBuffer.pop()
      scrollBuffer.reverse()
    if screenOFF == False:
      w.fill_rect(x=0, y=posY, w=240, h=320-posY, color = "#ffffff")
      yy = posY
      for x in scrollBuffer:
        w.draw_text(text=x, x = 10, y = yy, font_size=12, color="#3333FF")
        yy += 18
  if eraseStatus > -1 and screenOFF == False:
    if time.time() - eraseStatus > 5:
      logSys("")
      eraseStatus = -1
  if time.time() - lastInteraction > 120 and screenOFF == False:
    # turn screen off, or as close as can be.
    print("Screen off!")
    drawBlackScreen()
