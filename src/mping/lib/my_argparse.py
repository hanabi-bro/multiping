from textwrap import dedent
from argparse import (
    OPTIONAL, SUPPRESS, ZERO_OR_MORE,
    ArgumentDefaultsHelpFormatter, ArgumentParser,
    RawDescriptionHelpFormatter, RawTextHelpFormatter,
    Action)


class MyHelpFormatter(
    RawTextHelpFormatter,
    RawDescriptionHelpFormatter,
    ArgumentDefaultsHelpFormatter
):
    def _format_action(self, action: Action) -> str:
        return super()._format_action(action) + "\n"

    def _get_help_string(self, action):
        help = action.help
        if action.required:
            help += " (required)"

        if "%(default)" not in action.help:
            if action.default is not SUPPRESS:
                defaulting_nargs = [OPTIONAL, ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    if action.default is not None and not action.const:
                        help += " (default: %(default)s)"
        return help


class MyArgumentParser(ArgumentParser):
    def error(self, message):
        print(dedent(
            """
            !!! Args Error !!!
            error occured while parsing args
            """
            + str(message)
        ).strip())
        # self.print_help() 
        exit()


def parse_args(description):
    return MyArgumentParser(
        description=description,
        formatter_class=MyHelpFormatter
    )


if __name__ == '__main__':
    from textwrap import dedent
    description = dedent(
        """
        argsサンプル
        改行が出来る
        参考: https://qiita.com/yuji38kwmt/items/c7c4d487e3188afd781e
        """
    ).strip()
    parser = parse_args(description)

    parser.add_argument('-m', '--method', required=True, help=dedent(
        """
        サンプル
        """).strip())

    parser.add_argument('-f', '--file',  help=dedent(
        """
        target list file name,
        default: destination_list.csv'
        """).strip())
    parser.add_argument('-l', '--list', help=dedent(
        """
        target list. delimita is ,
        e.g.) booya_ping -l 1.1.1.1,8.8.8.8
        """).strip())

    # parser.add_argument('-i', '--ini', help='target list. delimita is , \ne.g.) booya_ping -l 1.1.1.1,8.8.8.8')
    args = parser.parse_args()

