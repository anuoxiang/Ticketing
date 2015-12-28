# -*- coding:utf-8 -*-
__author__ = '炜强'
import urllib2  # 网络访问
import urllib
import json  # JSON解析

def Print(a1,a2):
    print a1,a2

def Echo(a1):
    print a1

content = u'123'
print content
url = "http://bbb.dgshare.cn/Ticketing/Verify"
values = {'Password': 'this is my first', 'QRCode': urllib.quote(content.encode('gb2312'))}

params = str(values)
headers = {"Content-type": "application/json", "Accept": "application/json"}
req = urllib2.Request(url, params, headers)
print params
response = urllib2.urlopen(req)
requeststr = response.read()
jsondata = json.loads(requeststr)
if jsondata["Msg"] == "OK":
    Print(jsondata["ItemName"], jsondata["Code"])
else:
    Echo(jsondata["Msg"])


