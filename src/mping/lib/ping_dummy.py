from datetime import datetime
from random import random, randint, choices
from socket import socket, AF_INET, SOCK_DGRAM, gethostbyname, gethostname
from time import sleep
from os import getpid


def ping(dst, src=None, timeout=1, ttl=16, block_size=64, id=None, seq=None):
    starttime = datetime.now()
    pid = getpid()
    if id == 0:
        id = pid
    elif id is None:
        id = randint(1, 65535)

    if seq is None:
        seq = randint(1, 65535)

    icmp_type = choices([0, 11, 98, 99], weights=[10, 2, 1, 1], k=1)[0]
    icmp_code = 0   # default
    if icmp_type == 0:
        reply_from = dst
    elif icmp_type == 11:
        reply_from = '10.10.10.10'
    else:
        reply_from = ''

    if src is None:
        try:
            sock = socket(AF_INET, SOCK_DGRAM)
            sock.connect_ex((dst, 0))
            src = sock.getsockname()[0]
            sock.close()
        except Exception:
            src = gethostbyname(gethostname())

    sleep(random())
    rtt = (datetime.now() - starttime).total_seconds()

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
