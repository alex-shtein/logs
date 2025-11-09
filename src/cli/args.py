import argparse


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="log-analyzer", description="Анализатор NGINX логов"
    )
    p.add_argument("-p", "--path", required=True, type=str)
    p.add_argument("-o", "--output", required=True, type=str)
    p.add_argument("-f", "--format", dest="out_format", required=True, type=str)
    p.add_argument("--from", dest="date_from", default=None, type=str)
    p.add_argument("--to", dest="date_to", default=None, type=str)
    return p.parse_args(argv)
