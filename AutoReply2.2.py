# coding=utf-8
import utils
import itchat
from time import sleep
import threading
from logging import basicConfig, INFO, info, ERROR
import os.path

basicConfig(level=ERROR)

'''
# 该程序实现接入个人微信号并实现自动回复的功能，同时可选择好友有消息时短信通知或者邮件通知你，
    接入微信号使用了作者：LittleCoder的itchat微信接口开源库，
    github地址：https://itchat.readthedocs.io/zh/latest/#itchat
    在此感谢该作者！

# 基本使用说明：
# 接收的消息类型包括：
    文字：
    图片：
    视频：
    语音：
    共享：
    联系人名片：
    地图：
    声音文件：

# 处理规则：
# 对于文字类消息，分为两类好友进行判别
    # 非星标好友：收到该好友第一条消息后会发送以下全局变量中的：FirstMsg，然后根据好友的回复来处理
    如果好友回复内容是ReceiveYes中的内容之一，则会发邮件通知你，并给好友回复ReplyYes中的内容
    如果好友回复内容是ReceiveNo中的内容之一，则不会通知你，并且给好友回复ReplyNo中的内容
    否则调用图灵机器人，同时计时器开始计时会话周期，当计时器过了CountTime时间后没有收到该好友消息或者你也没有发送消息给给好友
    那么当前会话结束
    # 星标好友：与普通好友的区别在于好友第一条消息后会发送以下全局变量中的：FirstMsg，并且加送一条提示VIPMsg，然后自动邮件通知你
    其余一致
# 对于非文字类消息
    所有好友统一回复，说明接收到的文件类型，并说明小助手暂不支持处理该类消息  

# 会话类型：包括三类，一类是自己发给自己，用来测试，一类是自己发给别人，另一类是别人发给自己
    对于自己发给自己的消息，使用host_info函数处理
    对另外两类消息统一由auto_reply函数代理

'''
# 版本更新信息
log = "更新信息:\n" \
      "2017-10-01-v1.0：实现对微信的接入，实现图灵机器人接入。\n" \
      "2017-10-02-v1.1：实现对消息的自动回复。\n" \
      "2017-10-03-v1.2：完善消息回复逻辑，增加好友信息短信通知功能。\n" \
      "2017-10-04-v2.0：重构程序，将好友列表机制改为会话列表机制。\n" \
      "2017-10-05-v2.1：修复主人进入会话后不能自动停止机器人交互的bug.\n" \
      "2017-10-06-v2.2：添加主人通过指令获取好友信息功能。\n" \
      "2017-10-07-v2.2：修改对好友回复启用机器人的逻辑规则。\n"

# 支持的命令信息
command = "支持的命令：\n" \
          "START：启动全局回复代理。\n" \
          "STOP：停止全局回复代理。\n" \
          "STARFRIEND：返回星标好友列表。\n" \
          "NEVERLIST：返回不使用代理的好友名单。\n" \
          "ADD NEVER‘用户名’：添加好友到不使用代理名单。\n" \
          "DELETE NEVER ‘用户名’：将好友从不使用代理名单中删除。\n" \
          "N：刷新NEVERLIST。\n" \
          "REFRESH：刷新好友列表。\n" \
          "LOG：获取软件版本信息。\n" \
          "COMMAND：获取当前支持的命令信息。\n"
