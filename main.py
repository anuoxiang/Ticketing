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
import urllib
import urllib2  # 网络访问
import json  # JSON解析
from datetime import datetime  # 日期处理
import time  # 多线程控制
import thread
import random


class TxtInfo:
    #initT = int(time.time())
    def __init__(self, name):
        self.initTime = int(time.time())
        self.name = name# + str(int(time.time()) - TxtInfo.initT)

    def isDone(self):
        tf = int(time.time()) - self.initTime > txtDisplayDelay
        return tf

    def init(self):
        return self.initTime


# 摄像头预览图
def GetPrevImg():
    stream = io.BytesIO()  # Capture into in-memory stream
    camera.capture(stream, use_video_port=True, format='jpeg')
    stream.seek(0)
    image = Image.open(stream)
    image.load()
    # stream.readinto(rgb)
    # stream.close()
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
    values = {'Password': 'this is my first', 'QRCode': urllib.quote(content.encode('gb2312'))}
    params = str(values)
    headers = {"Content-type": "application/json", "Accept": "application/json"}
    req = urllib2.Request(url, params, headers)
    response = urllib2.urlopen(req)
    requeststr = response.read()
    jsondata = json.loads(requeststr)
    if jsondata["Msg"] == "OK":
        fh = open("hashcode.jpg", "wb")
        fh.write(jsondata["Code"].decode('base64'))
        fh.close()
        Print(jsondata["ItemName"], "hashcode.jpg")
    else:
        Echo(jsondata["Msg"])


# 打印
def Print(item, code):
    Echo(u"正在准备打印...")
    usb = printer.Usb(0x0416, 0x5011, 0, out_ep=0x01)

    Echo("打印...")
    usb.image('logo.bmp')
    usb.set('CENTER', 'B', 'B', 1, 2)
    usb.text(u"第一八佰伴岁末疯抢\n\n".encode('gbk'))
    # 内容正文开始
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
    usb.image(code)
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
        screen.blit(txtBg, (0, txtInfoTop + label.get_height() * infos.index(info)))
        screen.blit(label, ((width - label.get_width()) / 2,
                            txtInfoTop + label.get_height() * infos.index(info)))

    # 过期的移走
    for info in infos:
        if int(time.time()) - info.initTime >= txtDisplayDelay:
            infos.remove(info)

    # 显示时间
    timenow = timefont.render(datetime.now().strftime("%m/%d %H:%M:%S"), 1, (32, 87, 137))
    screen.blit(timenow,(10,930))

os.putenv('SDL_VIDEODRIVER', 'fbcon')
# os.putenv('SDL_FBDEV'      , '/dev/fb1')

# 界面初始化
pygame.init()
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/mouse0')
size = width, height = 600, 1024
screen = pygame.display.set_mode(size)
# screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
myfont = pygame.font.Font("msyhbd.ttc", 32)  # 雅黑粗体
# myfont = pygame.font.SysFont("wenquanyizenhei", 30)
sizeData = [  # Camera parameters for different size settings
              # Full res      Viewfinder  Crop window
              [(2592, 1944), (320, 240), (0.0, 0.0, 1.0, 1.0)],  # Large
              [(1920, 1080), (320, 180), (0.1296, 0.2222, 0.7408, 0.5556)],  # Med
              [(1440, 1080), (420, 420), (0.2222, 0.2222, 0.5556, 0.5556)]]  # Small
sizeMode = 2
txtInfoTop = 100  # 从y坐标哪里开始显示
txtDisplayDelay = 5  # 提示信息显示5秒
pygame.mouse.set_visible(False)

# 摄像头的定义
rgb = bytearray(sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)
camera = picamera.PiCamera()
camera.resolution = sizeData[sizeMode][1]
# camera.rotation = 180
camera.crop = sizeData[sizeMode][2]
MaxWaitingTime = 30  # 30秒摄像头启动等待
begTimer = 0
CameraMask = pygame.image.load('CameraMask.png')
CameraMaskRect = CameraMask.get_rect()
CameraMaskRect.x = 90
CameraMaskRect.y = 486
speed = [0, 20]
Scanner = pygame.image.load('Scanner.png')
ScannerRect = Scanner.get_rect()
ScannerRect.x = 140
ScannerRect.y = 536

# 背景
bg = pygame.image.load('home.jpg')
pygame.mouse.set_pos(300, 512)
pos = None

# 信息提示
infos = []
txtBg = pygame.image.load('txtBackground.png')
txtDisplayDelay = 5

# 时间提示
timefont = pygame.font.Font("msyhbd.ttc", 12)

# runCamera = False
while 1:
    # 背景绘图
    screen.blit(bg, (0, 0))
    ScannerRect = ScannerRect.move(speed)
    if ScannerRect.top > 854:
        ScannerRect.top = 537

    label = None
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            camera.close()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            Echo(u'不要点我呀~请直接扫码')

    if label != None:
        screen.blit(label, ((width - label.get_width()) / 2, 100))

    image = GetPrevImg()
    img = pygame.image.fromstring(image.tobytes(), image.size, image.mode)

    if img:
        # 摄像头预览图的位置
        screen.blit(img, (90, 486))
        screen.blit(CameraMask, CameraMaskRect)
        screen.blit(Scanner, ScannerRect)
        # 扫码读取
        txt = ScanCode(image)

        if txt != None:
            CheckQRCode(txt)
            runCamera = False
    Display()


    pygame.display.flip()
