# ! /usr/bin/env python
# coding=gbk
import requests
import json
import smtplib
# import webbrowser
from email.mime.text import MIMEText
from twilio.rest import Client
from urllib.request import urlopen, quote
from pylab import *

mpl.rcParams['font.sans-serif'] = ['SimHei']


# 使用Twilio的免费手机号发送短信
# 你需要在官网上申请一个账号，这里是官网：https://www.twilio.com/
def send_sms(msg='你好，这是来自你自己的手机测试信息！', my_number='+8618217235290'):
    # 从官网获得以下信息
    account_sid = 'ACaf4b6a367d3dc718ba8c1ccaaaff91a9'
    auth_token = '1d561065ea4b8857ec0537c25f9add1a'
    twilio_number = '+12067456298'

    client = Client(account_sid, auth_token)
    try:
        client.messages.create(to=my_number, from_=twilio_number, body=msg)
        print('短信已经发送！')
    except ConnectionError as e:
        print('发送失败，请检查你的账号是否有效或网络是否良好！')
        return e


# 获得图灵机器人回复
# 需要传入两个参数，Msg内容是文本或者表情，返回值就是回复内容
# Key是接入图灵机器人需要的秘钥，需要自己到官网获取
def get_response(Msg, Key, Userid='ItChat'):
    url = 'http://www.tuling123.com/openapi/api'
    payloads = {'key': Key, 'info': Msg, 'userid': Userid, }
    try:
        r = requests.post(url, data=json.dumps(payloads)).json()
    except ConnectionError:
        return None
    if not r['code'] in (100000, 200000, 302000, 308000, 313000, 314000):
        return
    if r['code'] == 100000:  # 文本类
        return '\n'.join([r['text'].replace('<br>', '\n')])
    elif r['code'] == 200000:  # 链接类
        return '\n'.join([r['text'].replace('<br>', '\n'), r['url']])
    elif r['code'] == 302000:  # 新闻类
        l = [r['text'].replace('<br>', '\n')]
        for n in r['list']: l.append('%s - %s' % (n['article'], n['detailurl']))
        return '\n'.join(l)
    elif r['code'] == 308000:  # 菜谱类
        l = [r['text'].replace('<br>', '\n')]
        for n in r['list']: l.append('%s - %s' % (n['name'], n['detailurl']))
        return '\n'.join(l)
    elif r['code'] == 313000:  # 儿歌类
        return '\n'.join([r['text'].replace('<br>', '\n')])
    elif r['code'] == 314000:  # 诗词类
        return '\n'.join([r['text'].replace('<br>', '\n')])


# 使用QQ邮箱发送邮件
# Content是发送的内容，格式为{'header':'你的发送主题','text':'你的正文内容'}
# HostUserName你自己的QQ邮箱名
# KEY：QQ邮箱授权码，注意，不是密码，如何获取授权码请百度
# ToUserName：接收方的邮箱账号
def send_mail(Content, HostUserName, KEY, ToUserName):
    # 你的邮箱账号
    _user = HostUserName
    # 这里填写邮箱授权码，如何获得QQ邮箱授权码，请百度
    _pwd = KEY
    # 这里是接收方邮箱账号
    _to = ToUserName

    msg = MIMEText(Content['text'])
    msg["Subject"] = Content['header']
    msg["From"] = _user
    msg["To"] = _to

    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(_user, _pwd)
        s.sendmail(_user, _to, msg.as_string())
        s.quit()
        print("发送成功！")
    except smtplib.SMTPException as e:
        print("发送失败,%s" % e)
        return e


# 根据地名获得经纬度信息
def GetLngLat(address):
    url = 'http://api.map.baidu.com/geocoder/v2/'
    output = 'json'
    ak = 'x2ZTlRkWM2FYoQbvGOufPnFK3Fx4vFR1'
    add = quote(address)
    uri = url + '?' + 'address=' + add + '&output=' + output + '&ak=' + ak
    try:
        req = urlopen(uri)
    except ConnectionRefusedError as e:
        return e
    res = req.read().decode()
    temp = json.loads(res)  # 对json数据进行解析
    return temp