# 需要的全局变量
SessionList = {}  # 会话列表
Auto_Reply_Status = True  # 是否开启自动回复
CountTime = 60 * 10  # 按照10分钟计算一个新会话的开始
# 消息类型
HOST_TO_HOST = 1  # 自己发给自己
HOST_TO_OTHER = 2  # 自己发给好友
OTHER_TO_HOST = 3  # 别人发给自己
NONE = 4  # 错误类型
# 调用图灵机器人需要用到的key
key = 'bfa6182deac04323b72c1705e4897ae4'
# 发邮件需要用到的信息
HostUserName = "yooongchun@foxmail.com"
KEY = "ynfrkvjmyhwwcfij"
ToUserName = "zyc121561@sjtu.edu.cn"
# 发短信需要用到的，查看utils.py里的详细说明
account_sid = 'ACaf4b6a367d3dc718ba8c1ccaaaff91a9'
auth_token = '1d561065ea4b8857ec0537c25f9add1a'
twilio_number = '+12067456298'
send_number = '+8618217235290'
# 不回复的好友名单
NeverList = []
# 主人
Host = ''
# 好友名单
UserName = []
NameList = []
# 星标好友
StarFriend = []
############################################
# 通用第一条消息模板
FirstMsg = u'嘿嘿嘿，你的消息我已经收到了，但是主人现在木有在呢，要不要小助手为你短信通知主人呢？[这是什么(W),聊天(C)，这很烦人(N)]'
# 星标好友额外消息模板
VIPMsgHead = u'小助手检测到你是:'
VIPMsgRear = u'，主人说你是对他特别重要的人，正在为你自动短信通知他喔,你稍等啦，或者也可以让我陪你聊天哈~'
# 对是否短信通知的回答及回复模板
ReceiveYes = ['要的', '有', '要', '好的', '好吧', '好啊', '好呀', '那你通知吧', '嗯', '可以', '有急事', '急事', '快点叫查永春来', '快叫他来', '快'
                                                                                                          '叫你主人来', '好']
ReplyYes = '好哒，小助手已经为你短信通知主人啦，你稍等喔~'
ReceiveWhat = ['W', '这是什么', '这是什么（W）', '啥？', '蛤？', '什么鬼？']
ReplyWhat = '亲爱的朋友，这是个人编写的微信代理小程序，如果您觉得这样的代理回复打扰到了您，可在任意时候回复 N ，即可永久停止我' \
            '与您之间的小助手回复代理。如果你也想试一试这样的功能，可联系我，我会为你免费提供此程序，包括源代码，不足之处，还望海' \
            '涵。谢谢您的谅解，祝您生活愉快！\n该助手主要功能包括：1.在好友有急事联系时短信/邮件通知我。2.使用手机微信控制电脑，如' \
            '给电脑传送文件，或者获取电脑文件，等。3.统计自己微信好友信息，比如性别比例、好友城市分布、个性签名、星标好友等。4.接' \
            '入图灵机器人实现智能聊天，等。'
ReceiveNoise = ['N', '这很烦人', '这份烦人（N）']
ReplyNoise = '抱歉给您带来的不便，小助手还在成长，望您谅解，今后我将停止代理所有您与主人之间的会话，祝您生活愉快，再见！'
ReceiveNo = ['不要', '不', '算了', '没事，不用了', '没急事', '不用', 'No']
ReplyNo = '好吧，那你可能要等他晚些回复你喔~'
ReceiveChat = ['聊天', 'C', '聊天（C）', 'c']
ReplyChat = '接下来小助手为你接入聊天机器人进行互动喔，回复 stop 即可退出，have fun!'


# 加载不自动回复的好友名单
def load_never_list():
    info('进入函数：load_never_list')
    global NeverList
    # 加载不回复好友列表
    if os.path.exists('NeverList.never'):
        with open('NeverList.never', 'r') as f:
            never = f.readlines()
            NeverList = [name.rstrip('\n') for name in never]
    else:
        with open('NeverList.never', 'w') as f:
            f.write(' \n')


# 更新好友列表
def refresh_friend_list():
    info('进入函数：refresh_friend_list')
    global Host
    global NameList
    global StarFriend
    global UserName
    UserName = itchat.get_friends(update=True)
    Host = UserName[0]  # 主人
    # 获得好友信息列表
    NameList = init(UserName)
    NameList['filehelper'] = '文件助手'  # 添加文件助手
    StarFriend = [NameList[star['UserName']] for star in UserName if star['StarFriend'] == 1]  # 星标好友


# 初始化：返回好友微信id及备注名
def init(UserName):
    info('进入函数：init')
    NameList = {}
    for user in UserName:
        if user['RemarkName']:
            NameList[user['UserName']] = user['RemarkName']
        else:
            NameList[user['UserName']] = user['NickName']
    return NameList


