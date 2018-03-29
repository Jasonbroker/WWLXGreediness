import time
import requests
import re
import json

with open('phone', 'rb') as f:
    phone = f.read().decode()
    # 简单校验
    while len(phone) != 11:
        print("请输入正确的手机号")
        phone = input()
        print('手机号被存为：', phone)

    with open('phone', 'wb') as f:
        f.write(phone.encode())


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


            time.sleep(3)
    # 休息1s
    page += 1
    time.sleep(1)