#!/usr/bin/python3
import time, requests, re
from os import path, remove
from unihiker import GUI
from pinpong.board import Board, I2C
from pinpong.libs.dfrobot_bme280 import BME280
from pinpong.libs.dfrobot_bme680 import DFRobot_BME680

Board("UNIHIKER").begin()
w = GUI()
w.clear()
w.draw_text(text="Loading...", x = 61, y = 111, font_size=18, color="#FFcccc")
w.draw_text(text="Loading...", x = 60, y = 110, font_size=18, color="#FF0000")

class Enviro:
  getData = None
  obj = None
  name = None

temp = 0
humi = 0
Pa = 0
press = 0
bme280 = None
bme680 = None
sensors = []

def get280data(obj):
  global temp, humi, Pa, press
  temp = obj.temp_c()
  humi = obj.humidity()
  Pa = obj.press_pa()
  temp = int(temp * 100)/100
  humi = int(humi * 100)/100
  press = int(Pa)/100

def get680data(cjmcu):
  global temp, humi, Pa, press
  temp = cjmcu.data.temperature
  humi = cjmcu.data.humidity
  Pa = cjmcu.data.pressure
  press = Pa/100

posY = 150
try:
  bme280 = BME280(0x76)
  enviro280 = Enviro()
  enviro280.getData = get280data
  enviro280.obj = bme280
  enviro280.name = "BME280"
  sensors.append(enviro280)
  w.draw_text(text="* BME280", x = 10, y = posY, font_size=13, color="#0000FF")
except:
  pass

posY += 20

try:
  bme680 = DFRobot_BME680()
  enviro680 = Enviro()
  enviro680.getData = get680data
  enviro680.obj = bme680
  enviro680.name = "BME680"
  sensors.append(enviro680)
  w.draw_text(text="* BME680", x = 10, y = posY, font_size=13, color="#0000FF")
except:
  pass

posY += 20

sensorCount = len(sensors)
currentSensor = 0

leftPos = 50
url = "https://www.hko.gov.hk/textonly/v2/forecast/text_readings_e.htm"
MSL = 101300

def getMSL():
  global MSL
  try:
    r = requests.get(url)
    s = r.text
    t = s.split('(hPa)')
    t = t[1].split('10-Minute Mean Visibility')
    s = t[0].strip().replace('\n\n', '\n')
    t = re.sub('  +', '\t', s).split('\n')
    for s in t:
      if s.startswith('Wetland'):
        u = s.split('\t')
        MSL = int(float(u[1])*100)
        print(f'Found it! {MSL/100} HPa')
  except:
    pass

getMSL()
lastCheck = int(time.time())-30 # seconds

while True:
  timeNow = int(time.time()) # seconds
  if timeNow - lastCheck > 300: #300 s = 5 mn
    getMSL()
    lastCheck = timeNow
  w.clear()
  if path.isfile("MSL.txt"):
    f = open("MSL.txt")
    MSL = f.readline().strip()
    txt = f"MSL: {MSL}"
    w.draw_text(text=txt, x = 5, y = 300, font_size=12, color="#000000")
    MSL = int(float(MSL)*100)
    f.close()
    remove("MSL.txt")
  sensor = sensors[currentSensor]
  sensor.getData(sensor.obj)
  w.draw_text(text=sensor.name, x = 80, y = 10, font_size=18, color="#FF0000")
  w.draw_text(text=sensor.name, x = 81, y = 11, font_size=18, color="#FF0000")
  currentSensor += 1
  if currentSensor == sensorCount:
    currentSensor = 0
  print(f"Temperature: {temp}° C, Humidity: {humi}%, Pressure: {press}")
  
  txt = f"T: {temp} C"
  clr = "#008b8b" # Normal
  fClr = "#FFFFFF" # Normal
  if temp < 20:
    clr = "#0000FF" #cold
    fClr = "#e0ffff"
  elif temp > 28:
    clr = "#FF0000"
    fClr = "#00ffff"
  w.fill_round_rect(x=leftPos, y=80, w=150, h=40, r=4, color=clr, fill=clr)
  w.fill_round_rect(x=leftPos+3, y=83, w=144, h=34, r=4, color=fClr, fill=fClr)
  w.draw_text(text=txt, x = leftPos+10, y=85, font_size=15, color=clr)

  clr = "#008b8b" # Normal
  fClr = "#FFFFFF" # Normal
  if humi < 40:
    clr = "#0000FF" #dry
    fClr = "#e0ffff"
  elif humi > 65:
    clr = "#FF0000"
    fClr = "#00ffff"
  w.fill_round_rect(x=leftPos, y=130, w=150, h=40, r=4, color=clr, fill=clr)
  w.fill_round_rect(x=leftPos+3, y=133, w=144, h=34, r=4, color=fClr, fill=fClr)
  txt = f"H: {humi}%"
  w.draw_text(text=txt, x = leftPos+10, y=135, font_size=15, color=clr)

  clr = "#008b8b" # Normal
  fClr = "#FFFFFF" # Normal
  w.fill_round_rect(x=leftPos, y=180, w=150, h=40, r=4, color=clr, fill=clr)
  w.fill_round_rect(x=leftPos+3, y=183, w=144, h=34, r=4, color=fClr, fill=fClr)
  txt = f"{press} HPa"
  w.draw_text(text=txt, x = leftPos+10, y=185, font_size=15, color=clr)
  
  H = 44330 * (1 - pow(Pa/MSL, (1/5.255)))
  H = int(H*100)/100
  print(f"Altitude: {H} m")

  clr = "#008b8b" # Normal
  fClr = "#FFFFFF" # Normal
  w.fill_round_rect(x=leftPos, y=230, w=150, h=40, r=4, color=clr, fill=clr)
  w.fill_round_rect(x=leftPos+3, y=233, w=144, h=34, r=4, color=fClr, fill=fClr)
  txt = f"Alt: {H} m"
  w.draw_text(text=txt, x = leftPos+10, y=235, font_size=15, color=clr)
  
  time.sleep(10)
