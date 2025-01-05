#!bin/bash

source pmu_freq_utils.sh

############################################################
# Script settings

program_to_launch=$1
pmu_perf_program="./build/pmu_collector"

pmu_events_list="
    inst_retired
    cpu_cycles
    l1d_cache_refill
    l2d_cache_rd
    l2d_cache_refill
    l3d_cache_rd
    l3d_cache_refill
"

# CLuster 2 is the copy of cluster 1
# active_clusters="0 1"
active_clusters="0 1"
benchnmark_timeout=6

############################################################
# Auxiliary variables/functions

pmu_events_id_list=$(get_pmu_event_ids ${pmu_events_list})
num_events=$(echo ${pmu_events_list} | awk '{print NF}')

read -ra clusters_list <<< "$active_clusters"
num_clusters=${#clusters_list[@]}

print_csv_data_header() {
    __pmu_events_list=$@
    echo "benchmark,cluster,ddrfreq,cpufreq,${__pmu_events_list// /,},time_run,time_enabled"
}

timeout_benchmark() {
    __delay=$1
    __pid_to_kill=$2

    sleep $__delay
    kill -s SIGUSR1 $__pid_to_kill
    wait $__pid_to_kill &> /dev/null
}

launch_benchmark() {
    __cmd_launch=$@

    __pmu_values_file=$(mktemp)
    ${__cmd_launch} > ${__pmu_values_file} &
    __pid=$!

    timeout_benchmark $benchnmark_timeout $__pid
    echo $(cat $__pmu_values_file)
}

############################################################
# Core phase

print_csv_data_header $pmu_events_list

for ((i=0; i<num_clusters; i++)); do
    get_available_ddr_freqs ddr_freqs_list

    for ddr_freq in $ddr_freqs_list
    do
        set_ddr_freq $ddr_freq

        cluster=${clusters_list[i]}
        cluster_policy_core=$(get_cluster_policy_core $cluster)
        cluster_target_core=$(get_cluster_target_core $cluster)

        get_available_cluster_cpu_freqs $cluster_policy_core cpu_freqs_list
        for cpu_freq in $cpu_freqs_list
        do
            set_cluster_cpu_freq $cluster_policy_core $cpu_freq

            cmd_launch="$pmu_perf_program -e ${pmu_events_id_list// /,} -a $cluster_target_core -c $@"
            pmu_events_values=$(launch_benchmark $cmd_launch)

            echo "$(basename ${program_to_launch}),$i,$ddr_freq,$cpu_freq,$pmu_events_values"
        done

        reset_cluster_cpu_freqs $cluster_policy_core
    done

    reset_ddr_freqs
done