# 计时：维持会话时间，当会话时间结束，则好友从当前会话列表中移除
def count_time(msg):
    info('进入函数：count_time')
    global SessionList
    # 获得线程锁
    lock = SessionList[msg['FromUserName'] + msg['ToUserName']]['Lock']
    # 维持计时器
    while SessionList[msg['FromUserName'] + msg['ToUserName']]['LastTime']:
        lock.acquire()
        try:
            SessionList[msg['FromUserName'] + msg['ToUserName']]['LastTime'] -= 1
        finally:
            lock.release()
        sleep(1)  # 睡眠一秒
    # 计时周期到期，销毁该对话
    SessionList.pop(msg['FromUserName'] + msg['ToUserName'])


# 对消息的处理判别
def msg_status(msg):
    info('进入函数：msg_status')
    # 判断好友是否为星标好友
    if NameList[msg['FromUserName']] in StarFriend:
        vip_flag = True
    else:
        vip_flag = False
    # 如果消息是自己发给别人
    if msg['FromUserName'] == Host['UserName'] and msg['ToUserName'] != Host['UserName']:
        Type = HOST_TO_OTHER
        host_in = True
        host_count = 1
        friend_count = 0
        session_holder = 'Host'
    # 如果消息是自己发给自己
    elif msg['FromUserName'] == Host['UserName'] and msg['ToUserName'] == Host['UserName']:
        Type = HOST_TO_HOST
        host_in = True
        host_count = 1
        friend_count = 0
        session_holder = 'Host'
    # 如果消息是别人发给自己
    elif msg['FromUserName'] != Host['UserName'] and msg['ToUserName'] == Host['UserName']:
        Type = OTHER_TO_HOST
        host_in = False
        host_count = 0
        friend_count = 1
        session_holder = 'Friend'
    else:
        Type = NONE
        host_in = None
        host_count = None
        friend_count = None
        session_holder = None
    return vip_flag, Type, host_in, host_count, friend_count, session_holder


# 创建会话函数
def create_session(msg):
    info('为用户：%s 创建会话' % NameList[msg['FromUserName']])
    global SessionList  # 添加
    # 参数说明：
    # FromUserName：消息发送者
    # ToUserName:消息接收者
    # 获得备注名或昵称：NameList[msg['FromUserName']],
    # FirstMsg：该会话周期内产生的第一条消息状态
    # FriendFirstReply：该对象的第一次回复状态
    # VIP：该对象是否属于星标好友状态
    # Lock：该对象的线程锁
    # HostIn：主人加入标志
    # LastTime：对话生命周期剩余状态
    # MsgType：消息类别：文字，声音等
    # FromUserCount:发送者发送的消息数
    # ToUserCount：接收者发送的消息数
    # Type:会话类别
    # SessionHolder：会话的发起者
    # host-->other：主人主动发消息给好友,Type = HOST_TO_OTHER
    # host-->host：主人发消息给自己，可作为测试,Type = HOST_TO_HOST
    # other-->host:好友发来的消息,Type = OTHER_TO_HOST
    # 其它：Type = NONE
    # 消息类别:文字类型：Text
    vip_flag, Type, host_in, host_count, friend_count, session_holder = msg_status(msg)  # 取得消息状态
    SessionList[msg['FromUserName'] + msg['ToUserName']] = {'FromUserName': NameList[msg['FromUserName']],
                                                            'ToUserName': NameList[msg['ToUserName']],
                                                            'SessionHolder': session_holder, 'Lock': threading.Lock(),
                                                            'HostIn': host_in, 'RobotIn': False, 'Type': Type,
                                                            'VIP': vip_flag, 'LastTime': CountTime,
                                                            'HostCount': host_count, 'FriendCount': friend_count}
    # 启动会话计时线程
    th_time = threading.Thread(target=count_time, args=(msg,))
    th_time.start()
    return msg['FromUserName'] + msg['ToUserName']


# 自己发给自己，用于启动全局回复代理，特殊处理
def host_info(msg):
    info('进入函数：host_info')
    global Auto_Reply_Status
    if msg['Text'] == 'START':
        Auto_Reply_Status = True
        itchat.send_msg('主人，我已开启全局回复代理！', msg['FromUserName'])


