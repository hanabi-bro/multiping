from configparser import ConfigParser
from pathlib import Path

from time import sleep
from threading import Event, Lock
from concurrent.futures import ThreadPoolExecutor
from signal import signal, SIGINT

from datetime import datetime
from re import compile

import traceback

from textwrap import dedent

from rich.live import Live
from rich.table import Table
from rich.console import Console

from lib.iptools import get_src_addr, get_my_hostname
from lib.fire_and_forget import fire_and_forget
from lib.my_argparse import parse_args
from lib.ping_run import Ping

from sys import exit
from os import getcwd


class MultiPing:
    def __init__(self, dst_file='destination_list.csv', dst_args=None, ini_file=None):
        self.dst_file = None
        self.ini_file = None

        # 実行ディレクトリ
        self.current_dir = Path(getcwd())

        self.ping_list = []
        self.my_hostname = get_my_hostname()

        # 停止フラグ
        self.stop_event = Event()
        self.ping_loop = False

        # コンソール
        self.console = Console()
        self.ping = Ping()

    def file_exsit(self, file_path):
        return Path(file_path).is_file()

    def gen_ini_file(self):
        from textwrap import dedent
        ini_description = dedent(
            """
            [ping]
            TTL = 64
            timeout = 1
            Retries = 1
            Interval = 1

            [tui]
            view_recent = 30
            view_sucess  = [green]O
            view_fail    = [red]X
            view_expired = [yellow]▲

            [log]
            result_directory = ./results
            ping_success = OK
            ping_fail = NG
            ping_expired = Expired
            """
        ).strip()

        with open(self.ini_file, 'w', encoding='utf-8') as f:
            print(ini_description, file=f)

    def gen_dst_file(self):
        from textwrap import dedent
        dst_list = dedent(
            """
            1.1.1.1
            example.com
            """
        ).strip()

        with open(self.dst_file, 'w', encoding='utf-8') as f:
            print(dst_list, file=f)

    def read_dst_file(self):
        with open(self.dst_file, 'r', encoding='utf-8') as f:
            dst_list = [line.split(',')[0].strip() for line in f.readlines()]
        return dst_list

    def setting(self,  dst_file=None, dst_args=None, ini_file=None, ping_args={}):
        # iniファイルチェック
        if ini_file and self.file_exsit(Path(ini_file)):
            self.ini_file = Path(ini_file)
        else:
            self.ini_file = Path(Path(__file__).parent, 'mping.ini')
            if not self.file_exsit(self.ini_file):
                self.gen_ini_file()

        # コンフィグロード
        config = ConfigParser()
        try:
            config.read(self.ini_file, encoding='utf-8')
        except Exception:
            self.gen_ini_file()
            config.read(self.ini_file, encoding='utf-8')

        # dstファイルチェック
        # dst_file指定あり
        # 存在チェック、無ければエラー終了
        # dst_argsしていあり
        # 両方指定なし
        #   デフォルト存在チェック
        #   無ければ作成
        # pingリスト作成
        if dst_args:
            dst_list = dst_args.split(',')
        elif dst_file:
            if self.file_exsit(Path(dst_file)):
                self.dst_file = Path(dst_file)
                dst_list = self.read_dst_file()

            else:
                self.console.print(f'dst file {Path(dst_file)} is not Found')
                exit()
        else:
            self.dst_file = Path('destination_list.csv')
            if not self.file_exsit(self.dst_file):
                self.gen_dst_file()
                dst_list = self.read_dst_file()

        # pingリスト作成
        if dst_args:
            dst_list = dst_args.split(',')
        else:
            with open(self.dst_file, 'r') as f:
                dst_list = f.readlines()

        self.ping_list = []
        self.gen_ping_list(dst_list)

        # Pingパラメータ
        ping_args.setdefault('ttl', int(config.get('ping', 'ttl', fallback=1)))
        ping_args.setdefault('timeout', float(config.get('ping', 'timeout', fallback=1)))
        ping_args.setdefault('interval', float(config.get('ping', 'interval', fallback=1)))
        ping_args.setdefault('retry_count', float(config.get('ping', 'retry_count', fallback=1)))
        self.ttl = ping_args['ttl']
        self.timeout = ping_args['timeout']
        self.interval = ping_args['interval']
        self.retry_count = ping_args['retry_count']

        # 表示パラメータ
        self.view_recent = int(config.get('tui', 'view_recent', fallback=1))

        # 表示マーク
        self.view_sucess = str(config.get('tui', 'view_sucess', fallback=1))
        self.view_fail = str(config.get('tui', 'view_fail', fallback=1))
        self.view_expired = str(config.get('tui', 'view_expired', fallback=1))

        # ログパラメータ
        self.res_dir = Path(str(config.get('log', 'result_directory', fallback=1)))
        self.log_success = str(config.get('log', 'ping_success', fallback=1))
        self.log_fail = str(config.get('log', 'ping_fail', fallback=1))
        self.log_expired = str(config.get('log', 'ping_expired', fallback=1))

        # ログディレクトリ
        Path(self.res_dir).mkdir(exist_ok=True)

    def gen_ping_list(self, dst_list):
        for line in dst_list:
            dst = line.strip()
            # 空白行とコメント行をスキップ
            skip_pattern = compile(r'^\s*(#.*)?$')
            if skip_pattern.match(dst):
                continue

            # 送信元IPアドレス取得
            try:
                src_addr = get_src_addr(dst)
            except Exception:
                src_addr = ''

            self.ping_list.append({
                'dst': dst,
                'machine_name': get_my_hostname(),
                'src': src_addr,
                'success_count': 0,
                'fail_count': 0,
                'results': [],
                'reply': '',
                'rtt': ''
            })

    def ping_dst(self, ping_dict, lock):
        # while not stop_event.is_set():  # 停止フラグがセットされていない場合
        while self.ping_loop:
            ping_dict['start_time'] = datetime.now()

            try:
                ping_reply = self.ping.run(
                    ping_dict['dst'], timeout=self.timeout,
                    ttl=self.ttl, id=0)
                ping_dict['src'] = ping_reply['src']
                ping_dict['reply_from'] = ping_reply['reply_from']
                ping_dict['type'] = ping_reply['type']
                ping_dict['code'] = ping_reply['code']

                if ping_reply['type'] == 0:
                    ping_dict['reply'] = self.log_success
                    ping_dict['results'].append(self.view_sucess)
                    ping_dict['success_count'] += 1
                    ping_dict['rtt'] = ping_reply['rtt']
                elif ping_reply['type'] == 11:
                    ping_dict['reply'] = self.log_expired
                    ping_dict['results'].append(self.view_expired)
                    ping_dict['fail_count'] += 1
                    ping_dict['rtt'] = ping_reply['rtt']
                else:
                    ping_dict['reply'] = self.log_fail
                    ping_dict['results'].append(self.view_fail)
                    ping_dict['fail_count'] += 1
                    ping_dict['rtt'] = ''

                view_num = self.view_recent
                ping_dict['results'] = ping_dict['results'][-view_num:]

                rtt = (datetime.now() - ping_dict['start_time']).total_seconds()

                # with lock:
                self.log_ping_result(ping_dict)

            except Exception as e:
                print(e)
                print(traceback.format_exc())
                exit()

            finally:
                # 設定インターバルに出来るだけ近づける
                if rtt < self.interval:
                    sleep(self.interval - rtt)

    def log_ping_result(self, ping_dict):
        log_file = Path(self.res_dir, f"{self.my_hostname}_{ping_dict['dst']}_log.csv")

        try:
            # 新規作成時はヘッダを書き込む
            if not log_file.exists():
                with open(log_file, 'w', encoding='utf-8') as f:
                    print('start_time,src,dst,result,rtt,type,code,reply_from', file=f)
            # ログ追記
            with open(log_file, 'a', encoding='utf-8') as f:
                message = [
                    ping_dict['start_time'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                    ping_dict['src'],
                    ping_dict['dst'],
                    ping_dict['reply'],
                    f'{ping_dict['rtt']}',
                    f'{ping_dict['type']}',
                    f'{ping_dict['code']}',
                    f'{ping_dict['reply_from']}',
                ]
                print(','.join(message), file=f)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            exit()

    def update_ping_table(self) -> Table:
        table = Table()
        table.title = 'Stop: Ctrl + C'
        table.add_column('Destination')
        table.add_column('OK/NG')
        table.add_column('RTT')
        table.add_column(f'result last {self.view_recent}')

        for row in self.ping_list:
            table.add_row(
                row['dst'],
                f'[green]{row['success_count']}[/]/[red]{row['fail_count']}[/]',
                '-' if isinstance(row['rtt'], str) else f'{row['rtt']:.3f}',
                ''.join(row['results'])
            )
        return table

    @fire_and_forget
    def run_ping_thread(self):
        lock = Lock()
        self.ping_loop = True
        with ThreadPoolExecutor(max_workers=len(self.ping_list)) as executor:
            for ping_dict in self.ping_list:
                executor.submit(self.ping_dst, ping_dict, lock)

    def run(self):
        with Live(self.update_ping_table(), refresh_per_second=10) as live:
            self.run_ping_thread()

            # SIGINT (Ctrl+C)をキャッチして停止
            def signal_handler(sig, frame):
                print("\nStoping...")
                self.stop_event.set()   # 停止フラグをセット
                self.ping_loop = False  # ping_loopはなぜかeventでは止まらない？？？

            signal(SIGINT, signal_handler)

            # 実行ループ (Ctrl+Cで停止)
            while not self.stop_event.is_set():
                live.update(self.update_ping_table())
                sleep(0.1)


if __name__ == '__main__':
    mp = MultiPing()

    parser = parse_args(description='multi ping tool')

    parser.add_argument('-f', '--file',  help=dedent(
        """
        target list file name,
        default: destination_list.csv'
        """).strip())
    parser.add_argument('-l', '--list', help=dedent(
        """
        target list. delimita is ,
        e.g.) -l 1.1.1.1,8.8.8.8
        """).strip())

    parser.add_argument('--ttl', type=int, help=dedent(
        """
        ping ttl
        e.g.) --ttl 64
        """).strip())

    parser.add_argument('--timeout', type=float, help=dedent(
        """
        ping timeout
        e.g.) --timeout 1
        """).strip())

    args = parser.parse_args()

    # pingパラメータ設定
    ping_args = {}
    if args.ttl is not None:
        if not 1 <= args.ttl <= 255:
            parser.error(f"TTL value {args.ttl} is out of range (must be between 1 and 255)")

        ping_args['ttl'] = args.ttl


    if args.timeout is not None:
        if not 0.1 <= args.timeout <= 100:
            parser.error(f"Timeout value {args.timeout} is out of range (must be between 0.1 and 100)")

        ping_args['timeout'] = args.timeout

    if args.list:
        mp.setting(dst_args=args.list, ping_args=ping_args)
    elif args.file:
        if not mp.file_exsit(args.file):
            parser.error(f'{Path(args.file).resolve()} is not Found')
            exit()
        mp.setting(dst_file=Path(args.file), ping_args=ping_args)

    else:
        mp.setting(ping_args=ping_args)

    mp.run()

    mp.console.print(f'ping log directory is \'{mp.res_dir.resolve()}\'')
