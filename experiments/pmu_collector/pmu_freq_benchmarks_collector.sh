#!bin/bash

path_to_benchmarks=$1
data_filename=$2

benchmarks_to_launch=$(ls -1 $path_to_benchmarks)
read -ra benchmarks_list <<< $(echo $benchmarks_to_launch)

timestamp="$(date +"%Y-%m-%d-%H.%M.%S")"
results_dir="launch-$timestamp"
mkdir -p $results_dir

for benchmark in "${benchmarks_list[@]}"
do
    touch "$results_dir/$benchmark.csv"
    bash pmu_freq_collector.sh $path_to_benchmarks/$benchmark > "$results_dir/$benchmark.csv"
done

python3 combine_csv.py "$results_dir/$benchmark.csv" $data_filename
