import sys
import os
import argparse
import time
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
        return []
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
        # check if there even is a query host and if it is already in hosts list
        if len(query) > 0 and not any(query == sublist for sublist in hosts):
            hosts.append(query)
        query = []
    if len(hosts) < 1:
        return None

    return hosts

def update_hosts(hosts, host_dict, hop_number):
    new_hosts = host_dict.get(hop_number)
    for host in hosts:
        if(hop_number == 7):
            print(new_hosts)
            print(host[1])
            print(any(host[1] == sublist[1] for sublist in new_hosts))
        # check if host already in dictionary at hop number
        if not any(host[1] == sublist[1] for sublist in new_hosts):
            if(hop_number == 7):
              print(hop_number, 'Appended.')
              print('\n')
            new_hosts.append(host)
        
    host_dict.update({hop_number : new_hosts})
    return host_dict


# Parse each line of traceroute text into a dictionary output which records
# network hop statistics including min, med, avg and max latencies for each hop
def parse_text(runs_arr):
    # 2d array to hold all latency values of each hop from each run
    hop_arr = [] 
    host_dict = {}
    for run in runs_arr:
        for hop in run:
            ms_split = hop.split(' ms')
            hop_split = hop.split()
            hop_latencies = parse_latencies(ms_split)
            hop_number = int(hop_split[0])
            hosts = parse_hosts(ms_split)
            if host_dict.get(hop_number) is not None:
                host_dict = update_hosts(hosts, host_dict, hop_number)
            else:
                host_dict.update({hop_number : hosts})
            if len(hop_arr) >= hop_number:
                hop_arr[hop_number-1] += hop_latencies
            else:
                hop_arr.append(hop_latencies)
    output_dict = []
    index = 1
    for hops in hop_arr:
        # if there is zero latency detail for a hop, disregard it and don't append to JSON
        if len(hops) > 0:
            new_dict = {}
            hops.sort()
            
            # print(hops)
            new_dict.update({'avg': round(sum(hops)/len(hops), 3)})
            new_dict.update({'hop': index})
            if host_dict.get(index) is not None:   
                new_dict.update({'hosts' : host_dict.get(index)})
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


parser = argparse.ArgumentParser()
parser.add_argument('-t', metavar='TARGET', type = str, nargs = 1, help = "A target domain name or IP address")
parser.add_argument('-n', metavar='NUM_RUNS', type = int, nargs = 1, help = "Number of times traceroute will run")
parser.add_argument('-d', metavar='RUN_DELAY', type = int, nargs = 1, help = "Number of seconds to wait between two consecutive runs")
parser.add_argument('-m', metavar='MAX_HOPS', type = int, nargs = 1, help = "Max number of hops that traceroute will probe")
parser.add_argument('-o', metavar='OUTPUT', required=True, type = str, nargs = 1, help = "Path and name (without extension) of the .json output file")
parser.add_argument('--test', metavar='TEST_DIR', type = str, nargs = 1, help = "Directory containing num_runs text files, each of which contains the output of a traceroute run. If present, this will override all other options and traceroute will not be invoked. Statistics will be computed over the traceroute output stored in the text files only")

args = parser.parse_args()

final_dictionary = []
if args.d is not None:
    if args.d[0] < 0:
        print("INPUT_ERROR: RUN_DELAY must be a positive integer.")
        exit(1)
if args.m is not None:
    if args.m[0] < 0:
        print("INPUT_ERROR: MAX_HOPS must be a positive integer.")
        exit(1)      
        
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
        outfile.write(json.dumps(runs_arr, indent=1))

else:
    num_runs = 1
    #Optional NUM_RUNS call -n
    if args.n is not None: 
        num_runs = args.n[0]
    runs_arr = []
    for i in range(num_runs):
        output_arr = []
        if args.m is not None:
            output_arr = subprocess.run(["traceroute","-m", str(args.m[0]), args.t[0]], capture_output=True, text = True).stdout.split('\n')
        else:
            output_arr = subprocess.run(["traceroute", args.t[0]], capture_output=True, text = True).stdout.split('\n')
        print(output_arr)
        # handle non data traceroute outputs
        if output_arr[0][0] == 't':
            del output_arr[0]
        if output_arr[-1] == '':
            del output_arr[-1]
        runs_arr.append(output_arr)
        # Optional DELAY call -d
        if i < num_runs - 1 and args.d is not None:
            print("sleep")
            time.sleep(int(args.d[0]))
    runs_arr = parse_text(runs_arr)
    with open(args.o[0], "w") as outfile:
        outfile.write(json.dumps(runs_arr, indent=4))
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



