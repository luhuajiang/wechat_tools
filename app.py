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
from flask import render_template
from flask import send_file
from flask import request


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
@app.route('/getUUID')
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
        return uuid
    return 'error' 


@app.route('/isScan/<uuid>')
def isScan(uuid):
    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % ('1', uuid, int(time.time()))

    request = urllib.request.Request(url=url)
    response = urllib.request.urlopen(request)
    data = response.read()
    return str(data)


@app.route('/isLogin', methods = ['POST'])
def isLogin():
    redirect_uri = request.values.get('redirect_uri', 0)
    print(redirect_uri)
    global skey, wxsid, wxuin, pass_ticket, BaseRequest

    request1 = urllib.request.Request(url=redirect_uri)
    response = urllib.request.urlopen(request1)
    data = response.read()
    print(str(data))
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
        'pass_ticket': pass_ticket,
    }

    return json.dumps(BaseRequest) 

@app.route('/getConstact')
def getConstact():
    pass_ticket = request.values.get('pass_ticket', 0)
    skey = request.values.get('skey', 0)
    url = base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (pass_ticket, skey, int(time.time()))

    request = urllib.request.Request(url=url)
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = urllib.request.urlopen(request)
    data = response.read()

    if DEBUG:
        f = open(os.getcwd() + '/webwxgetcontact.json', 'wb')
        f.write(data)
        f.close()

    # print data
    data = data.decode('utf-8', 'replace')

    dic = json.loads(data)
    MemberList = dic['MemberList']

    # 倒序遍历,不然删除的时候出问题..
    SpecialUsers = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail', 'fmessage', 'tmessage', 'qmessage',
                    'qqsync', 'floatbottle', 'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 'readerapp', 'blogapp',
                    'facebookapp', 'masssendapp', 'meishiapp', 'feedsapp', 'voip', 'blogappweixin', 'weixin',
                    'brandsessionholder', 'weixinreminder', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c',
                    'officialaccounts', 'notification_messages', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'wxitil',
                    'userexperience_alarm', 'notification_messages']
    for i in range(len(MemberList) - 1, -1, -1):
        Member = MemberList[i]
        if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
            MemberList.remove(Member)
        elif Member['UserName'] in SpecialUsers:  # 特殊账号
            MemberList.remove(Member)
        elif Member['UserName'].find('@@') != -1:  # 群聊
            MemberList.remove(Member)
        elif Member['UserName'] == My['UserName']:  # 自己
            MemberList.remove(Member)

    return json.dumps(MemberList)

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