# 统计好友信息
def frinds_info(UserName):
    male = 0
    female = 0
    other = 0
    pro_city = {}
    signature = {}
    star_friend = []

    for user in UserName:
        # 性别数据
        if user['Sex'] == 1:
            male += 1
        elif user['Sex'] == 2:
            female += 1
        else:
            other += 1
        # 城市数据
        if (user['Province'] + ' ' + user['City']) in pro_city:
            pro_city[user['Province'] + ' ' + user['City']] += 1
        else:
            pro_city[user['Province'] + ' ' + user['City']] = 1
        # 签名数据
        if user['RemarkName'] == '':
            signature[user['RemarkName']] = user['Signature']
        else:
            signature[user['NickName']] = user['Signature']
        # 星标朋友
        if user['StarFriend'] == 1:
            star_friend.append(user['RemarkName'])

    return male, female, other, pro_city, signature, star_friend


# 可视化好友信息
def view_info(male, female, other, pro_city, star_friend):
    # 显示性别比例
    labels = 'Male(%s)' % male, 'Female(%s)' % female, 'Other(%s)' % other, 'StarFriend(%s)' % len(star_friend)
    fracs = [male, female, other, len(star_friend)]

    plt.axes(aspect=1)  # set this , Figure is round, otherwise it is an ellipse
    patches, l_texts, p_texts = plt.pie(x=fracs, labels=labels, autopct='%3.1f %%', shadow=False,
                                        labeldistance=1.1, startangle=90, pctdistance=0.8)
    '''
    labeldistance，文本的位置离远点有多远，1.1指1.1倍半径的位置
    autopct，圆里面的文本格式，%3.1f%%表示小数有三位，整数有一位的浮点数
    shadow，饼是否有阴影
    startangle，起始角度，0，表示从0开始逆时针转，为第一块。一般选择从90度开始比较好看
    pctdistance，百分比的text离圆心的距离
    patches, l_texts, p_texts，为了得到饼图的返回值，p_texts饼图内部文本的，l_texts饼图外label的文本
    '''
    # 改变文本的大小
    # 方法是把每一个text遍历。调用set_size方法设置它的属性
    for t in l_texts:
        t.set_size = 30
    for t in p_texts:
        t.set_size = 20

    fig = plt.gcf()
    # fig.set_size_inches(20, 20)
    fig.savefig('sex.png', dpi=500)
    # plt.show()

    # 显示城市分布,使用百度的api获得相应城市的经纬度，然后使用heatmap.json生成热力图，返回html文件
    json_data = ''
    # 把城市数据转为经纬度
    for city, value in pro_city.items():
        try:
            pos = GetLngLat(city)
        except ConnectionError:
            pos = None
        if pos is not None and pos['status'] == 0:
            lng = pos['result']['location']['lng']
            lat = pos['result']['location']['lat']
            json_temp = '{"lng":' + str(lng) + ',"lat":' + str(lat) + ', "count":' + str(value) + '}, '
            json_data += '\n' + json_temp

    # 生成html格式热力图文件
    try:
        head, rear = html_code()
        html_file = head + json_data + rear
        with open('heatmap.html', 'w', encoding='utf-8') as f:
            f.write(html_file)
            # 网页显示
            # webbrowser.open('heatmap.html', new=0, autoraise=True)
    except AttributeError:
        return AttributeError


