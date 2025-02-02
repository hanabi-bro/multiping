from re import compile, IGNORECASE
from subprocess import Popen, PIPE, TimeoutExpired
from os import environ
from datetime import datetime

from pathlib import Path
import sys
# sys.path.append(f'{Path(Path(__file__).parent.parent).resolve()}')
sys.path.append(f'{Path(Path(__file__).parent.parent.parent).resolve()}')

from lib.iptools import get_src_addr

MY_ENV = dict(environ)
MY_ENV['LC_ALL'] = 'C'


# リプライアドレス
"""
64 bytes from a23-192-228-80.deploy.static.akamaitechnologies.com (23.192.228.80): icmp_seq=1 ttl=50 time=123 ms
"""
RE_REPLY_FROM = compile(r'\d+ bytes from .* ?(\d+\.\d+\.\d+\.\d+): icmp_seq=(\d+) ttl=\d+ time=\d+.\d+ ms', IGNORECASE)

# ttl expire
"""
From 62.115.140.25 icmp_seq=1 Time to live exceeded
"""
# unreachable
"""
From 172.16.201.100 icmp_seq=1 Destination Host Unreachable
"""

RE_REPLY_ERROR = compile(r'From .*(\d+\.\d+\.\d+\.\d+).* ?icmp_seq=(\d+) ?.*(Time to live exceeded|Destination .* Unreachable).*', IGNORECASE)

# packet loss
RE_PACKET_LOSS = compile(r'100% packet loss', IGNORECASE)


def ping(
        dst,
        src='',
        timeout=1,
        ttl=16,
        block_size=64,
        id='',
        seq='',
        debug=False):

    if src:
        ping_cmd = ['ping', dst, '-4', '-n', '-c', '1', '-W', str(timeout), '-t', str(ttl), '-s', 'block_size', '-I', src]
    else:
        src = get_src_addr(dst)
        ping_cmd = ['ping', dst, '-4', '-n', '-c', '1', '-W', str(timeout), '-t', str(ttl), '-s', 'block_size']

    starttime = datetime.now()
    icmp_type = 99      # Unknown Error
    icmp_code = 0       # default
    reply_from = ''

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
    finally:
        """"""
        # print(ping_cmd)
        # print(out)
        # print(ping_process.returncode)

    rtt = (datetime.now() - starttime).total_seconds()

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
    reply_from = ''
    seq = 0
    icmp_type = 0
    icmp_code = 0

    if reply_from_line:
        reply_from = reply_from_line.group(1)
        seq = reply_from_line.group(2)
        icmp_type = 0
        icmp_code = 0

    return reply_from, seq, icmp_type, icmp_code


def parse_error_output(out):
    reply_error_line = RE_REPLY_ERROR.search(out)
    packet_loss_line = RE_PACKET_LOSS.search(out)

    reply_from = ''
    seq = 0
    icmp_type = 99
    icmp_code = 99

    if reply_error_line:
        reply_from = reply_error_line.group(1)
        seq = reply_error_line.group(2)
        if reply_error_line.group(3) == 'Time to live exceeded':
            icmp_type = 11
            icmp_code = 0
        elif reply_error_line.group(3) == 'Destination Net Unreachable':
            icmp_type = 3
            icmp_code = 1
        elif reply_error_line.group(3) == 'Destination Host Unreachable':
            icmp_type = 3
            icmp_code = 0
        else:
            icmp_type = 3
            icmp_code = 99
    elif packet_loss_line:
        reply_from = ''
        seq = 0
        icmp_type = 98
        icmp_code = 98        
    
    return reply_from, seq, icmp_type, icmp_code


if __name__ == '__main__':
    # import argparse
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
# 正常
PING example.com (23.192.228.80) 56(84) bytes of data.
64 bytes from a23-192-228-80.deploy.static.akamaitechnologies.com (23.192.228.80): icmp_seq=1 ttl=50 time=123 ms

--- example.com ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 122.870/122.870/122.870/0.000 ms
"""


"""
# タイムアウト
PING www.nvc.co.jp (150.60.155.99) 56(84) bytes of data.

--- www.nvc.co.jp ping statistics ---
1 packets transmitted, 0 received, 100% packet loss, time 0ms
"""

"""
# Destination Host Unreachable
PING 172.16.201.2 (172.16.201.2) 56(84) bytes of data.
From 172.16.201.100 icmp_seq=1 Destination Host Unreachable

--- 172.16.201.2 ping statistics ---
1 packets transmitted, 0 received, +1 errors, 100% packet loss, time 0ms
"""

"""
# TTL Expire
PING www.nvc.co.jp (150.60.155.99) 56(84) bytes of data.
From 92.203.141.236 icmp_seq=1 Time to live exceeded

--- www.nvc.co.jp ping statistics ---
1 packets transmitted, 0 received, +1 errors, 100% packet loss, time 0ms
"""