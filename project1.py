import sys
import os
import argparse

import subprocess
import json
# Parse each line of traceroute text into a dictionary output which records
# network hop statistics including min, med, avg and max latencies for each hop
def parse_text(line):
    ms_split = line.split(' ms')
    latency = []
    for connection in ms_split:
        split_connection = connection.split(" ")
        try: 
            latency.append(float(split_connection[-1]))
        except ValueError:
            pass
    if len(latency) < 1:
        return None
    space_split = line.split()
    hop_dict = {'hop' : space_split[0]}
    # latency.sort()
    return hop_dict

parser = argparse.ArgumentParser()
parser.add_argument('-t', metavar='TARGET', type = str, nargs = 1, help = "A target domain name or IP address")
parser.add_argument('-n', metavar='NUM_RUNS', type = int, nargs = 1, help = "Number of times traceroute will run")
parser.add_argument('-d', metavar='RUN_DELAY', type = int, nargs = 1, help = "Number of seconds to wait between two consecutive runs")
parser.add_argument('-m', metavar='MAX_HOPS', type = int, nargs = 1, help = "Max number of hops that traceroute will probe")
parser.add_argument('-o', metavar='OUTPUT', required=True, type = str, nargs = 1, help = "Path and name (without extension) of the .json output file")
parser.add_argument('--test', metavar='TEST_DIR', type = str, nargs = 1, help = "Directory containing num_runs text files, each of which contains the output of a traceroute run. If present, this will override all other options and traceroute will not be invoked. Statistics will be computed over the traceroute output stored in the text files only")

args = parser.parse_args()

final_dictionary = []

# If --test called, rip text files from directory
if args.test is not None:
    directory = args.test[0]
    if args.n is None:
        print("Directory called once: " + directory)
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r") as file_x:
                    #parse data function here
                    print(file_x.read())
    else:
        for i in range(args.n[0]):
            print("Directory called: " + args.test[0])

#Optional NUM_RUNS call
elif args.n is not None:
    for i in range(args.n[0]):
        code = subprocess.run(["traceroute", args.t[0]], capture_output=True, text = True)
        print(code.stdout)
else:
    code = subprocess.run(["traceroute", args.t[0]], capture_output=True, text = True)
    output_arr = code.stdout.split('\n')
    del output_arr[0]
    for line in output_arr:
        parsed = parse_text(line)
        if parsed is not None:
            final_dictionary.append(parsed)
    print(final_dictionary)



