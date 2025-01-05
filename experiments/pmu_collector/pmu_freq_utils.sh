#!bin/bash

get_cluster_policy_core() {
    __cluster=$1
    case $__cluster in
        0)
            echo 0
            ;;
        1)
            echo 4
            ;;
        2)
            echo 6
            ;;
        *)
            echo "Cluster is invalid"
            ;;
    esac
}

get_cluster_target_core() {
    __cluster=$1
    case $__cluster in
        0)
            echo 3
            ;;
        1)
            echo 5
            ;;
        2)
            echo 7
            ;;
        *)
            echo "Cluster is invalid"
            ;;
    esac
}

get_available_cluster_cpu_freqs() {
    local __cpu_cluster=$1
    local -n __cpu_freqs=$2
    local __cpu_freqs_path="/sys/devices/system/cpu/cpufreq/policy${__cpu_cluster}/scaling_available_frequencies"
    read -ra __cpu_freqs_cluster <<< "$(cat $__cpu_freqs_path)"
    __cpu_freqs=${__cpu_freqs_cluster[@]}
}

set_cluster_cpu_freq() {
    local __cpu_cluster=$1
    local __cpu_freq=$2
    local __cpu_max_freq_path="/sys/devices/system/cpu/cpufreq/policy${__cpu_cluster}/scaling_max_freq"
    local __cpu_min_freq_path="/sys/devices/system/cpu/cpufreq/policy${__cpu_cluster}/scaling_min_freq"

    echo "${__cpu_freq}" > $__cpu_max_freq_path
    echo "${__cpu_freq}" > $__cpu_min_freq_path
    echo "${__cpu_freq}" > $__cpu_max_freq_path
}

reset_cluster_cpu_freqs() {
    local __cpu_cluster=$1
    local __cpu_max_freq_path="/sys/devices/system/cpu/cpufreq/policy${__cpu_cluster}/scaling_max_freq"
    local __cpu_min_freq_path="/sys/devices/system/cpu/cpufreq/policy${__cpu_cluster}/scaling_min_freq"

    echo 10000000000 > $__cpu_max_freq_path
    echo 0 > $__cpu_min_freq_path
}

get_available_ddr_freqs() {
    local -n __ddr_freqs=$1
    local __ddr_freq_path="/sys/class/devfreq/dmc/available_frequencies"

    read -ra __ddr_freqs_list <<< "$(cat $__ddr_freq_path)"
    __ddr_freqs=${__ddr_freqs_list[@]}
}

set_ddr_freq() {
    local __ddr_freq=$1
    local __ddr_freq_governor_path="/sys/class/devfreq/dmc/governor"
    local __ddr_freq_set_path="/sys/class/devfreq/dmc/userspace/set_freq"
    echo "userspace" > $__ddr_freq_governor_path
    echo "${__ddr_freq}" > $__ddr_freq_set_path
}

reset_ddr_freqs() {
    local __ddr_freq_governor_path="/sys/class/devfreq/dmc/governor"
    echo "dmc_ondemand" > $__ddr_freq_governor_path
}

