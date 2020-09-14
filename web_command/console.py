import argparse
import logging
import sys

from . import __version__
from .server import WebCommandServer


LOG_LEVELS = ('none', 'debug', 'info', 'warning', 'error', 'critical')


def get_parser():
    parser = argparse.ArgumentParser(
        description='Output a command to a web browser.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', type=str, nargs='*', metavar='COMMAND',
                        help='command to run')
    parser.add_argument('-a', '--host', type=str, default=WebCommandServer.DEFAULT_HOST,
                        help='host to bind to')
    parser.add_argument('-p', '--port', type=int, default=WebCommandServer.DEFAULT_PORT,
                        help='port to bind to')
    parser.add_argument('-s', '--suppress-output',
                        action='store_true', help='suppress output')
    parser.add_argument('-l', '--log-level', type=str, default='none',
                        metavar='LEVEL', choices=LOG_LEVELS, help='log level')
    parser.add_argument('-w', '--wait-time', type=int,
                        default=WebCommandServer.DEFAULT_WAIT_TIME,
                        help='seconds to wait before restarting command')
    parser.add_argument('-V', '--version',
                        action='store_true', help='show version and exit')
    return parser


def main():
    args = get_parser().parse_args()

    if args.version:
        print('web-command version ' + __version__)
        sys.exit(0)

    if args.log_level != 'none':
        logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    if args.wait_time < 0:
        print('ERROR: Wait time must be non-negative', file=sys.stderr)
        sys.exit(1)

    output = None if args.suppress_output else sys.stdout

    server = WebCommandServer(command=args.command, host=args.host, port=args.port,
                              output=output, wait_time=args.wait_time)
    server.run_forever()
