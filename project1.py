import sys
import os
import argparse
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-h', '--help', help="Help text", required=False)
args = parser.parse_args()
print(f'Processing file: {args.file}')
# n = sys.argv[0]
# tr_output = os.system("traceroute ", n)