# 处理会话
def operate_session(session_id, msg, msg_type):
    info('进入函数：operate_session')
    global SessionList
    global Auto_Reply_Status
    global NeverList
    # 更新会话计时器
    lock = SessionList[session_id]['Lock']
    lock.acquire()
    try:
        # 更新会话生命周期
        SessionList[session_id]['LastTime'] = CountTime
    finally:
        lock.release()
    # 自己发给自己
    if SessionList[session_id]['Type'] == HOST_TO_HOST:
        host_to_host(msg, msg_type)
    # 自己发给别人
    elif SessionList[session_id]['Type'] == HOST_TO_OTHER:
        SessionList[session_id]['HostIn'] = True
        pass
        # itchat.send_msg('主人，你给%s发了一条消息' % msg['ToUserName'])
    # 别人发给自己
    elif SessionList[session_id]['Type'] == OTHER_TO_HOST:
        other_to_host(session_id, msg, msg_type)


# 自己发给自己
# 发文件 ithcat.send("@fil@%s" % '/tmp/test.text')
# 发图片 ithcat.send("@img@%s" % '/tmp/test.png')
# 发视频 ithcat.send("@vid@%s" % '/tmp/test.mkv')
# send_file(fileDir, toUserName=None)
# send_image(fileDir, toUserName=None)
# send_video(fileDir, toUserName=None)
def host_to_host(msg, msg_type):
    info('进入函数：host_to_host')
    global SessionList
    global Auto_Reply_Status
    global NeverList
    if msg_type == 'Text':
        # 停止全局自动回复代理
        if msg['Text'].lower() == 'stop':
            Auto_Reply_Status = False
            itchat.send_msg('主人，我已停止全局自动回复代理！', msg['FromUserName'])
        # 命令信息
        elif msg['Text'].lower() == 'command':
            itchat.send_msg('主人，这是目前支持的命令信息：\n%s' % command, msg['FromUserName'])
        # 获取log信息
        elif msg['Text'].lower() == 'log':
            itchat.send_msg('主人，这是版本更新信息：\n%s' % log, msg['FromUserName'])

        # 更新好友名单
        elif msg['Text'].lower() == 'refresh':
            refresh_friend_list()
            itchat.send_msg('主人，我已经更新了你的好友列表', msg['FromUserName'])
        # START用于特殊情况开启全局代理，N用于刷新NeverList，都不使用机器人回复
        elif msg['Text'].lower() == 'start':
            pass
        elif msg['Text'].lower() == 'n':
            itchat.send_msg('主人，我已经刷新了不回复好友名单', msg['FromUserName'])
        # 添加不回复好友
        elif 'add never' in msg['Text'].lower():
            text = msg['Text'].lower().replace('add never ', '')
            exflag = False
            for name in NameList:
                if text == NameList[name]:
                    exflag = True
                    break
            if exflag:  # 存在该好友
                with open('NeverList.never', 'a') as fff:
                    fff.write(text + '\n')
                itchat.send_msg('主人，已经将好友：%s 放入NeverList名单中' % text, msg['FromUserName'])
            else:
                itchat.send_msg('主人，你要添加的好友：%s 不在你的好友名单中' % text, msg['FromUserName'])
        # 删除不回复好友
        elif 'delete never' in msg['Text'].lower():
            text = msg['Text'].lower().replace('delete never ', '')
            with open('NeverList.never', 'r') as ffff:
                name = ffff.readlines()
                NeverList = [na.rstrip('\n') for na in name]
            if text in NeverList:
                with open('NeverList.never', 'w') as fffff:
                    for name in NeverList:
                        if name != text:
                            fffff.write(name + '\n')
                itchat.send_msg('主人，已经将好友：%s 从NeverList名单中删除' % text, msg['FromUserName'])
            else:
                itchat.send_msg('主人，你要从NeverList中删除的好友：%s 不在你的NeverList名单中' % text, msg['FromUserName'])
        # 获取不回复的好友名单
        elif msg['Text'].lower() == 'neverlist':
            str_name = ''
            with open('NeverList.never', 'r') as f:
                never = f.readlines()
                NeverList = []
                for ne in never:
                    NeverList.append(ne.rstrip('\n'))
            for name in NeverList:
                str_name += '【' + name + '】'
            itchat.send_msg('主人，这是目前不进行代理回复的好友名单：%s' % str_name, msg['FromUserName'])
        # 获取星标好友名单
        elif msg['Text'].lower() == 'starfriend':
            str_name = ''
            for name in StarFriend:
                str_name += '【' + name + '】'
            itchat.send_msg('主人，这是目前你好友中的星标好友名单：%s' % str_name, msg['FromUserName'])
        # 获取好友列表
        elif msg['Text'].lower() == 'friendlist':
            str_name = ''
            for id, name in NameList.items():
                str_name += '【' + name + '】'
            itchat.send_msg('主人，这是目前你的好友名单：\n%s' % str_name, msg['FromUserName'])
        # 获取好友性别，星标好友分布图
        elif msg['Text'].lower() == 'viewinfo':
            itchat.send_msg('主人，我正在为你生成好友性别比例图和城市分布热力图，请稍等！', msg['FromUserName'])
            try:
                male, female, other, pro_city, signature, star_friend = utils.frinds_info(UserName)
                utils.view_info(male, female, other, pro_city, star_friend)
                if os.path.exists('sex.png'):
                    itchat.send_image('sex.png', msg['FromUserName'])
                else:
                    itchat.send_msg('主人，性别统计数据生成成功啦，只是好像没保存成功呢，再试一次吧！', msg['FromUserName'])
                if os.path.exists('heatmap.html'):
                    itchat.send_file('heatmap.html', msg['FromUserName'])
                else:
                    itchat.send_msg('主人，好友城市分布热力图数据生成成功啦，只是好像没保存成功呢，再试一次吧！', msg['FromUserName'])
            except ConnectionRefusedError:
                itchat.send_msg('主人，生成失败了呢，检查一下网络连接吧！', msg['FromUserName'])

        # 别的文字消息则启动机器人回复
        else:
            robot_reply = utils.get_response(msg['Text'], key)
            itchat.send_msg(robot_reply, msg['FromUserName'])
    elif msg_type == 'Attachment':
        itchat.send_msg('主人，我收到了你发来的附件！', msg['FromUserName'])
    elif msg_type == 'Voice':
        itchat.send_msg('主人，我收到了你发来的语音！', msg['FromUserName'])
    elif msg_type == 'Recording':
        itchat.send_msg('主人，我收到了你发来的音频文件爱你！', msg['FromUserName'])
    elif msg_type == 'Video':
        itchat.send_msg('主人，我收到了你发来的视频文件！', msg['FromUserName'])
    elif msg_type == 'Picture':
        itchat.send_msg('主人，我收到了你发来的图片！', msg['FromUserName'])
    elif msg_type == 'Map':
        itchat.send_msg('主人，我收到了你发来的地图！', msg['FromUserName'])
    elif msg_type == 'Card':
        itchat.send_msg('主人，我收到了你发来的联系人卡片！', msg['FromUserName'])
    elif msg_type == 'Sharing':
        itchat.send_msg('主人，我收到了你发来的共享文件！', msg['FromUserName'])
    elif msg_type == 'Note':
        itchat.send_msg('主人，我收到了系统提示！', msg['FromUserName'])
    elif msg_type == 'System':
        itchat.send_msg('主人，我收到了系统消息！', msg['FromUserName'])


