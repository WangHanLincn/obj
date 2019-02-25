import socket
ip_port=('192.168.0.114',9999)

# 封装协议（对象）
s = socket.socket()

# 向服务端建立连接
s.connect(ip_port)

while True:
    # 发送消息
    send_data=input('>>: ').strip()
    if len(send_data) == 0:continue  # 如果发送消息为空，不去执行以下发送
    s.send(bytes(send_data,encoding='utf8'))
    if send_data == 'exit': break  # 如果输入exit，则退出

    # 接收消息
    recv_data = s.recv(1024) #
    print(str(recv_data,encoding='utf8'))

# 结束连接
s.close()