get_pmu_event_id() {
    __event_name=$1
    declare -A __events
    __events=(
        ["sw_incr"]="0x00"
        ["l1i_cache_refill"]="0x01"
        ["l1i_tlb_refill"]="0x02"
        ["l1d_cache_refill"]="0x03"
        ["l1d_tlb_refill"]="0x06"
        ["inst_retired"]="0x08"
        ["exc_taken"]="0x09"
        ["exc_return"]="0x0A"
        ["cid_write_retired"]="0x0B"
        ["br_mis_pred"]="0x10"
        ["cpu_cycles"]="0x11"
        ["br_pred"]="0x12"
        ["mem_access"]="0x13"
        ["l1i_cache"]="0x14"
        ["l1d_cache_wb"]="0x15"
        ["l2d_cache"]="0x16"
        ["l2d_cache_refill"]="0x17"
        ["l2d_cache_wb"]="0x18"
        ["bus_access"]="0x19"
        ["memory_error"]="0x1A"
        ["inst_spec"]="0x1B"
        ["ttbr_write_retired"]="0x1C"
        ["bus_cycles"]="0x1D"
        ["chain"]="0x1E"
        ["l2d_cache_allocate"]="0x20"
        ["br_retired"]="0x21"
        ["br_mis_pred_retired"]="0x22"
        ["stall_frontend"]="0x23"
        ["stall_backend"]="0x24"
        ["l1d_tlb"]="0x25"
        ["l1i_tlb"]="0x26"
        ["l3d_cache_allocate"]="0x29"
        ["l3d_cache_refill"]="0x2A"
        ["l3d_cache_rd"]="0x2B"
        ["l2d_tlb_refill"]="0x2D"
        ["l2d_tlb"]="0x2F"
        ["remote_access"]="0x31"
        ["dtlb_walk"]="0x34"
        ["itlb_walk"]="0x35"
        ["ll_cache_rd"]="0x36"
        ["ll_cache_miss_rd"]="0x37"
        ["l1d_cache_wr"]="0x41"
        ["l1d_cache_refill_rd"]="0x42"
        ["l1d_cache_refill_wr"]="0x43"
        ["l1d_cache_refill_inner"]="0x44"
        ["l1d_cache_refill_outer"]="0x45"
        ["l1d_cache_wb_victim"]="0x46"
        ["l1d_cache_wb_clean"]="0x47"
        ["l1d_cache_inval"]="0x48"
        ["l1d_tlb_refill_rd"]="0x4C"
        ["l1d_tlb_refill_wr"]="0x4D"
        ["l1d_tlb_rd"]="0x4E"
        ["l1d_tlb_wr"]="0x4F"
        ["l2d_cache_rd"]="0x50"
        ["l2d_cache_wr"]="0x51"
        ["l2d_cache_refill_rd"]="0x52"
        ["l2d_cache_refill_wr"]="0x53"
        ["l2d_cache_wb_victim"]="0x56"
        ["l2d_cache_wb_clean"]="0x57"
        ["l2d_cache_inval"]="0x58"
        ["l2d_tlb_refill_rd"]="0x5C"
        ["l2d_tlb_refill_wr"]="0x5D"
        ["l2d_tlb_rd"]="0x5E"
        ["l2d_tlb_wr"]="0x5F"
        ["bus_access_rd"]="0x60"
        ["bus_access_wr"]="0x61"
        ["mem_access_rd"]="0x66"
        ["mem_access_wr"]="0x67"
        ["unaligned_ld_spec"]="0x68"
        ["unaligned_st_spec"]="0x69"
        ["ldrex_spec"]="0x6C"
        ["strex_pass_spec"]="0x6D"
        ["strex_fail_spec"]="0x6E"
        ["strex_spec"]="0x6F"
        ["ld_spec"]="0x70"
        ["st_spec"]="0x71"
        ["dp_spec"]="0x73"
        ["ase_spec"]="0x74"
        ["vfp_spec"]="0x75"
        ["pc_write_spec"]="0x76"
        ["crypto_spec"]="0x77"
        ["br_immed_spec"]="0x78"
        ["br_return_spec"]="0x79"
        ["br_indirect_spec"]="0x7A"
        ["isb_spec"]="0x7C"
        ["dsb_spec"]="0x7D"
        ["dmb_spec"]="0x7E"
        ["exc_undef"]="0x81"
        ["exc_svc"]="0x82"
        ["exc_pabort"]="0x83"
        ["exc_dabort"]="0x84"
        ["exc_irq"]="0x86"
        ["exc_fiq"]="0x87"
        ["exc_smc"]="0x88"
        ["exc_hvc"]="0x8A"
        ["exc_trap_pabort"]="0x8B"
        ["exc_trap_dabort"]="0x8C"
        ["exc_trap_other"]="0x8D"
        ["exc_trap_irq"]="0x8E"
        ["exc_trap_fiq"]="0x8F"
        ["rc_ld_spec"]="0x90"
        ["rc_st_spec"]="0x91"
        ["l3d_cache_rd"]="0xA0"
    )

    echo ${__events[$__event_name]}
}

get_pmu_event_ids() {
    __event_list=$@
    read -ra __event_names <<< "${__event_list}"
    __event_ids=()

    for __event_name in "${__event_names[@]}"; do
        __event_id=$(get_pmu_event_id "$__event_name")
        __event_ids+=("$__event_id")
    done

    echo ${__event_ids[@]}
}
