# -*- coding:utf-8 -*-
__author__ = 'Django'

import pygame
import sys
import os
import picamera
import io
import zbarlight
from PIL import Image
from escpos import *  # 打印机
import re  # 正则表达式
import urllib2  # 网络访问
import json  # JSON解析
from datetime import datetime  # 日期处理
import time  # 多线程控制
import thread
import random

class TxtInfo:
    txtDisplayDelay = 5
    def __init__(self, name):
        self.name = name
        self.initTime = time.time()

    def isDone(self):
        return time.time() - self.initTime > txtDisplayDelay


# 摄像头预览图
def GetPrevImg():
    stream = io.BytesIO()  # Capture into in-memory stream
    camera.capture(stream, use_video_port=True, format='jpeg')
    stream.seek(0)
    image = Image.open(stream)
    image.load()
    stream.readinto(rgb)
    stream.close()
    return image


# 二维码扫描
def ScanCode(image):
    txt = None
    codes = zbarlight.scan_codes('qrcode', image)
    if codes != None:
        txt = codes[0].decode('utf-8')
    return txt


# 网络验证
def CheckQRCode(content):
    url = "http://bbb.dgshare.cn/Ticketing/Verify"
    values = {'Password':'this is my first', 'QRCode':content.encode('utf-8')}
    params = str(values)
    headers = {"Content-type":"application/json","Accept": "application/json"}
    req = urllib2.Request(url, params, headers)
    response = urllib2.urlopen(req)
    requeststr = response.read()
    jsondata = json.loads(requeststr)
    if jsondata["Msg"]=="OK":
        Print(jsondata["ItemName"], jsondata["Code"])
    else:
        Echo(jsondata["Msg"])

# 打印
def Print(item,code):
    Echo("准备打印...")
    usb = printer.Usb(0x0416, 0x5011, 0, out_ep=0x01)

    Echo("打印...")
    usb.image('logo.bmp')
    usb.set('CENTER', 'B', 'B', 1, 2)
    usb.text(u"第一八佰伴岁末疯抢\n\n".encode('gbk'))
    #内容正文开始
    usb.set('LEFT', 'B', 'B', 1, 2)
    usb.text(item.encode('gbk') + "\n")

    usb.set('LEFT', 'A', 'A', 1, 1)
    usb.text(u"打印时间:%s\n".encode('gbk') % datetime.now().strftime("%m/%d %H:%M:%S"))

    '''
    usb.set('LEFT', 'B', 'A', 1, 1)
    usb.text(u"交易账户：".encode('gbk'))
    usb.set('LEFT', 'B', 'B', 1, 1)
    usb.text(u"测试账户\n".encode('gbk'))
    '''
    usb.text("\n\n")
    usb.set('CENTER', '', '', 1, 1)
    usb.text(u"校验码\n".encode('gbk'))
    # usb.barcode('9787900420206', 'EAN13', 64, 2, '', '')
    usb.qr(code)
    usb.text("\n\n")

    usb.set('LEFT', 'A', 'A', 1, 1)
    usb.text(u"    凭本券当场换领相应品牌的销售通知单，本券仅限当场兑换有效，如不兑换视为自动放弃，本券作废。\n\n".encode('gbk'))

    usb.set('CENTER', '', '', 1, 1)
    usb.text(u"技术支持\n坤鼎文化发展".encode('gbk') + "\n")

    usb.set('CENTER', '', '', 1, 1)
    usb.text(u"2016".encode('gbk') + "\n")

    usb.text("------------------------------\n")
    #

    usb.cut('full')


def Echo(content):
    infos.append(TxtInfo(content))
    Display()

def Display():
    for info in infos:
        label = myfont.render(info.name, 1, (32, 87, 137))
        screen.blit(txtBg,(0,txtInfoTop+ label.get_height()*infos.index(info)))
        screen.blit(label,((width - label.get_width()) / 2,
                     txtInfoTop + label.get_height()*infos.index(info)))

    #过期的移走
    for info in infos:
        if not info.isDone:
            infos.remove(info)



os.putenv('SDL_VIDEODRIVER', 'fbcon')
# os.putenv('SDL_FBDEV'      , '/dev/fb1')



# 界面初始化
pygame.init()
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/mouse0')
size = width, height = 600, 1024
screen = pygame.display.set_mode(size)
# screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
myfont = pygame.font.Font("msyhbd.ttc", 32)#雅黑粗体
#myfont = pygame.font.SysFont("wenquanyizenhei", 30)
sizeData = [  # Camera parameters for different size settings
              # Full res      Viewfinder  Crop window
              [(2592, 1944), (320, 240), (0.0, 0.0, 1.0, 1.0)],  # Large
              [(1920, 1080), (320, 180), (0.1296, 0.2222, 0.7408, 0.5556)],  # Med
              [(1440, 1080), (320, 240), (0.2222, 0.2222, 0.5556, 0.5556)]]  # Small
sizeMode = 2
txtInfoTop = 100        #从y坐标哪里开始显示
txtDisplayDelay = 5     #提示信息显示5秒
pygame.mouse.set_visible(False)

# 摄像头的定义
rgb = bytearray(sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)
camera = picamera.PiCamera()
camera.resolution = sizeData[sizeMode][1]
#camera.rotation = 180
camera.crop = sizeData[sizeMode][2]
MaxWaitingTime = 30  # 30秒摄像头启动等待
begTimer = 0
border = pygame.image.load('viewBorder.png')
borderrect = border.get_rect()
borderrect.x = 140
borderrect.y = 670

# 按钮定义
speed = [0, -2]
button = pygame.image.load('exchange.png')
buttonOrgPos = {"x": 140, "y": 457}# 原始位置
buttonrect = button.get_rect()
buttonrect.x = buttonOrgPos["x"]
buttonrect.y = buttonOrgPos["y"]

#背景
bg = pygame.image.load('home.jpg')
pygame.mouse.set_pos(300, 512)
pos = None

# 信息提示
infos = []

txtBg = pygame.image.load('txtBackground.png')


#runCamera = False
while 1:
    # 背景绘图
    screen.blit(bg, (0, 0))

    buttonrect = buttonrect.move(speed)
    if buttonrect.top < buttonOrgPos["y"] - 16 or buttonrect.top > buttonOrgPos["y"]:
        speed[1] = -speed[1]

    label = None
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            camera.close()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            Echo(u'点我呀')

    if label != None:
        screen.blit(label, ((width - label.get_width()) / 2, 100))
    screen.blit(button, buttonrect)

    image = GetPrevImg()
    img = pygame.image.fromstring(image.tobytes(), image.size, image.mode)

    if img:
        # 摄像头预览图的位置
        screen.blit(img, (140, 670))
        screen.blit(border,borderrect)
        # 扫码读取
        txt = ScanCode(image)
        if txt != None:
            CheckQRCode(txt)
            runCamera = False
    Display()

    pygame.display.flip()
