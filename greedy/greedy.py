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

QR_CODE = 'QRCode.jpg'

qr_header = {
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}

status_header = {
'Accept':'*/*',
'Accept-Encoding':'gzip, deflate, br',
'Accept-Language':'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
}

# 获取二维码状态地址
status_fetcher_url = 'https://www.dianping.com/account/ajax/queryqrcodestatus'

# 报名链接
url = "http://s.dianping.com/ajax/json/activity/offline/saveApplyInfo"

# 一个单独的未登录状态爬虫，防止刷页面被封禁
spider_session = requests.session()
spider_url = 'http://m.dianping.com/activity/static/pc/list'
pre_callback = 'jQuery112405054301475677674'


# 获取二维码图片, 成功扫描二维码后将返回信令
def fetch_qr_code():
    qr_code_data = session.get('https://www.dianping.com/account/getqrcodeimg', headers=qr_header, stream=True)

    with open(QR_CODE, 'wb') as f:
        f.write(qr_code_data.content)
    # 打开图片
    if platform.system() == 'Darwin':
        subprocess.call(['open', QR_CODE])
    elif platform.system() == 'Linux':
        subprocess.call(['xdg-open', QR_CODE])
    else:
        os.startfile(QR_CODE)
    # get the ticket
    token = session.cookies.__getitem__('lgtoken')
    print('ticket got: ', token)
    return token


#获取二维码状态
def fetch_qr_status(token):
    status_payload = {'lgtoken': token}
    sucess = False
    while True:
        r = session.post(status_fetcher_url, headers=status_header, data=status_payload)
        dic = r.json()
        if dic['code'] != 200:
            continue
        status = dic['msg']['status']
        # 0 no scan, 1 scan, 2 scaned
        if status == -1:
            print('验证码过期')
            break
        elif status == 0:
            print('请使用大众点评APP扫描二维码……')
            time.sleep(1)
        elif status == 1:
            print('已经成功扫描二维码，请在手机点击确认登录')
            time.sleep(1)
        elif status == 2:
            print('成功登录')
            # 目的是拿到浏览器cookies
            print(r.cookies)
            sucess = True
            break
    return sucess


# 手机号验证
def phone_num():
    with open('phone', 'rb') as reader:
        phone = reader.read().decode()
        # 简单校验
        while len(phone) != 11:
            print("请输入正确的手机号")
            phone = input()
            print('手机号已被存为：', phone)
        # 写入文件
        with open('phone', 'wb') as writer:
            writer.write(phone.encode())
    return phone


def spider(handler):
    current_page = 0
    prefered_ranger = 1024  # 最大页码数量，肯定是不会取到这么大的，所以ranger 是可调整的。
    while True:
        ts = int(time.time()*1000)
        # type = 0 全部霸王餐
        param = {'page': current_page, 'callback': (pre_callback + '_' + str(ts)), 'cityId': 2, '_': ts}
        raw = spider_session.get(spider_url, params=param).text
        # jQuery -> json
        matchObj = re.search('\(.*?', raw, 0)
        span = matchObj.span()
        json_str = raw[span[1]:]
        json_str = json_str[:-1]
        dic = json.loads(json_str)
        if dic['code'] != 200:
            continue
        else:
            mlist = dic['data']['detail']
            # adjust the length of page
            if mlist and len(mlist) <= 0 and current_page > 10:
                current_page = 0
                prefered_ranger = 10
                time.sleep(3)
                continue
            # slow down
            for detail in mlist:
                offlineActivityId = detail['offlineActivityId']
                # TODO: 可以对商户进行筛选
                handler(offlineActivityId, phone_num, '1', detail['activityTitle'])
                time.sleep(3)

            current_page += 1
            current_page %= prefered_ranger
        # sleep 1s
        time.sleep(1)


# 报名开始
def join_in_it(aid, phone_num, extra_count, title):
    payload = {'shippingAddress': '', 'extraCount': extra_count, 'birthdayStr': '', 'email': '',
               'marryDayStr': '', 'babyBirths': '', 'pregnant': '', 'marryStatus': '0', 'comboId': '', 'branchId': '',
               'usePassCard': '', 'passCardNo': '', 'isShareSina': 'false', 'isShareQQ': 'false',
               'offlineActivityId': aid, 'phoneNo': phone_num}
    # 请求报名
    data = session.post(url, headers=headers, data=payload)
    m_json = data.json()
    if m_json['code'] == 200:
        print('成功报名' + title)
    else:
        print('报名失败：', m_json)
    print('tracking id', aid)

# entrance
if __name__ == '__main__':
    # 登录验证
    while True:
        lgtoken = fetch_qr_code()
        success = fetch_qr_status(lgtoken)
        if success:
            break

    # 手机号验证
    phone_num = phone_num()

    spider(join_in_it)

# TODO:
"""
1. cookie 持久化 cy=2; cye=beijing
2. 报名信息筛选
2. mysql 存储已报名信息
3. 自动签到
"""