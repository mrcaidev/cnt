# 单元三习题

## 第 1 题

> 请自拟一个 14 位长的二进制码串，计算其海明纠错编码。将编码后的码串某位翻转，利用海明码进行纠错。

自拟码串：`01 0010 1100 1001`

| 序号  |   1   |   2   |   3   |   4   |   5   |   6   |   7   |   8   |   9   |  10   |  11   |  12   |  13   |    14    |    15    |  16   |    17    |    18    |    19    |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :------: | :------: | :---: | :------: | :------: | :------: |
| 符号  | $P_1$ | $P_2$ | $D_1$ | $P_3$ | $D_2$ | $D_3$ | $D_4$ | $P_4$ | $D_5$ | $D_6$ | $D_7$ | $D_8$ | $D_9$ | $D_{10}$ | $D_{11}$ | $P_5$ | $D_{12}$ | $D_{13}$ | $D_{14}$ |
| 数值  |   1   |   1   |   0   |   1   |   1   |   0   |   0   |   0   |   1   |   0   |   1   |   1   |   0   |    0     |    1     |   1   |    0     |    0     |    1     |

海明纠错编码：`11101`

翻转 1 位后的误码：`01 0110 1100 1001`

| 序号  |   1   |   2   |   3   |   4   |   5   |   6   |   7   |   8   |   9   |  10   |  11   |  12   |  13   |    14    |    15    |  16   |    17    |    18    |    19    |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :------: | :------: | :---: | :------: | :------: | :------: |
| 符号  | $P_1$ | $P_2$ | $D_1$ | $P_3$ | $D_2$ | $D_3$ | $D_4$ | $P_4$ | $D_5$ | $D_6$ | $D_7$ | $D_8$ | $D_9$ | $D_{10}$ | $D_{11}$ | $P_5$ | $D_{12}$ | $D_{13}$ | $D_{14}$ |
| 收得  |   1   |   1   |   0   |   1   |   1   |   0   | **1** |   0   |   1   |   0   |   1   |   1   |   0   |    0     |    1     |   1   |    0     |    0     |    1     |
| 验得  | **0** | **0** |   0   | **0** |   1   |   0   |   0   |   0   |   1   |   0   |   1   |   1   |   0   |    0     |    1     |   1   |    0     |    0     |    1     |

计算校验码时，第 1、2、4 位与得到的码串不同，所以可判定码串第 7 位出错，翻转后得到 `01 0010 1100 1001`，与原始码串相同。

## 第 2 题

> 请自拟一个 10 位长的二进制码串。设 CRC 校验生成式为：$G(x)=x^4+x^3+1$。
>
> 1. 请计算出校验码。
>
> 2. 将编码后的码串某两位翻转，利用 CRC 校验进行检错。

自拟码串：`10 1110 0101`

1. CRC 校验生成式对应的二进制数：`11001`；则校验码应为 `10 1110 0101 0000` / `11001` 所得的余数，为 `0010`。
2. 将上一问得到的码串翻转 2 位，得 `10 0010 0101 0010`，接收方使用 `11001` 检错时，余数为 `0111`，不为 `0`，说明出错。

## 第 3 题

> 设无线信道误码率为 $5\times 10^{-5}$，信道速率为 300Mbps，出现比特错误的平均时间间隔为多少？

平均 $2\times 10^4$ 位中会出现一比特错误，平均时间间隔为

$$
t=\frac{2\times 10^4}{300\times 1024^2}=6.36\times 10^{-5}s
$$

## 第 4 题

> 设滑动窗口协议的收发窗口都为 6，帧序号为 0-8 循环。双方在传输过程中发现了差错，使用选择性重传并进行了控制。什么情况下会出现发送方认为自己正确发送的帧数量，比接收方认为正确接收的数量多 2 个及以上，即例举一种可能的场景和演变过程。

如果是接收方认为自己正确接收的帧数比发送方认为正确发送的多2个及以上，那么有可能例如：

- 发送方发送第 1、2 帧；接收方接收第 2 帧时出错，向发送方报错；
- 发送方在收到报错信息前，以为自己没错，又发送了第 3、4 帧；
- 发送方在第 5 帧前，收到了第 2 帧的报错，以为自己只发对了第 1 帧；
- 但此时发送方已经接收到了正确的第 1、3、4 帧，只是第 3、4 帧被缓存了起来。
- 此时，接收方认为自己正确接收的帧数比发送方认为正确发送的多2帧。
- 如果RTT够高，还可能出现多 3、4...... 帧的情况。

## 第 5 题

> 设某个信道上设计的滑窗协议最佳 $W_s$ 为 2000 字节，已知数据传输速率为 10Mbps，如果平均帧长为 200 字节：
>
> 1. 该信道的传输往返延时为多少？
>
> 2. 如果最小帧长度为 50 字节，这个滑动窗口协议的序号最小容量上限值为多少？（序号是从 0 开始编到容量上限，然后循环回来继续编号）
>
> 3. 发送窗口大小为多少帧？

1. 最坏的情况如下：发送方发送的第一个帧就错了，但直到发了最后一帧才收到接收方的报错。

$$
RTT=\frac{2000\times 8}{10\times 1024^2}=1.53ms
$$

2. 由 $W_s$ 为 2000 字节、最小帧长为 50 字节，可知窗口内最多有 40 帧。又有发送窗口大小 $\le$ (序号容量 + 1) / 2，所以序号最小容量上限为79。
3. 发送窗口为 40 帧。

## 第 6 题

> 假设当前网络情况稳定，TCP 协议持续稳定地滑动窗口，已测得 A、B 之间的 RTT 为 10ms，TCP 窗口大小为 2KB，请问，发送方测得的网速是多少？

$$
v=\frac{2\times 1024\times 8}{10\times 10^{-3}}=1.6Mbps
$$