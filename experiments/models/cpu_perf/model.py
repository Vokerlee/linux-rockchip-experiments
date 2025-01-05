from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
import argparse
import copy

from matplotlib.gridspec  import GridSpec
from matplotlib.ticker    import MaxNLocator

matplotlib.rcParams['axes.formatter.limits'] = (-5, 4)

MAX_LOCATOR_NUMBER = 10
FIGURE_XSIZE = 15
FIGURE_YSIZE = 9

# BACKGROUND_RGB = '#F5F5F5'
BACKGROUND_RGB = '#FFFFFF'
MAJOR_GRID_RGB = '#919191'

LEGEND_FRAME_ALPHA = 0.95

def set_axis_properties(axes):
    axes.xaxis.set_major_locator(MaxNLocator(MAX_LOCATOR_NUMBER))
    axes.minorticks_on()
    axes.grid(which='major', linewidth=2, color=MAJOR_GRID_RGB)
    axes.grid(which='minor', linestyle=':')

def add_pmu_metrics(df):
    df['cpi'] = df['cpu_cycles'] / df['inst_retired']
    df['ipc'] = df['inst_retired'] / df['cpu_cycles']

    df['l2api']  = df['l2d_cache_rd'] / df['inst_retired']
    df['l3api']  = df['l3d_cache_rd'] / df['inst_retired']

    df['l1rpi'] = df['l1d_cache_refill'] / df['inst_retired']
    df['l2rpi']  = df['l2d_cache_refill'] / df['inst_retired']
    df['l3rpi']  = df['l3d_cache_refill'] / df['inst_retired']

    return df

def get_df_from_file(filename: str):
    df = pd.read_csv(filename)

    benchmarks = df['benchmark'].unique()
    df = add_pmu_metrics(df)

    return benchmarks, df

# def get_benchmarks_without_pmu_invariance(benchmarks, dfs, pmu_field):
#     suspicious_benchmarks = []
#     reference_value = 0

#     for i in range(len(benchmarks)):
#         benchmark = benchmarks[i]
#         pmu_values = max(dfs[benchmark][pmu_field])
#         if pmu_values > reference_value:
#             reference_value = pmu_values

#     for i in range(len(benchmarks)):
#         benchmark = benchmarks[i]
#         ddr_freqs = sorted(dfs[benchmark]['ddrfreq'].unique())
#         benchmark_df = dfs[benchmark]
#         benchmark_df = benchmark_df[benchmark_df['cluster'] == 1]
#         benchmark_df = benchmark_df[benchmark_df['ddrfreq'] == ddr_freqs[0]]

#         benchmark_pmu_values = benchmark_df[pmu_field].to_numpy()

#         if np.mean(benchmark_pmu_values) / reference_value > 0.10:
#             if np.abs(benchmark_pmu_values[-1] - benchmark_pmu_values[0]) / np.mean(benchmark_pmu_values) > 0.1:
#                 suspicious_benchmarks.append(benchmarks[i])

#     return suspicious_benchmarks

# def pmu_invariance_research(benchmarks, dfs):
#     suspicious_benchmarks = get_benchmarks_without_pmu_invariance(benchmarks, dfs, "l3rpi")
#     print(f"Benchmark which l3rpi value is not invariant for cpufreq: {suspicious_benchmarks}")

#     figure = plt.figure(figsize=(FIGURE_XSIZE, FIGURE_YSIZE), facecolor=BACKGROUND_RGB)
#     gs = GridSpec(ncols=1, nrows=1, figure=figure)
#     axes = figure.add_subplot(gs[0, 0])
#     set_axis_properties(axes)

#     # benchmark = suspicious_benchmarks[3]
#     benchmark = "random_copy_22_15"
#     benchmark_df = dfs[benchmark][dfs[benchmark]['cluster'] == 0]
#     ddr_freqs = sorted(benchmark_df['ddrfreq'].unique())
#     benchmark_df = benchmark_df[benchmark_df['ddrfreq'] == ddr_freqs[0]]

