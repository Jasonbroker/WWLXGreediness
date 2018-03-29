import requests
import platform
import os
import subprocess
import time
import re
import json

session = requests.session()
headers = {
    'Host': 's.dianping.com',
    'Connection': 'keep-alive',
    'Content-Length': '1224',
    'Origin': 'http://s.dianping.com',
    'X-Request': 'JSON',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8;',
    'Accept': 'application/json, text/javascript',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

qr_header = {
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}

qr_code_data = session.get('https://www.dianping.com/account/getqrcodeimg', headers=qr_header, stream=True)
QR_CODE = 'QRCode.jpg'

with open(QR_CODE, 'wb') as f:
    f.write(qr_code_data.content)

# 打开图片
if platform.system() == 'Darwin':
    subprocess.call(['open', QR_CODE])
elif platform.system() == 'Linux':
    subprocess.call(['xdg-open', QR_CODE])
else:
    os.startfile(QR_CODE)

status_fetcher_url = 'https://www.dianping.com/account/ajax/queryqrcodestatus'
# get the ticket
token = session.cookies.__getitem__('lgtoken')
print('ticket got: ', token)

status_payload = {'lgtoken': token}
status_header = {
'Accept':'*/*',
'Accept-Encoding':'gzip, deflate, br',
'Accept-Language':'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}
while True:
    r = session.post(status_fetcher_url, headers=status_header, data=status_payload)
    dic = r.json()
    if dic['code']!= 200:
        continue

    status = dic['msg']['status']
    # 0 no scan, 1 scan, 2 scaned
    if status == -1:
        print('验证码过期')
    elif status == 0:
        print('请使用大众点评APP扫描二维码……')
        time.sleep(1)
        continue
    elif status == 1:
        print('已经成功扫描二维码，请在手机点击确认登录')
        time.sleep(1)
    elif status == 2:
        print('成功登录')
        # 目的是拿到浏览器cookies
        print(r.cookies)
        break

# 手机号验证
with open('phone', 'rb') as f:
    phone = f.read().decode()
    # 简单校验
    while len(phone) != 11:
        print("请输入正确的手机号")
        phone = input()
        print('手机号被存为：', phone)

    with open('phone', 'wb') as f:
        f.write(phone.encode())

#报名链接
url = "http://s.dianping.com/ajax/json/activity/offline/saveApplyInfo"
def join_in_it(id, phone_num):
    payload = {'shippingAddress': '', 'extraCount': '', 'birthdayStr': '', 'email': '',
               'marryDayStr': '', 'babyBirths': '', 'pregnant': '', 'marryStatus': '0', 'comboId': '', 'branchId': '',
               'usePassCard': '', 'passCardNo': '', 'isShareSina': 'false', 'isShareQQ': 'false',
               'offlineActivityId': id, 'phoneNo':phone_num}
    # 请求报名
    data = session.post(url, headers=headers, data=payload)
    dic = data.json()
    if dic['code'] == 200:
        print('成功报名')
    else:
        print(dic)

# 一个单独的请求器，防止刷页面被封禁
spider_session = requests.session()
spider_url = 'http://m.dianping.com/activity/static/pc/list'
pre_callback = 'jQuery112405054301475677674'
page = 0
while True:
    ts = int(time.time()*1000)
    param = {'page': page, 'callback': (pre_callback + '_' + str(ts)), 'cityId': 2, '_': ts}
    raw = spider_session.get(spider_url, params=param).text
    # 将jQuery 转化成json
    matchObj = re.search('\(.*?', raw, 0)
    span = matchObj.span()
    json_str = raw[span[1]:]
    json_str = json_str[:-1]
    dict = json.loads(json_str)
    if dict['code'] != 200:
        continue
    else:
        mlist = dict['data']['detail']
        print(mlist)
        # 不要并发请求 慢慢来
        for detail in mlist:
            offlineActivityId = detail['offlineActivityId']
            print(offlineActivityId)
            join_in_it(offlineActivityId, phone)
            time.sleep(3)
    # 休息1s
    page += 1
    time.sleep(1)



