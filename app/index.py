#!/usr/bin/env python
# coding=utf-8

from flask import request, abort, url_for, render_template
import xml.etree.ElementTree as ET
import hashlib
import requests
import json
import os

from app import app, APPID, APPSECRET
from user import update_user, get_user
from ext import get_point

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if request.args.get('timestamp') == None:
            return abort(403)
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')
        token = os.getenv("TOKEN") or 'weixin'
        li = [token, timestamp, nonce]
        li.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, li)
        hashcode = sha1.hexdigest()
        if hashcode == request.args.get('signature'):
            return echostr
        else:
            return abort(403)
    elif request.method == 'POST':
        message = request.data  # 接收用户消息
        root = ET.fromstring(message)  # 解析xml
        to_user_name = root.findall('ToUserName')[0].text  # 开发者账号
        from_user_name = root.findall('FromUserName')[0].text  # 用户微信id
        create_time = root.findall('CreateTime')[0].text  # 消息创建时间 （整型）
        message_type = root.findall('MsgType')[0].text # 消息类型text
        try:
            content = root.findall('Content')[0].text # 消息内容
        except:
            content = ''
        try:
            message_id = root.findall('MsgId')[0].text # 消息的ID
        except:
            message_id = ''
        try:
            event  = root.findall('Event')[0].text # 事件类型
        except:
            event = ''
        try:
            event_key = root.findall('EventKey')[0].text or ''  # 事件Key值
        except:
            event_key = ''

        if event == 'CLICK':
            userinfo = get_user(from_user_name)
            if event_key == 'SCHEDULE':
                if userinfo is None:
                    return text % (from_user_name, to_user_name, create_time, "您的微信号未与学号绑定，请您先绑定账号")
                return text % (from_user_name, to_user_name, create_time, userinfo['no'] + u"的课表")
            elif event_key == 'LIBRARY':
                if userinfo is None:
                    return text % (from_user_name, to_user_name, create_time, "您的微信号未与学号绑定，请您先绑定账号")
                return text % (from_user_name, to_user_name, create_time, userinfo['no'] + u"的图书馆借阅信息")
            elif event_key == 'ACCOUNT':
                if userinfo is not None:
                    return info % (from_user_name, to_user_name, create_time, 
                               u"账号已绑定",
                               u"您的微信号已与学号(" + userinfo['no'] + u")绑定，您可以点击此处来更改学号或者更新密码",
                               u"https://open.weixin.qq.com/connect/oauth2/authorize?appid=" + APPID +
                               u"&redirect_uri=" + url_for('bind', _external=True) +
                               u"&response_type=code&scope=snsapi_base&state=ACCOUNT#wechat_redirect")

                return info % (from_user_name, to_user_name, create_time, 
                               "绑定账号信息",
                               "把微信号与学号，教务处账号，图书馆账号绑定，然后就把剩下的查询工作交给我们吧！",
                               "https://open.weixin.qq.com/connect/oauth2/authorize?appid=" + APPID +
                               "&redirect_uri=" + url_for('bind', _external=True) +
                               "&response_type=code&scope=snsapi_base&state=ACCOUNT#wechat_redirect")
            elif event_key == 'STUDENT_POINT':
                if userinfo is None:
                    return text % (from_user_name, to_user_name, create_time, "您的微信号未与学号绑定，请您先绑定账号")
                point = get_point(userinfo)
                return text % (from_user_name, to_user_name, create_time, userinfo['no'] + u"目前的绩点是：" + str(point['point']))
            elif event_key == 'STUDENT_GRADE':
                if userinfo is None:
                    return text % (from_user_name, to_user_name, create_time, "您的微信号未与学号绑定，请您先绑定账号")
                return text % (from_user_name, to_user_name, create_time, userinfo['no'] + u"的学期成绩")

        return info % (from_user_name, to_user_name, create_time, "梦续代码", "念念不忘，必有回响", "http://www.ihypo.net")


@app.route('/bind', methods=['GET', 'POST'])
def bind():

    if request.method == 'GET':
        code = request.args.get('code') or ''
        params = {
            'appid': APPID,
            'secret': APPSECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
        res = requests.get("https://api.weixin.qq.com/sns/oauth2/access_token", params=params)
        dic = json.loads(res.text)
        return render_template('bind.html', id=dic['openid'])
    elif request.method == 'POST':
        student = {
            'id': request.form['id'],
            'no': request.form['no'],
            'jwch': request.form['jwch'],
            'library': request.form['library']
        }

        ans = update_user(student)

        if ans is True:
            return "SUCCESS"
        return "ERROR"


info = """
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[news]]></MsgType>
<ArticleCount>1</ArticleCount>
<Articles>
<item>
<Title><![CDATA[%s]]></Title>
<Description><![CDATA[%s]]></Description>
<Url><![CDATA[%s]]></Url>
</item>
</xml>
"""

text="""
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[%s]]></Content>
</xml>
"""