# 别人发给自己消息处理
def other_to_host(session_id, msg, msg_type):
    info('进入好友发给自己的处理函数')
    # 判断主人是否在会话中
    if msg['FromUserName'] == Host['UserName']:
        SessionList[session_id]['HostIn'] = True

    # 主人不在会话中,则使用回复代理
    if not SessionList[session_id]['HostIn']:
        # 发送给自己的消息类型
        if msg_type == 'Text':
            send_text = msg['Text']
        else:
            send_text = msg_type
        # 好友回复了永久停止小助手
        if msg['Text'] in ReceiveNoise:
            with open('NeverList.never', 'a') as f:
                f.write(NameList[msg['FromUserName']] + '\n')
            itchat.send_msg(ReplyNoise, msg['FromUserName'])
            return
        # 好友回复了对小助手的询问
        if msg['Text'] in ReceiveWhat:
            itchat.send_msg(ReplyWhat, msg['FromUserName'])
            return
        # 好友回复聊天
        if msg['Text'] in ReceiveChat:
            SessionList[session_id]['RobotIn'] = True
            itchat.send_msg(ReplyChat, msg['FromUserName'])
            return
        # 好友回复退出聊天
        if msg['Text'] == 'stop':
            SessionList[session_id]['RobotIn'] = False
            itchat.send_msg('已退出机器人聊天！', msg['FromUserName'])
            return

        # 判断这是该好友发来的第几条消息
        if SessionList[session_id]['FriendCount'] == 1:
            SessionList[session_id]['FriendCount'] += 1
            # 发送第一条消息
            itchat.send_msg(FirstMsg, msg['FromUserName'])
            # VIP好友加送一条
            if SessionList[session_id]['VIP']:
                itchat.send_msg(VIPMsgHead + NameList[msg['FromUserName']] + VIPMsgRear, msg['FromUserName'])
                # 发短信通知
                try:
                    utils.send_sms(
                        '主人，你的微信VIP好友%s在微信上给你发消息：%s。快去看看吧' % (NameList[msg['FromUserName']], send_text),
                        send_number)
                except Exception:
                    itchat.send_msg('阿欧，短信发不了呢，为你尝试发邮件联系喔~', msg['FromUserName'])
                    # 发邮件
                    try:
                        content = {'header': '微信好友%s发来消息' % NameList[msg['FromUserName']],
                                   'text': '主人，你的微信好友%s 在微信上给你发了消息：%s。发你短信出故障了呢！' % (NameList[msg['FromUserName']],
                                                                                     send_text)}
                        utils.send_mail(content, HostUserName, KEY, ToUserName)
                    except Exception:
                        itchat.send_msg('啊，今天真是倒霉，邮件也发不出去啦，要是有急事的话，试试打电话吧：%s' % send_number, msg['FromUserName'])
        # 好友发来的第二条消息，可能是对第一条的回复
        elif SessionList[session_id]['FriendCount'] == 2:
            SessionList[session_id]['FriendCount'] += 1
            # 非VIP好友
            if not SessionList[session_id]['VIP']:
                if msg['Text'] in ReceiveYes:
                    # 发短信通知
                    try:
                        utils.send_sms(
                            '主人，你的微信好友 %s 在微信上给你发消息：%s。快去看看吧' % (NameList[msg['FromUserName']], send_text),
                            send_number)
                        itchat.send_msg(ReplyYes, msg['FromUserName'])
                    except Exception:
                        itchat.send_msg('阿欧，短信发不了了呢，为你尝试发邮件联系喔~', msg['FromUserName'])
                        # 发邮件
                        try:
                            content = {'header': '微信好友 %s 发来消息' % NameList[msg['FromUserName']],
                                       'text': '主人，你的微信好友 %s 在微信上给你发了消息：%s。发你短信出故障了呢！' % (
                                           NameList[msg['FromUserName']],
                                           send_text)}
                            utils.send_mail(content, HostUserName, KEY, ToUserName)
                        except Exception:
                            itchat.send_msg('啊，今天真是倒霉呢，邮件也发不出去啦，要是有急事的话，试试打电话吧：%s' % send_number,
                                            msg['FromUserName'])
                elif msg['Text'] in ReceiveNo:
                    itchat.send_msg(ReplyNo, msg['FromUserName'])

                else:
                    # 好友回复聊天状态为True
                    if SessionList[session_id]['RobotIn']:
                        robot_reply = utils.get_response(msg['Text'], key)
                        itchat.send_msg(robot_reply, msg['FromUserName'])
            else:
                # 好友回复聊天状态为True
                if SessionList[session_id]['RobotIn']:
                    robot_reply = utils.get_response(msg['Text'], key)
                    itchat.send_msg(robot_reply, msg['FromUserName'])
        else:  # 启动机器人回复
            # 好友回复聊天状态为True
            if SessionList[session_id]['RobotIn']:
                robot_reply = utils.get_response(msg['Text'], key)
                itchat.send_msg(robot_reply, msg['FromUserName'])


