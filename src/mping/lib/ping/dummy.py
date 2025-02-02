from random import random, randint, choices
from time import sleep
from datetime import datetime


def ping(dst, src='127.0.0.1', timeout=1, ttl=16, block_size=64, id=None, seq=None):
    if id is None:
        id = randint(1, 65535)
    if seq is None:
        seq = randint(1, 65535)
    starttime = datetime.now()
    icmp_type = choices([0, 99], weights=[10, 1])[0]
    icmp_code = 0
    reply_from = dst
    rtt = random()

    sleep(rtt)

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
