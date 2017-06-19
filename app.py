#!/usr/bin/env python
# coding=utf-8
import os
import urllib.request, urllib.parse, urllib.error
import re
import http.cookiejar
import time
import xml.dom.minidom
import json
import sys
import math
import subprocess
import json
import threading
import logging
from flask import Flask
from io import * 
from io import * 
from flask import render_template
from flask import send_file


app = Flask(__name__)
DEBUG = True

QRImageName = './qrcode.jpg'
QRImagePath = os.getcwd() + '/qrcode.jpg' 


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/showLogin')
def showLogin():
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    urllib.request.install_opener(opener)

    if not getUUID():
        return 'getUUID failed'
    getQRImage()
    return send_file(QRImageName, mimetype='image/jpg')

def getQRImage():
    url = 'https://login.weixin.qq.com/qrcode/' + uuid
    params = {
        't': 'webwx',
        '_': int(time.time()),
    }
    request = urllib.request.Request(url = url, data = urllib.parse.urlencode(params).encode(encoding = 'UTF-8'))
    response = urllib.request.urlopen(request)

    f = open(QRImagePath, 'wb')
    f.write(response.read())
    f.close()

def getUUID():
    global uuid

    url = 'https://login.weixin.qq.com/jslogin'
    params = {
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
        'lang': 'zh_CN',
        '_': int(time.time()),
    }
    
    request = urllib.request.Request(url=url, data=urllib.parse.urlencode(params).encode(encoding='UTF8'))
    response = urllib.request.urlopen(request)
    data = response.read()
    print(data)
    # print data
    # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
    pm = re.search(regx, str(data))

    code = pm.group(1)
    uuid = pm.group(2)

    if code == '200':
        return True

    return False


@app.route('/isScan')
def isScan():
    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (tip, uuid, int(time.time()))

    request = urllib.request.Request(url=url)
    response = urllib.request.urlopen(request)
    data = response.read()

    regx = r'window.code=(\d+);'
    pm = re.search(regx, str(data))

    code = pm.group(1)

    if code == '201':
        return '成功扫描,请在手机上点击确认以登录'

    elif code == '200':
        print(u'login ...')
        regx = r'window.redirect_uri="(\S+?)";'
        pm = re.search(regx, str(data))
        redirect_uri = pm.group(1) + '&fun=new'
        print(redirect_uri)
        base_uri = redirect_uri[:redirect_uri.rfind('/')]
        print(base_uri)
    elif code == '408':
        pass
    return code

@app.route('/isLogin')
def isLogin(redirect_uri):
    global skey, wxsid, wxuin, pass_ticket, BaseRequest

    request = urllib.request.Request(url=redirect_uri)
    response = urllib.request.urlopen(request)
    data = response.read()

    # print data

    '''
		<error>
			<ret>0</ret>
			<message>OK</message>
			<skey>xxx</skey>
			<wxsid>xxx</wxsid>
			<wxuin>xxx</wxuin>
			<pass_ticket>xxx</pass_ticket>
			<isgrayscale>1</isgrayscale>
		</error>
	'''

    doc = xml.dom.minidom.parseString(data)
    root = doc.documentElement

    for node in root.childNodes:
        if node.nodeName == 'skey':
            skey = node.childNodes[0].data
        elif node.nodeName == 'wxsid':
            wxsid = node.childNodes[0].data
        elif node.nodeName == 'wxuin':
            wxuin = node.childNodes[0].data
        elif node.nodeName == 'pass_ticket':
            pass_ticket = node.childNodes[0].data

    # print 'skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid, wxuin, pass_ticket)

    if skey == '' or wxsid == '' or wxuin == '' or pass_ticket == '':
        return False

    BaseRequest = {
        'Uin': int(wxuin),
        'Sid': wxsid,
        'Skey': skey,
        'DeviceID': deviceId,
    }

    return json.dumps(BaseRequest) 

@app.route('/webwxinit')
def webwxinit(base_uri,BaseRequest):
    url = base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (pass_ticket, skey, int(time.time()))
    params = {
        'BaseRequest': BaseRequest
    }

    request = urllib.request.Request(url=url, data=json.dumps(params).encode('utf-8'))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = urllib.request.urlopen(request)
    data = response.read()

    if DEBUG:
        f = open(os.getcwd() + '/webwxinit.json', 'wb')
        f.write(data)
        f.close()

    # print data

    global ContactList, My
    dic = json.loads(data.decode())
    ContactList = dic['ContactList']
    My = dic['User']

    ErrMsg = dic['BaseResponse']['ErrMsg']
    # if len(ErrMsg) > 0:
    # 	print ErrMsg

    Ret = dic['BaseResponse']['Ret']
    if Ret != 0:
        return False

    #获得用户与服务器同步的信息
    #SyncKey = dic['SyncKey']

    return json.dumps(ContactList) 

@app.route('/sendMsg/<message>/<user_name>')
def sendMsg():
    t = threading.Thread(target = sendMsg, args=(My['UserName'], userName, message,500))
    t.start()
    t.join()
    return 200

if __name__ == '__main__':
    app.debug = True
    app.run()




