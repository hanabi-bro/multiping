import re
from os import getpid
from datetime import datetime
from subprocess import run
from shlex import split as shlex_split
from random import randint
from pathlib import Path
import sys
sys.path.append(f'{Path(Path(__file__).parent, "..")}')
from logger import my_logger
logger = my_logger(__name__, level='DEBUG')
from iptoolz import get_src_addr

run(['chcp.com', '65001'], capture_output=True)

def ping(
        dst,
        src=None,
        timeout=1,
        ttl=16,
        block_size=64,
        id=None,
        seq=None,
        debug=False):
    """run
    id = 0, use pid
    return:
        res(dict):  [reply_type, ttl, src, dst, reply_from, starttime, rtt]
                    reply_type is icmp type: 99 is unknown, 98 is timeout, 97 is transmission failed (this app specific)
    Todo:
        * 想定外のエラーの場合の処理
        * ログ処理
        * テスト
    """
    pid = getpid()
    if id == 0:
        id = pid
    elif id is None:
        id = randint(1, 65535)
    if seq is None:
        seq = randint(1, 65535)
    starttime = datetime.now()
    icmp_type = 99      # Unknown Error
    icmp_code = 0       # default
    timeout = timeout * 1000  # For Windows Native Ping
    reply_from = None

    # ping command generate
    if src:
        ping_cmd = f'ping -S {src} -i {ttl} -w {timeout} -n 1 -l {block_size} {dst}'
    else:
        src = get_src_addr(dst)
        ping_cmd = f'ping -i {ttl} -w {timeout} -n 1  -l {block_size}  {dst}'
    ping_cmd_params = shlex_split(ping_cmd)

    # run ping
    ping_res = run(
        ping_cmd_params,
        capture_output=True,
        text=True,
    )

    rtt = (datetime.now() - starttime).total_seconds()

    if debug: logger.debug(f'{ping_res}')

    if ping_res.returncode == 0:
        for i in ping_res.stdout.rstrip("\n").split("\n"):
            if re.search(r'Reply +from +(\d+\.\d+\.\d+\.\d+): +TTL +expired +in +transit', i):
                icmp_type = 11
                reply_from = re.search(
                        r'Reply +from +(\d+\.\d+\.\d+\.\d+): +.*', i).groups()[0]
                break

            ## Success (Get icmp type 0)
            # 応答時間が早い場合 '=' ではなく '<' が使われたりする。全仕様が不明なのでワイルドカードに変更
            # Reply from 192.168.0.1: bytes=64 time<1ms TTL=255
            elif re.search(r'Reply +from +(\d+\.\d+\.\d+\.\d+): +bytes.* +time.* +TTL.*', i):
                icmp_type = 0
                reply_from = re.search(
                        r'Reply from (\d+\.\d+\.\d+\.\d+): .*', i).groups()[0]
                break

            ## Other
            else:
                icmp_type = 88

    else:
        for i in ping_res.stdout.rstrip("\n").split("\n"):
            ## Unrechable
            if re.search(r'Reply from (\d+\.\d+\.\d+\.\d+)：Destination (net|host) unreachable', i):
                icmp_type = 3
                reply_from = re.search(
                    r'Reply from (\d+\.\d+\.\d+\.\d+)：Destination (net|host) unreachable', i
                ).groups()[0]
                break
            ## Request Timeout
            elif re.search(r"Request timed out", i):
                icmp_type = 98
                break
            ## Transmit Failed
            elif re.search(r"PING: transmit failed", i):
                icmp_type = 97
                break
            ## General failure
            elif re.search(r"General failure", i):
                icmp_type = 96
                break

    return {
        'pid': pid,
        'starttime': starttime,
        'dst': dst,
        'src': src,
        'type': icmp_type,
        'code': icmp_code,
        'reply_from': reply_from,
        'rtt': rtt,
        'ttl': ttl,
        'id': id,
        'seq': seq
    }


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('dst', type=str, help='Target Address')
    parser.add_argument('-S', '--src', help='Source Address')
    parser.add_argument('-t', '--timeout', help='Timeout second', default=1)
    parser.add_argument('-H', '--ttl', help='Set the IP TTL field', default=16)
    parser.add_argument('-c', '--count', help='Number of request packets to send', default=1)
    parser.add_argument('-s', '--size', help='Size of ping data to send', default=64)
    args = parser.parse_args()

    from pprint import pprint
    pprint(ping(args.dst, args.src, args.timeout, args.ttl, args.size))


"""
```
$ ping -S 10.156.144.79 -i 10 -w 1000 -n 1 -l 64 1.1.1.1

Pinging 1.1.1.1 from 10.156.144.79 with 64 bytes of data:
PING: transmit failed. General failure.

Ping statistics for 1.1.1.1:
    Packets: Sent = 1, Received = 0, Lost = 1 (100% loss),
```
```
$ ping -S 10.156.134.79 -i 10 -w 1000 -n 1 -l 64 1.1.1.1

Pinging 1.1.1.1 from 10.156.134.79 with 64 bytes of data:
Reply from 203.190.230.72: TTL expired in transit.

Ping statistics for 1.1.1.1:
    Packets: Sent = 1, Received = 1, Lost = 0 (0% loss),
```
"""