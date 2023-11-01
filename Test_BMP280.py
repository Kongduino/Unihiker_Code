#!/usr/bin/python3
import time
from os import path, remove
from unihiker import GUI
from pinpong.board import Board, I2C
from pinpong.libs.dfrobot_bme280 import BME280
Board("UNIHIKER").begin()
w = GUI()
bme = BME280(0x76)
leftPos = 50
MSL = 101300

while True:
  w.clear()
  if path.isfile("MSL.txt"):
    f = open("MSL.txt")
    MSL = f.readline().strip()
    txt = f"MSL: {MSL}"
    w.draw_text(text=txt, x = 5, y = 300, font_size=12, color="#000000")
    MSL = int(float(MSL)*100)
    f.close()
    remove("MSL.txt")
  temp = bme.temp_c()
  humi = bme.humidity()
  Pa = bme.press_pa()
  temp = int(temp * 100)/100
  humi = int(humi * 100)/100
  press = int(Pa)/100
  print(f"Temperature: {temp}° C, Humidity: {humi}%, Pressure: {press}")
  w.draw_text(text="BMP280", x = 80, y = 10, font_size=18, color="#FF0000")
  w.draw_text(text="BMP280", x = 81, y = 11, font_size=18, color="#FF0000")
  
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