# 可视化热力图html代码
def html_code():
    head = '''<!DOCTYPE html>\n<html>\n<head>\n    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />\n    <script type="text/javascript" src="http://gc.kis.v2.scr.kaspersky-labs.com/C8BAC707-C937-574F-9A1F-B6E798DB62A0/main.js" charset="UTF-8"></script><script type="text/javascript" src="http://api.map.baidu.com/api?v=2.0&ak=x2ZTlRkWM2FYoQbvGOufPnFK3Fx4vFR1"></script>\n    <script type="text/javascript" src="http://api.map.baidu.com/library/Heatmap/2.0/src/Heatmap_min.js"></script>\n    <title>热力图功能示例</title>\n    <style type="text/css">\n		ul,li{list-style: none;margin:0;padding:0;float:left;}\n		html{height:100%}\n		body{height:100%;margin:0px;padding:0px;font-family:"微软雅黑";}\n		#container{height:500px;width:100%;}\n		#r-result{width:100%;}\n    </style>	\n</head>\n<body>\n	<div id="container"></div>\n	<div id="r-result">\n		<input type="button"  onclick="openHeatmap();" value="显示热力图"/><input type="button"  onclick="closeHeatmap();" value="关闭热力图"/>\n	</div>\n</body>\n</html>\n<script type="text/javascript">\n    var map = new BMap.Map("container");          // 创建地图实例\n\n    var point = new BMap.Point(105.418261, 35.921984);\n    map.centerAndZoom(point, 5);             // 初始化地图，设置中心点坐标和地图级别\n    map.enableScrollWheelZoom(); // 允许滚轮缩放\n  \n    var points =['''
    rear = ''']\n   \n    if(!isSupportCanvas()){\n    	alert('热力图目前只支持有canvas支持的浏览器,您所使用的浏览器不能使用热力图功能~')\n    }\n	//详细的参数,可以查看heatmap.js的文档 https://github.com/pa7/heatmap.js/blob/master/README.md\n	//参数说明如下:\n	/* visible 热力图是否显示,默认为true\n     * opacity 热力的透明度,1-100\n     * radius 势力图的每个点的半径大小   \n     * gradient  {JSON} 热力图的渐变区间 . gradient如下所示\n     *	{\n			.2:'rgb(0, 255, 255)',\n			.5:'rgb(0, 110, 255)',\n			.8:'rgb(100, 0, 255)'\n		}\n		其中 key 表示插值的位置, 0~1. \n		    value 为颜色值. \n     */\n	heatmapOverlay = new BMapLib.HeatmapOverlay({"radius":20});\n	map.addOverlay(heatmapOverlay);\n	heatmapOverlay.setDataSet({data:points,max:10});\n	//是否显示热力图\n    function openHeatmap(){\n        heatmapOverlay.show();\n    }\n	function closeHeatmap(){\n        heatmapOverlay.hide();\n    }\n	openHeatmap();\n    function setGradient(){\n     	/*格式如下所示:\n		{\n	  		0:'rgb(102, 255, 0)',\n	 	 	.5:'rgb(255, 170, 0)',\n		  	1:'rgb(255, 0, 0)'\n		}*/\n     	var gradient = {};\n     	var colors = document.querySelectorAll("input[type='color']");\n     	colors = [].slice.call(colors,0);\n     	colors.forEach(function(ele){\n			gradient[ele.getAttribute("data-key")] = ele.value; \n     	});\n        heatmapOverlay.setOptions({"gradient":gradient});\n    }\n	//判断浏览区是否支持canvas\n    function isSupportCanvas(){\n        var elem = document.createElement('canvas');\n        return !!(elem.getContext && elem.getContext('2d'));\n    }\n</script>'''

    return head, rear


if __name__ == '__main__':
    HostUserName = "yooongchun@foxmail.com"
    KEY = "ynfrkvjmyhwwcfij"
    ToUserName = "zyc121561@sjtu.edu.cn"
    send_mail({'text': '你好永春，这是一个测试邮件！', 'header': '测试邮件'}, HostUserName, KEY, ToUserName)

    # 图灵机器人接入需要使用的key，需要自己到图灵机器人官网申请
    key = 'bfa6182deac04323b72c1705e4897ae4'
    result = get_response('你好！', key)
    print(result)
    # 发短信
    send_sms()
