import sys
import os
import argparse

import subprocess
import json

def parse_latencies(ms_arr):
    latency = []
    for connection in ms_arr:
        split_connection = connection.split(" ")
        try: 
            latency.append(float(split_connection[-1]))
        except ValueError:
            pass
    if len(latency) < 1:
        return None
    return latency

def parse_hosts(ms_arr):
    hosts = []
    query = []
    for connection in ms_arr:
        split_connection = connection.split(" ")
        for split in split_connection:
            try: 
                # check if value is a float/int
                q = float(split)
            except ValueError:
                if split != "*" and split != '':
                    query.append(split)        
        if len(query) > 0:
            hosts.append(query)
        query = []
    if len(hosts) < 1:
        return None
    print(hosts)
    return hosts

# Parse each line of traceroute text into a dictionary output which records
# network hop statistics including min, med, avg and max latencies for each hop
def parse_text(runs_arr):
    # 2d array to hold all latency values of each hop from each run
    hop_arr = [] 
    for run in runs_arr:
        for hop in run:
            ms_split = hop.split(' ms')
            parse_hosts(ms_split)
            hop_split = hop.split()
            hop_latencies = parse_latencies(ms_split)
            hop_number = int(hop_split[0])
            if hop_latencies is not None:
                if len(hop_arr) >= hop_number:
                    hop_arr[hop_number-1] += hop_latencies
                else:
                    hop_arr.append(hop_latencies)
    output_dict = []
    index = 1
    for hops in hop_arr:
        new_dict = {}
        hops.sort()
        # print(hops)
        new_dict.update({'avg': round(sum(hops)/len(hops), 3)})
        new_dict.update({'hop': index})
        new_dict.update({'max': hops[-1]}) 
        if len(hops) % 2 == 0:
            med = round((hops[(len(hops) - 1) // 2] + hops[((len(hops) - 1) // 2) + 1]) / 2, 3)
            new_dict.update({'med': med})
        else:    
            new_dict.update({'med': hops[(len(hops) - 1) // 2]})
        new_dict.update({'min': hops[0]})
        output_dict.append(new_dict)
        index+=1
    return output_dict
    # space_split = line.split()
    # hop_dict = {'hop' : space_split[0]}
    # latency.sort()
    # return hop_dict

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
    # print("Directory called once: " + directory)
    runs_arr = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r") as file_x:
                # parse data function here
                output_arr = file_x.read().split('\n')

                # handle non data traceroute outputs
                if output_arr[0][0] == 't':
                    del output_arr[0]
                if output_arr[-1] == '':
                    del output_arr[-1]
                # print(output_arr)
                runs_arr.append(output_arr)
    runs_arr = parse_text(runs_arr)
    with open(args.o[0], "w") as outfile:
        outfile.write(json.dumps(runs_arr, indent=2))

#Optional NUM_RUNS call
else:
    num_runs = 1
    if args.n is not None: 
        num_runs = args.n[0]
    runs_arr = []
    for i in range(num_runs):
        code = subprocess.run(["traceroute", args.t[0]], capture_output=True, text = True)
        output_arr = code.stdout.split('\n')

        # handle non data traceroute outputs
        if output_arr[0][0] == 't':
            del output_arr[0]
        if output_arr[-1] == '':
            del output_arr[-1]
        runs_arr.append(output_arr)
    runs_arr = parse_text(runs_arr)
    with open(args.o[0], "w") as outfile:
        outfile.write(json.dumps(runs_arr, indent=2))
# else:
#     code = subprocess.run(["traceroute", args.t[0]], capture_output=True, text = True)
#     output_arr = code.stdout.split('\n')
#     del output_arr[0]
#     for line in output_arr:
#         parsed = parse_text(line)
#         if parsed is not None:
#             final_dictionary.append(parsed)

#     with open(args.o[0], "w") as outfile:
#         outfile.write(json.dumps(final_dictionary, indent=2))

#     print(final_dictionary)



