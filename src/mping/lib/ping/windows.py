from re import compile, IGNORECASE
from datetime import datetime
from subprocess import run, Popen, PIPE, TimeoutExpired
from pathlib import Path
import sys
sys.path.append(f'{Path(Path(__file__).parent.parent).resolve()}')
sys.path.append(f'{Path(Path(__file__).parent.parent.parent).resolve()}')

# from logger import my_logger
# logger = my_logger(__name__, level='DEBUG')
from lib.iptools import get_src_addr

# 出力パースのためutf-8、英字出力にする。
run(['chcp.com', '65001'], capture_output=True)

# Windowsの場合、TTL ExpireやDestination Unreachableでもreturn codeは0
# なので、出力で判断していく


# リプライアドレス
"""
Reply from 23.215.0.136: bytes=64 time=189ms TTL=42
or
Reply from 127.0.0.1: bytes=64 time<1ms TTL=128
or
Reply from 62.115.142.128: TTL expired in transit.
or
Reply from 172.16.201.111: Destination host unreachable.
or
Reply from 172.16.201.111: Destination network unreachable.
or
Reply from 172.16.201.111: Destination protocol unreachable.
"""
RE_REPLY_FROM = compile(r'Reply from .* ?(\d+\.\d+\.\d+\.\d+): (.*)', IGNORECASE)
r'\d+ bytes from .* ?(\d+\.\d+\.\d+\.\d+): icmp_seq=(\d+) ttl=\d+ time=\d+.\d+ ms'

# OK
RE_SUCCESS = compile(r'bytes.* time.* TTL.*', IGNORECASE)

# TTL EXPIRE
RE_TTL_EXPIRE = compile(r'TTL expired in transit', IGNORECASE)

# UNREACHABLE
RE_UNREACHABLE = compile(r'Destination (.*) unreachable', IGNORECASE)

# エラー
## Request Timeout
RE_TIMEOUT = compile(r'Request timed out')

## Transmit Failed
RE_TRANSMIT_FAILE = compile(r'transmit failed')

## General failure
RE_GENERAL_FAILURE = compile(r'General failure')


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
    os native pingのためid, seqは指定不要
    return:
        res(dict):  [reply_type, ttl, src, dst, reply_from, starttime, rtt]
                    reply_type is icmp type: 99 is unknown, 98 is timeout, 97 is transmission failed (this app specific)
    Todo:
        * 想定外のエラーの場合の処理
        * ログ処理
        * テスト
    """
    # ping command generate
    if src:
        ping_cmd = ['ping', '-4', '-S', src, '-i', str(ttl), '-w', str(timeout * 1000), '-n', '1', '-l', str(block_size), dst]
    else:
        src = get_src_addr(dst)
        ping_cmd = ['ping', '-4', '-i', str(ttl), '-w', str(timeout * 1000), '-n', '1', '-l', str(block_size), dst]

    starttime = datetime.now()
    seq = 0
    reply_from = None

    # run ping
    ping_process = Popen(
        ping_cmd,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    pid = id = ping_process.pid

    try:
        out, err = ping_process.communicate(timeout=timeout)
    except TimeoutExpired:
        ping_process.kill()
        out, err = ping_process.communicate()
        ping_process.terminate()

        return {
            'pid': pid,
            'starttime': starttime,
            'dst': dst,
            'src': src,
            'type': 98,
            'code': 98,
            'reply_from': '',
            'rtt': '',
            'ttl': ttl,
            'id': id,
            'seq': 0
        }
    finally:
        """"""
        # print(ping_cmd)
        # print(out)
        # print(ping_process.returncode)

    rtt = (datetime.now() - starttime).total_seconds()
    # if debug: logger.debug(f'{ping_res}')

    if ping_process.returncode == 0:
        reply_from, seq, icmp_type, icmp_code = parse_success_output(out)
    else:
        reply_from, seq, icmp_type, icmp_code = parse_error_output(out)

    # print({
    #     'pid': pid,
    #     'starttime': starttime,
    #     'dst': dst,
    #     'src': src,
    #     'type': icmp_type,
    #     'code': icmp_code,
    #     'reply_from': reply_from,
    #     'rtt': rtt,
    #     'ttl': ttl,
    #     'id': id,
    #     'seq': seq
    # })

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

def parse_success_output(out):
    reply_from_line = RE_REPLY_FROM.search(out)
    reply_from = reply_from_line.group(1)

    success_msg = RE_SUCCESS.search(reply_from_line.group(2))
    ttl_expire_msg = RE_TTL_EXPIRE.search(reply_from_line.group(2))
    unreacabhle_msg = RE_UNREACHABLE.search(reply_from_line.group(2))


    if success_msg:
        seq = 0
        icmp_type = 0
        icmp_code = 0
    elif ttl_expire_msg:
        seq = 0
        icmp_type = 0
        icmp_code = 0
    elif unreacabhle_msg:
        seq = 0
        icmp_type = 0
        icmp_code = 0
    else:
        seq = 0 
        icmp_type = 99
        icmp_code = 0

    return reply_from, seq, icmp_type, icmp_code


def parse_error_output(out):
    reply_from = ''
    if RE_TIMEOUT.search(out):
        seq = 0
        icmp_type = 98
        icmp_code = 98
    elif RE_TRANSMIT_FAILE.search(out):
        seq = 0
        icmp_type = 0
        icmp_code = 0
    elif RE_GENERAL_FAILURE.search(out):
        seq = 0
        icmp_type = 0
        icmp_code = 0
    else:
        seq = 0
        icmp_type = 99
        icmp_code = 99

    return reply_from, seq, icmp_type, icmp_code


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

