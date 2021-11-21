import sys
from time import time

from utils import *

if __name__ == "__main__":
    print("Net".center(30, "-"))

    # 确定端口。
    if len(sys.argv) == 4:
        app_port, net_port, phy_port = sys.argv[1:]
        print(f"App port: {app_port}")
        print(f"Net port: {net_port}")
        print(f"Phy port: {phy_port}")
    else:
        print(f"[Error] Expect 3 arguments, got {len(sys.argv) - 1}.")
        exit(-1)

    # 创建网络层。
    net = NetLayer(net_port)
    net.bind_app(app_port)
    net.bind_phy(phy_port)

    # 全局变量。
    seq = 0
    ack = Frame()
    nak = Frame()

    # 开始运作。
    while True:
        # 网络层进入指定模式。
        mode = net.receive_from_app()
        mode_name = (
            "Receive"
            if mode == const.Mode.RECV
            else "Unicast"
            if mode == const.Mode.UNICAST
            else "Broadcast"
            if mode == const.Mode.BROADCAST
            else "Quit"
        )
        print(f"[Log] Current Mode: {mode_name}")

        # 如果要退出程序，就跳出循环。
        if mode == const.Mode.QUIT:
            break

        # 如果要接收消息，就逐帧读取。
        elif mode == const.Mode.RECV:
            recv_cnt = 0
            recv_message = ""
            record_flag = True
            timeout_cnt = 0
            while True:
                # 从物理层接收消息，第一帧可以等得久一些。
                if recv_cnt == 0:
                    phy_message, success = net.receive_from_phy(
                        const.Network.USER_TIMEOUT
                    )
                else:
                    phy_message, success = net.receive_from_phy()

                # 如果超时。
                if not success:
                    print(f"[Frame {seq + 1}] Timeout.")
                    timeout_cnt += 1
                    # 如果超时次数达到Keepalive机制上限，就不再接收。
                    if timeout_cnt == const.Network.KEEPALIVE_MAX_RETRY:
                        break
                    # 如果超时次数还没有很多，就什么都不做，重新开始等待。
                    else:
                        continue

                # 一旦接收到了帧，就重置超时次数。
                timeout_cnt = 0

                # 如果这是第一个接收到的帧，就开始计时。
                if record_flag:
                    start_time = time()
                    record_flag = False

                # 解析接收到的帧。
                recv_frame = Frame()
                recv_frame.read(phy_message)

                # 如果帧不是给自己的，就什么都不做，重新开始等待。
                if recv_frame.dst not in (app_port, const.Topology.BROADCAST_PORT):
                    print(f"[Warning] I'm not {recv_frame.dst}.")
                    continue

                # 如果序号重复，就丢弃这帧，再发一遍ACK。
                if seq == recv_frame.seq:
                    print(f"{recv_frame} (Repeated)")
                    ack.write(
                        {
                            "src": app_port,
                            "seq": seq,
                            "data": encode_text(const.Frame.ACK),
                            "dst": recv_frame.src,
                        }
                    )
                    net.send_to_phy(ack.binary)
                    continue

                # 如果校验未通过，就丢弃这帧，发送NAK。
                if not recv_frame.verified:
                    print(f"{recv_frame} (Invalid)")
                    nak.write(
                        {
                            "src": app_port,
                            "seq": seq + 1,
                            "data": encode_text(const.Frame.NAK),
                            "dst": recv_frame.src,
                        }
                    )
                    net.send_to_phy(nak.binary)
                    continue

                # 如果帧信息正确，就接收这帧，发送ACK。
                seq = recv_frame.seq
                if recv_cnt == 0:
                    recv_total = bin_to_dec(
                        recv_frame.data[: const.Frame.DATA_LEN // 2]
                    )
                    message_type = str(
                        bin_to_dec(recv_frame.data[const.Frame.DATA_LEN // 2 :])
                    )
                    message_type_name = (
                        "text" if message_type == const.MessageType.TEXT else "picture"
                    )
                    print(
                        f"[Frame {seq}] {recv_total} frame(s) of {message_type_name}."
                    )
                else:
                    recv_message += recv_frame.data
                    print(f"{recv_frame} (Verified)")
                ack.write(
                    {
                        "src": app_port,
                        "seq": seq,
                        "data": encode_text(const.Frame.ACK),
                        "dst": recv_frame.src,
                    }
                )
                net.send_to_phy(ack.binary)
                recv_cnt += 1

                # 如果这是最后一帧，就退出循环。
                if recv_cnt == recv_total + 1:
                    break

            # 如果触发了Keepalive机制，就不能传消息给应用层。
            if timeout_cnt == const.Network.KEEPALIVE_MAX_RETRY:
                print("[Warning] Connection lost.")
                continue

            # 将消息传给应用层。
            net.send_to_app(message_type)
            net.send_to_app(recv_message)

            # 计算网速。
            end_time = time()
            speed = 16 * len(recv_message) / (end_time - start_time)
            print(f"[Log] Receiving speed: {round(speed, 1)}bps")

        # 如果要发送，就封装、发送、确认。
        else:
            # 确定目的端口。
            if mode == const.Mode.UNICAST:
                dst = net.receive_from_app()
            else:
                dst = const.Topology.BROADCAST_PORT
            print(f"[Log] Destination port: {dst}")

            # 确定消息类型。
            message_type = net.receive_from_app()
            message_type_name = (
                "text" if message_type == const.MessageType.TEXT else "picture"
            )
            print(f"[Log] Message type: {message_type_name}")

            # 确定消息。
            app_message = net.receive_from_app()
            send_total = Frame.calc_frame_num(app_message)

            # 第一帧是请求帧，告知对方总帧数和消息类型。
            seq = (seq + 1) % (2 ** const.Frame.SEQ_LEN)
            request = Frame()
            request.write(
                {
                    "src": app_port,
                    "seq": seq,
                    "data": f"{dec_to_bin(send_total, 16)}{dec_to_bin(int(message_type), 16)}",
                    "dst": dst,
                }
            )
            send_frames = [request]

            # 逐帧封装。
            for i in range(send_total):
                seal_message = app_message[
                    i * const.Frame.DATA_LEN : (i + 1) * const.Frame.DATA_LEN
                ]
                seq = (seq + 1) % (2 ** const.Frame.SEQ_LEN)
                send_frame = Frame()
                send_frame.write(
                    {"src": app_port, "seq": seq, "data": seal_message, "dst": dst}
                )
                send_frames.append(send_frame)

            # 逐帧发送。
            send_cnt, timeout_cnt = 0, 0
            start_time = time()
            while True:
                # 向物理层发送消息。
                net.send_to_phy(send_frames[send_cnt].binary)
                if send_cnt == 0:
                    print(
                        f"[Frame {send_frames[send_cnt].seq}] {send_total} frame(s) of {message_type_name}."
                    )
                else:
                    print(f"{send_frames[send_cnt]} (Sent)")

                # 每个接收端的回复都要接收，即使已经知道要重传。
                dst_num = (
                    1
                    if mode == const.Mode.UNICAST
                    else const.Topology.BROADCAST_RECVER_NUM
                )
                ack_cnt = 0
                for _ in range(dst_num):
                    # 从物理层接收回复。
                    resp_binary, success = net.receive_from_phy()

                    # 如果超时了，说明之后没有信息会发来了，直接跳出循环，同时超时次数+1。
                    if not success:
                        print(f"[Frame {send_frames[send_cnt].seq}] Timeout.")
                        timeout_cnt += 1
                        break

                    # 一旦有回复，就重置超时次数。
                    timeout_cnt = 0

                    # 解包读取回复，如果是ACK，ACK次数就+1。
                    resp_frame = Frame()
                    resp_frame.read(resp_binary)
                    resp_message = decode_text(resp_frame.data)
                    if resp_message == const.Frame.ACK:
                        print(f"[Frame {resp_frame.seq}] ACK.")
                        ack_cnt += 1
                    elif resp_message == const.Frame.NAK:
                        print(f"[Frame {resp_frame.seq}] NAK.")
                    else:
                        print(f"[Frame {resp_frame.seq}] Unknown response.")

                # 如果连续多次超时，就停止重传。
                if timeout_cnt == const.Network.KEEPALIVE_MAX_RETRY:
                    print("[Warning] Connection lost.")
                    break

                # 如果每个接收端都ACK了，发送的帧数就+1。
                if ack_cnt == dst_num:
                    send_cnt += 1

                # 如果这是发送的最后一帧，就跳出循环。
                if send_cnt == send_total + 1:
                    break

            # 释放这些帧的空间。
            del send_frames

            # 计算网速。
            end_time = time()
            speed = 16 * len(app_message) / (end_time - start_time)
            print(f"[Log] Sending speed: {round(speed, 1)}bps")