#     # x = benchmark_df['l2pi']
#     x = benchmark_df['cpufreq']
#     # y = benchmark_df['cpi']
#     y = benchmark_df['l3rpi']

#     axes.set_title(f'$l3rpi$ dependence on CPU frequency for {benchmark}')
#     # axes.plot(benchmark_df['cpufreq'], 1 / benchmark_df['l3pi'], label=f"{benchmark}", marker='o', markersize=6, linestyle='')
#     axes.plot(x, benchmark_df['l3rpi'], label=f"{benchmark}, l3rpi", marker='o', markersize=6, linestyle='')
#     axes.plot(x, benchmark_df['l2rpi'], label=f"{benchmark}, l2rpi", marker='o', markersize=6, linestyle='')
#     axes.plot(x, benchmark_df['l1rpi'], label=f"{benchmark}, l1rpi", marker='o', markersize=6, linestyle='')
#     # axes.plot(x, y, label=f"{benchmark}", marker='o', markersize=6, linestyle='')
#     # axes.set_xlim([0, 1.2 * max(x)])
#     # axes.set_ylim([0, 1.2 * max(y)])

#     figure.legend(loc="upper right", fontsize="8")
#     figure.savefig('cpi_invariance.png')

def cluster_ddrfreq_visitor(benchmarks, df, function):
    ddr_freqs = sorted(df['ddrfreq'].unique())
    clusters = sorted(df['cluster'].unique())

    artifacts = {}

    for cluster in clusters:
        cluster_artifacts = {}
        for ddr_freq in ddr_freqs:
            visit_df = df[df['cluster'] == cluster]
            visit_df = visit_df[visit_df['ddrfreq'] == ddr_freq]
            cluster_artifacts[ddr_freq] = function(benchmarks, visit_df, cluster, ddr_freq)

        artifacts[cluster] = cluster_artifacts

    return artifacts

def train_cpi_models(benchmarks, dfs):
    linear_models = []

    for i in range(len(benchmarks)):
        cpu_freq = dfs[benchmarks[i]]['cpufreq'].to_numpy()
        cpi = dfs[benchmarks[i]]['cpi'].to_numpy()

        linear_reg = LinearRegression().fit(cpu_freq.reshape(-1, 1), cpi)
        linear_models.append(linear_reg)

    return linear_models

def predict_cpi(model, cpu_freqs):
    return model.predict(cpu_freqs.reshape(-1, 1))

def train_cpi_model_cluster_ddrfreq(benchmarks, df, cluster, ddr_freq):
    dfs = dict(tuple(df.groupby('benchmark')))

    linear_models = train_cpi_models(benchmarks, dfs)
    benchmarks, linear_models = zip(*sorted(zip(benchmarks, linear_models), key=lambda x: x[1].coef_[0]))

    hsv = plt.get_cmap('hsv')
    linear_coeffs = [linear_models[i].coef_[0] for i in range(len(linear_models))]
    colors = hsv(0.8 * np.array(linear_coeffs) / np.max(linear_coeffs))

    figure = plt.figure(figsize=(FIGURE_XSIZE, FIGURE_YSIZE), facecolor=BACKGROUND_RGB)
    gs = GridSpec(ncols=1, nrows=1, figure=figure)
    axes = figure.add_subplot(gs[0, 0])
    set_axis_properties(axes)

    for i in range(len(benchmarks)):
        bencmark_name = benchmarks[i].split("/")[-1]
        cpu_freqs = dfs[benchmarks[i]]['cpufreq'].to_numpy()

        cpu_freqs_to_zero = np.linspace(0, np.min(cpu_freqs), 256)
        cpi = dfs[benchmarks[i]]['cpi'].to_numpy()
        cpi_pred = predict_cpi(linear_models[i], cpu_freqs)

        axes.plot(cpu_freqs, cpi, label=f"{bencmark_name}", color=colors[i],
                  marker='o', markersize=6, linestyle='')
        axes.plot(cpu_freqs, cpi_pred, color=colors[i],
                  marker='*', markersize=6, linestyle='-')

    axes.set_xlabel('$freq_{cpu}$, ГГц')
    axes.set_ylabel('$cpi$')
    axes.set_title(f'Dependence of CPI on $freq_{{cpu}}$ for cluster {cluster}, DDR frequency {ddr_freq} Hz')

    figure.legend(loc="upper right", fontsize="6", ncol=3)
    figure.savefig(f'cpi_model_{cluster}_{ddr_freq}.png')

    return dict(zip(benchmarks, linear_models))

