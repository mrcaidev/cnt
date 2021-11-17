from utils.coding import *
from utils.param import Constant as const


class Frame:
    """报文帧。"""

    def __init__(self) -> None:
        """初始化帧属性为默认值。"""
        self.__src = 0
        self.__seq = 0
        self.__data = ""
        self.__dst = 0
        self.__checksum = 0
        self.__verified = True
        self.__binary = ""

    def __str__(self) -> str:
        """打印帧信息。

        Returns:
            帧信息字符串。
        """
        return f"[Frame {self.__seq}] ({self.__src}→{self.__dst}, {self.__verified}) {self.__data}"

    @property
    def src(self) -> int:
        """将源地址设为只读。"""
        return self.__src

    @property
    def seq(self) -> int:
        """将序号设为只读。"""
        return self.__seq

    @property
    def data(self) -> str:
        """将封装数据设为只读。"""
        return self.__data

    @property
    def dst(self) -> int:
        """将目的地址设为只读。"""
        return self.__dst

    @property
    def verified(self) -> bool:
        """将检验结果设为只读。"""
        return self.__verified

    @property
    def binary(self) -> str:
        """将帧对应的01序列设为只读。"""
        return self.__binary

    def write(self, src: int, seq: int, data: str, dst: int) -> None:
        """
        将信息写入帧。

        Args:
            src: 帧的源端口。
            seq: 帧的序号。
            data: 要封装的消息。
            dst: 帧的目的端口。
        """
        self.__src = src
        self.__seq = seq
        self.__data = data
        self.__dst = dst

        checksum_target = f"{dec_to_bin(src, const.PORT_LEN)}{dec_to_bin(seq, const.SEQ_LEN)}{data}{dec_to_bin(dst, const.PORT_LEN)}"
        self.__checksum = Frame.__generate_checksum(checksum_target)
        self.__verified = True

        self.__binary = Frame.__add_locator(
            f"{checksum_target}{dec_to_bin(self.__checksum, const.CHECKSUM_LEN)}"
        )

    def read(self, binary: str) -> None:
        """
        读入01序列，解析为帧。

        Args:
            binary: 物理层中传输的01序列字符串。
        """
        message, extracted = Frame.__extract_message(binary)

        self.__src = bin_to_dec(message[: const.PORT_LEN])
        self.__seq = bin_to_dec(
            message[const.PORT_LEN : const.PORT_LEN + const.SEQ_LEN]
        )
        self.__data = message[
            const.PORT_LEN + const.SEQ_LEN : -const.CHECKSUM_LEN - const.PORT_LEN
        ]
        self.__dst = bin_to_dec(
            message[-const.CHECKSUM_LEN - const.PORT_LEN : -const.CHECKSUM_LEN]
        )
        self.__checksum = bin_to_dec(message[-const.CHECKSUM_LEN :])
        self.__verified = extracted and self.__checksum == Frame.__generate_checksum(
            message[: -const.CHECKSUM_LEN]
        )
        self.__binary = binary

    def __extract_message(binary: str) -> tuple[str, bool]:
        """
        从有干扰的01序列中提取帧序列。

        Args:
            binary: 物理层中传输的01序列字符串。

        Returns:
            一个二元元组。
            - [0] 提取的帧序列。
            - [1] 是否提取成功，成功为True，失败为False。
        """
        message = ""
        start = binary.find(const.LOCATOR)
        # 如果没找到定位串，就返回空帧。
        if start == -1:
            return const.EMPTY_FRAME, False

        # 向后反变换。
        start += const.LOCATOR_LEN
        susp = binary.find(const.SUSPICIOUS, start)
        while susp != -1:
            # 如果到达帧尾，就返回提取出的信息。
            if binary[susp + const.SUSPICIOUS_LEN] == "1":
                message += binary[start : susp - 1]
                return message, True
            # 如果只是连续5个1，就删除后面的0，然后继续寻找。
            else:
                message += binary[start : susp + const.SUSPICIOUS_LEN]
                start = susp + const.SUSPICIOUS_LEN + 1
                susp = binary.find(const.SUSPICIOUS, start)

        # 如果只找到了1个定位串，也返回空帧。
        return const.EMPTY_FRAME, False

    def __add_locator(binary: str) -> str:
        """
        变换01序列，并加上定位串。

        Args:
            binary: 待操作的01序列，包含帧内的所有信息。

        Returns:
            加上定位串后的01序列。
        """
        # 变换，在连续的5个`1`之后添加1个`0`。
        cur = binary.find(const.SUSPICIOUS)
        while cur != -1:
            binary = f"{binary[: cur + const.SUSPICIOUS_LEN]}0{binary[cur + const.SUSPICIOUS_LEN :]}"
            cur = binary.find(const.SUSPICIOUS, cur + 6)

        return f"{const.LOCATOR}{binary}{const.LOCATOR}"

    def __generate_checksum(binary: str) -> int:
        """
        生成校验和。

        Args:
            binary: 要对其生成校验和的01序列。

        Returns:
            16位校验和。
        """
        return sum(
            [bin_to_dec(binary[i * 8 : i * 8 + 8]) for i in range(len(binary) // 8)]
        )

    def calcFrameNum(message: str) -> int:
        """
        计算消息需要分几帧发送。

        Args:
            message: 当前要发送的消息。

        Returns:
            计算所得的帧数。
        """
        length = len(message)
        return (
            length // const.DATA_LEN
            if length % const.DATA_LEN == 0
            else length // const.DATA_LEN + 1
        )
