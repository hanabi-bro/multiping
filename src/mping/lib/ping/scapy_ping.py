from scapy.all import sr1, IP, ICMP
from logging import getLogger, ERROR
getLogger("scapy.runtime").setLevel(ERROR)
from random import randint
from datetime import datetime
import sys
sys.path.append(f'{Path(Path(__file__).parent, "..")}')
from logger import my_logger
logger = my_logger(__name__, level='DEBUG')

def ping(dst, src=None, timeout=1, ttl=16, block_size=64, id=randint(1, 65535), seq=randint(1, 65535)):
    starttime = datetime.now()
    icmp_type = 99      # Timeout
    icmp_code = 0       # default
    reply_from = None

    if src:
        pkt = IP(dst=dst, src=src, ttl=ttl)/ICMP(id=id, seq=seq)
    else:
        pkt = IP(dst=dst, ttl=ttl)/ICMP(id=id, seq=seq)
        src = pkt.src

    ans = sr1(pkt, timeout=timeout, verbose=0)
    rtt = (datetime.now() - starttime).total_seconds()

    if ans:
        reply_from = ans.src
        icmp_type = ans.type
        icmp_code = ans.code

    return {
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

    print(ping(args.dst, args.src, args.timeout, args.ttl, args.size))