#############################################
# 消息接收
@itchat.msg_register(itchat.content.TEXT)
def info_text(msg):
    info('进入函数：info_text')
    print('收到来自 %s 的文字消息：%s' % (NameList[msg['FromUserName']], msg['Text']))
    global SessionList
    global NeverList
    # 创建线程处理会话
    # 特殊情况，用于在全局回复代理关闭时进行启动
    if msg['FromUserName'] == Host['UserName'] and (not Auto_Reply_Status):
        host_sess = threading.Thread(target=host_info, args=(msg,))
        host_sess.start()
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if msg['FromUserName'] == Host['UserName'] and msg['Text'] == 'N':  # 收到主人发的N更新NeverList
        with open('NeverList.never', 'r') as ff:
            never = ff.readlines()
            NeverList = [name.rstrip('\n') for name in never]
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
            session_id = msg['FromUserName'] + msg['ToUserName']
        elif (msg['ToUserName'] + msg['FromUserName']) in SessionList:
            session_id = msg['ToUserName'] + msg['FromUserName']
        # 会话已经存在
        else:
            session_id = create_session(msg)  # 创建会话

        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Text'))
        new_sess.start()


# 语音消息
@itchat.msg_register(itchat.content.RECORDING)
def info_recording(msg):
    info('进入函数：info_recording')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Recording'))
        new_sess.start()


