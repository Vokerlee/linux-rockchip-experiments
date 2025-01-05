#include "pmu_events.hpp"

#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sched.h>
#include <cstdlib>
#include <functional>
#include <cerrno>
#include <iostream>
#include <sstream>
#include <vector>

// Amount of time when PMU is not collected due to benchmark is not
// stabilized yet
static constexpr size_t N_USEC_TO_WAIT = 1000000;

struct BenchmarkArgs {
    std::vector<uint32_t> affinity_cores;
    std::vector<uint32_t> pmu_values;
    std::vector<std::string> cmd_argv;
};

PMU::Events EVENTS_COLLECTOR;
int PID_BENCHMARK = -1;

template <typename T>
std::vector<T> split_string(const std::string& s, char delimiter, std::function<T(const std::string&)> converter)
{
    std::vector<T> split_values;
    std::stringstream ss(s);
    std::string item;

    while (std::getline(ss, item, delimiter))
        split_values.push_back(converter(item));

    return split_values;
}

bool set_affinity(pid_t pid, const std::vector<uint32_t>& affinity_cores);
BenchmarkArgs handle_arguments(int argc, char *argv[]);
void finish_collecting([[maybe_unused]] int unused);

int main(int argc, char *argv[])
{
    BenchmarkArgs args = handle_arguments(argc, argv);

    std::vector<PMU::EventDescriptor> events;
    for (size_t i = 0; i < args.pmu_values.size(); ++i)
        events.push_back({.type = PERF_TYPE_RAW, .perf_id = args.pmu_values[i]});

    signal(SIGUSR1, finish_collecting);

    std::vector<char*> benchmark_argv(args.cmd_argv.size() + 1, nullptr);
    std::transform(args.cmd_argv.begin(), args.cmd_argv.end(), benchmark_argv.begin(),
        [](std::string& arg) {
            return arg.data();
        }
    );

    PID_BENCHMARK = fork();
    if (PID_BENCHMARK < 0) {
        std::cerr << "fork() returned -1: " << strerror(errno) << std::endl;
        exit(EXIT_FAILURE);
    } else if (PID_BENCHMARK == 0) {
        set_affinity(getpid(), args.affinity_cores);
        if (execvp(benchmark_argv[0], &(benchmark_argv[0])) == -1) {
            std::cerr << "execvp() returned -1: " << strerror(errno) << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    usleep(N_USEC_TO_WAIT);
    EVENTS_COLLECTOR.add_events(PID_BENCHMARK, events);
    EVENTS_COLLECTOR.enable_collection();

    int status = 0;
    int benchmark_pid = waitpid(PID_BENCHMARK, &status, 0);
    if (benchmark_pid == -1) {
        std::cerr << "waitpid() returned -1: " << strerror(errno) << std::endl;
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}

bool set_affinity(pid_t pid, const std::vector<uint32_t>& affinity_cores)
{
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);

    for (const auto& core : affinity_cores)
        CPU_SET(core, &cpuset);

    if (sched_setaffinity(pid, sizeof(cpuset), &cpuset) == -1) {
        std::cerr << "sched_setaffinity() returned -1: " << strerror(errno) << std::endl;
        return false;
    }

    return true;
}

BenchmarkArgs handle_arguments(int argc, char *argv[])
{
    BenchmarkArgs args;
    int option = 0;

    while ((option = getopt(argc, argv, "a:e:c:")) != -1) {
        switch (option) {
            case 'a': {
                args.affinity_cores = split_string<uint32_t>(optarg, ',',
                    [](const std::string& str) {
                        return std::strtol(str.data(), nullptr, 10);
                    });
                break;
            }
            case 'e': {
                args.pmu_values = split_string<uint32_t>(optarg, ',',
                    [](const std::string& str) {
                        return std::strtol(str.data(), nullptr, 16);
                    });
                break;
            }
            case 'c': {
                args.cmd_argv = split_string<std::string>(optarg, ' ',
                    [](const std::string& str) {
                        return str;
                    });
                break;
            }
            case '?': {
                if (optopt == 'a' || optopt == 'e' || optopt == 'c')
                    std::cerr << "Option -" << static_cast<char>(optopt) << " requires an argument" << std::endl;
                else
                    std::cerr << "Unknown option: " << static_cast<char>(optopt) << std::endl;
                exit(EXIT_FAILURE);
            }
            default:
                exit(EXIT_FAILURE);
        }
    }

    return args;
}

void finish_collecting([[maybe_unused]] int unused)
{
    std::vector<float> final_pmu_values = EVENTS_COLLECTOR.read_events();
    EVENTS_COLLECTOR.disable_collection(true);
    EVENTS_COLLECTOR.clear_events();

    if (PID_BENCHMARK != -1)
        kill(PID_BENCHMARK, SIGUSR1);

    for (size_t i = 0; i < final_pmu_values.size() - 1; ++i) {
        std::cout << final_pmu_values[i] << ",";
    }

    std::cout << final_pmu_values[final_pmu_values.size() - 1] << std::endl;
}
