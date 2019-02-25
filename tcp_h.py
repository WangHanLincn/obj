import socket
ip_port=('192.168.0.114',9999)

# 封装协议（对象)
s = socket.socket()

# 绑定ip，端口
s.bind(ip_port)

# 启动监听
s.listen(5)  # 挂起连接数，  允许最多处理5个请求
while True:
    # 等待连接
    conn, addr = s.accept()  # accept方法等待客户端连接，直到有客户端连接后，会返回连接线（conn）、连接地址（addr）

    while True:
        # 至此，当客户端连接时，conn即为连接客户端的连接线
        # 所以，当客户端主动断开连接时，conn就不存在了，也会抛出异常
        # 在这里定义一个异常跟踪
        try:
            # 接收消息
            recv_data=conn.recv(1024)  # 接收conn连接线路，并指定缓存该线路的1024
            print('接收消息类型：%s' % type(recv_data))

            # 发送消息
            send_data=recv_data.upper()  # 将接收消息转换为大写
            print("发送消息内容：%s" % send_data)
            conn.send(send_data)  # 使用conn线路，发送消息
        except Exception:  # 如果客户端主动断开，则server退出该循环等待下一条连接
            break

    # 结束进程
    conn.close() # 中断线路