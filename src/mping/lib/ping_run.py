import platform


class Ping():
    def __init__(self):
        os = platform.system()
        if os == 'Windows':
            from .ping.windows import ping
        elif os == 'Linux':
            from .ping.linux import ping
        elif os == 'Darwin':
            from .ping.macos import ping

        self.ping = ping

    def run(
            self,
            dst,
            src=None,
            timeout=1,
            ttl=16,
            block_size=64,
            id=None,
            seq=None,
            debug=False):
        return self.ping(dst, src, timeout, ttl, block_size, id, seq, debug)


if __name__ == '__main__':
    ping = Ping()
    print(ping.run('2.2.2.2', id=0))