# 附件
@itchat.msg_register(itchat.content.ATTACHMENT)
def info_attachment(msg):
    info('进入函数：info_attachment')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Attachment'))
        new_sess.start()


# 通知消息
@itchat.msg_register(itchat.content.NOTE)
def info_note(msg):
    info('进入函数：info_note')
    pass


# 图片
@itchat.msg_register(itchat.content.PICTURE)
def info_picture(msg):
    info('进入函数：info_picture')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Picture'))
        new_sess.start()


# 地图
@itchat.msg_register(itchat.content.MAP)
def info_map(msg):
    info('进入函数：info_map')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Map'))
        new_sess.start()


# 卡片
@itchat.msg_register(itchat.content.CARD)
def info_card(msg):
    info('进入函数：info_card')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Card'))
        new_sess.start()


# 共享
@itchat.msg_register(itchat.content.SHARING)
def info_sharing(msg):
    info('进入函数：info_sharing')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Sharing'))
        new_sess.start()


# 视频
@itchat.msg_register(itchat.content.VIDEO)
def info_video(msg):
    info('进入函数：info_video')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Video'))
        new_sess.start()


# 朋友邀请
@itchat.msg_register(itchat.content.FRIENDS)
def info_friends(msg):
    info('进入函数：info_friends')
    pass


# 系统消息
@itchat.msg_register(itchat.content.SYSTEM)
def info_system(msg):
    info('进入函数：info_system')
    pass


# 声音
@itchat.msg_register(itchat.content.VOICE)
def info_voice(msg):
    info('进入函数：info_voice')
    global SessionList
    # 仅当全局回复状态及该好友不在NeverList中时传递该消息
    if Auto_Reply_Status and NameList[msg['FromUserName']] not in NeverList:
        # 判断会话是否已经存在
        if ((msg['FromUserName'] + msg['ToUserName']) not in SessionList) and (
                    (msg['ToUserName'] + msg['FromUserName']) not in SessionList):
            session_id = create_session(msg)  # 创建会话
        else:
            if (msg['FromUserName'] + msg['ToUserName']) in SessionList:
                session_id = msg['FromUserName'] + msg['ToUserName']
            else:
                session_id = msg['ToUserName'] + msg['FromUserName']
        # 处理会话
        # 创建线程处理会话
        new_sess = threading.Thread(target=operate_session, args=(session_id, msg, 'Voice'))
        new_sess.start()


if __name__ == '__main__':
    print('正在登录微信，若第一次登录，请扫描弹出的二维码，没加载出来则请重新启动程序')  # 登录微信
    itchat.auto_login(hotReload=True)
    print('登录成功！')
    load_never_list()  # 加载不代理的好友名单
    refresh_friend_list()  # 更新好友名单
    print('开启自动回复！')
    itchat.run()  # 持续监听自动回复
    print('程序运行结束!')