def plot_kek(l3rpi_values, l3api_values, linear_coeffs, benchmarks):
    assert(len(l3rpi_values) == len(l3api_values))
    assert(len(l3rpi_values) == len(linear_coeffs))

    hsv = plt.get_cmap('hsv')
    colors = hsv(linear_coeffs / np.max(linear_coeffs))

    figure = plt.figure(figsize=(FIGURE_XSIZE, FIGURE_YSIZE), facecolor=BACKGROUND_RGB)
    axes = figure.add_subplot(projection='3d')

    # linear_reg = LinearRegression(fit_intercept=False).fit(
    #     np.swapaxes(np.array([l3rpi_values - l3api_values, l3api_values]), 0, 1), linear_coeffs)
    # print(np.array(linear_reg.coef_) * 1024 * 1024)
    # print(np.array(linear_reg.coef_))

    for i in range(len(benchmarks)):
        axes.scatter(l3rpi_values[i], l3api_values[i] - l3rpi_values[i], linear_coeffs[i], label=benchmarks[i])

    # X, Y = np.meshgrid(l3rpi_values - l3api_values, l3api_values)
    # axes.plot_wireframe(X, Y, linear_reg.coef_[0] * X + linear_reg.coef_[1] * Y)

    axes.set_ylabel("$l3api - l3rpi$", fontsize=14)
    axes.set_xlabel("$l3rpi$", fontsize=14)
    axes.set_zlabel("$lat_{gen}$", fontsize=14)

    # plt.show()
    figure.savefig('cpi_3d.png')

def train_cpi_model(benchmarks, df):
    models = cluster_ddrfreq_visitor(benchmarks, df, train_cpi_model_cluster_ddrfreq)
    ddr_freqs = sorted(df['ddrfreq'].unique())
    clusters = sorted(df['cluster'].unique())

    coeffs_models = {}
    for cluster in clusters:
        coeffs_cluster_models = {}

        for ddr_freq in ddr_freqs:
            cluster_df = df[df['cluster'] == cluster]
            cluster_df = cluster_df[cluster_df['ddrfreq'] == ddr_freq]
            model_params = models[cluster][ddr_freq]

            l3rpi_values = np.array([np.max(cluster_df[cluster_df["benchmark"] == benchmarks[i]]["l3rpi"].to_numpy()) for i in range(len(benchmarks))])
            l3api_values = np.array([np.max(cluster_df[cluster_df["benchmark"] == benchmarks[i]]["l3api"].to_numpy()) for i in range(len(benchmarks))])
            coeff_values = np.array([model_params[benchmarks[i]].coef_[0] for i in range(len(benchmarks))])

            coeffs_model = LinearRegression(fit_intercept=False).fit(
                np.swapaxes(np.array([l3rpi_values, l3api_values - l3rpi_values]), 0, 1), coeff_values)

            coeffs_cluster_models[ddr_freq] = coeffs_model.coef_

            if (cluster == 0):
                plot_kek(l3rpi_values, l3api_values, coeff_values, benchmarks)

        coeffs_models[cluster] = coeffs_cluster_models

    def print_model_params(benchmarks, df, cluster, ddr_freq):
        print(cluster, ddr_freq, coeffs_models[cluster][ddr_freq])

    cluster_ddrfreq_visitor(benchmarks, df, print_model_params)

def main(args):
    benchmarks, df = get_df_from_file(args.file)
    # pmu_invariance_research(copy.deepcopy(benchmarks), copy.deepcopy(dfs))
    train_cpi_model(copy.deepcopy(benchmarks), copy.deepcopy(df))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('file', type=argparse.FileType('r'),
                        help='csv file with PMU data of benchmarks')
    args = parser.parse_args()

    main(args)
