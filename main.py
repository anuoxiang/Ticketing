# -*- coding:utf-8 -*-
__author__ = 'Django'

import pygame
import sys
import os
import picamera
import io
# import yuv2rgb
import zbarlight
from PIL import Image
from escpos import *        # 打印机
import re                   # 正则表达式
import urllib2              # 网络访问
import json                 # JSON解析
from datetime import datetime  # 日期处理
import time                 # 多线程控制
import thread

os.putenv('SDL_VIDEODRIVER', 'fbcon')
# os.putenv('SDL_FBDEV'      , '/dev/fb1')

# main progress
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

rgb = bytearray(320 * 240 * 3)
yuv = bytearray(320 * 240 * 3 / 2)

pygame.init()
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/mouse0')
size = width, height = 1024, 600
speed = [2, 2]
black = 0, 0, 0

screen = pygame.display.set_mode(size)
camera = picamera.PiCamera()
camera.resolution = (320, 240)
camera.rotation = 180
camera.crop = (0.0, 0.0, 1.0, 1.0)
myfont = pygame.font.SysFont("wenquanyizenhei", 30)
sizeData = [  # Camera parameters for different size settings
              # Full res      Viewfinder  Crop window
              [(2592, 1944), (320, 240), (0.0, 0.0, 1.0, 1.0)],  # Large
              [(1920, 1080), (320, 180), (0.1296, 0.2222, 0.7408, 0.5556)],  # Med
              [(1440, 1080), (320, 240), (0.2222, 0.2222, 0.5556, 0.5556)]]  # Small
sizeMode = 2

ball = pygame.image.load('ball.bmp')
ballrect = ball.get_rect()
# pygame.mouse.set_visible(False)
bg = pygame.image.load('bg.jpg')
pygame.mouse.set_pos(512, 300)
pos = None
while 1:
    ballrect = ballrect.move(speed)
    if ballrect.left < 0 or ballrect.right > width:
        speed[0] = -speed[0]
    if ballrect.top < 0 or ballrect.bottom > height:
        speed[1] = -speed[1]

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            camera.close()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if ((pos[0] > ballrect.left) and (pos[0] < ballrect.right) and
                    (pos[1] > ballrect.top) and (pos[1] < ballrect.bottom)):
                speed = [speed[0] + 1, speed[1] + 1]
                # speed = [3, 3]

    screen.fill(black)
    screen.blit(bg, (0, 0))
    screen.blit(ball, ballrect)
    # display camera
    stream = io.BytesIO()  # Capture into in-memory stream
    camera.capture(stream, use_video_port=True, format='jpeg')
    stream.seek(0)
    image = Image.open(stream)
    image.load()
    # stream.readinto(yuv)  # stream -> YUV buffer
    stream.readinto(rgb)
    stream.close()
    mode = image.mode
    size = image.size
    data = image.tobytes()
    img = pygame.image.fromstring(data, size, mode)
    # yuv2rgb.convert(yuv, rgb, sizeData[sizeMode][1][0],sizeData[sizeMode][1][1])
    # img = pygame.image.frombuffer(rgb,(320,240),'RGB')
    '''img = pygame.image.frombuffer(rgb[0:
      (sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)],
      sizeData[sizeMode][1], 'RGB')
	'''
    if img:
        screen.blit(img, ((1024 - img.get_width()) / 2, (600 - img.get_height()) / 2))
        codes = zbarlight.scan_codes('qrcode', image)
        if codes != None:
            print type(codes)
            txt = codes[0].decode('utf-8')
            label = myfont.render(txt, 1, (255, 255, 0))

            screen.blit(label, ((1024 - label.get_width()) / 2, 100))
            usb = printer.Usb(0x0416, 0x5011, 0, out_ep=0x01)
            usb.set('CENTER', 'B', 'B', 1, 2)
            usb.text(txt.encode('gbk'))

            # if (qr.decode(img)):
            #	label = myfont.render(qr.decode(img).data, 1, (255,255,0))
            #	screen.blit(label, (100, 100))
    if (pos != None):
        pygame.draw.circle(screen, BLUE, pos, 20, 0)
    pygame.display.flip()
