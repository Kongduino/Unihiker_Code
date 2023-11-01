import time, gc
from unihiker import GUI

btnPing = None


gc.enable()
gui = GUI()



def ping():
  print("ping")

def MainMenu():
  global gui, btnPing
  bg = gui.fill_rect(x=0, y=0, w=240, h=320, color='#026BC6')
  lbl0 = gui.draw_text(x=60, y=10, text="LoRa老板", color='white', font_family='WenQuanYi Zen Hei Sharp',font_size=18)
  btnPing = gui.add_button(x=40, y=60, w=60, h=30, text="PING", origin='center', onclick=ping)

MainMenu()

while True:
  pass



