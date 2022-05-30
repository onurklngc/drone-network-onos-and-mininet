import numpy as np
from matplotlib import pyplot as plt

from chart.constant import cb_color_cycle
from chart.utils import get_multiple_files, get_specific_tasks, \
    get_average_system_times, ORDERING, REQUEST_INTERVAL_FILE_LIST

plt.rcParams["font.size"] = "34.5"
tags = ["5 s", "10 s", "15 s"]


# tags = ["5 km/h", "20km/h", "40km/h"]
# tags = ["Slow", "Medium", "Fast"]


def sub_plot(ax, penalty_data_list, method_name, plot_index, case_ordering):
    delay_data = {}
    total_delays = []
    pool = []
    tx_time = []
    queue_time = []
    process_time = []

    method_data = penalty_data_list[method_name]
    for case in case_ordering:
        tasks = get_specific_tasks(penalty_data_list, method_name, case)
        # prioritized_penalties = get_prioritized_penalties(tasks)
        delay_averages = get_average_system_times(tasks)
        delay_data[case] = delay_averages
        total_delays.append(delay_averages['average_delay'])
        pool.append(delay_averages['average_pool_time'])
        tx_time.append(delay_averages['average_tx_time'])
        queue_time.append(delay_averages['average_queue_time'])
        process_time.append(delay_averages['average_process_time'])
    width = 0.2  # the width of the bars: can also be len(x) sequence

    tx_time = np.array(tx_time)
    process_time = np.array(process_time)
    pool = np.array(pool)
    queue_time = np.array(queue_time)
    sub_x = plot_index + np.array([-0.2, 0, 0.2])
    ax.bar(sub_x, tx_time, width, label=r'$\overline{t}_{tx}$', color=cb_color_cycle[0], hatch='\\')
    ax.bar(sub_x, process_time, width, bottom=tx_time, label=r'$\overline{t}_{process}$',
           color=cb_color_cycle[1], hatch='o')
    ax.bar(sub_x, pool, width, bottom=process_time + tx_time, label=r'$\overline{t}_{pool}$',
           color=cb_color_cycle[2], hatch='/')
    ax.bar(sub_x, queue_time, width, bottom=process_time + tx_time + pool,
           label=r'$\overline{t}_{queue}$', color=cb_color_cycle[3])
    for i in range(3):
        ax.text(sub_x[i], total_delays[i], tags[i], ha="center", va="bottom", size=26.5)
    ax.set_ylabel('Average Delay (s)', size=50)
    print(method_name)


def plot(penalty_data_list, case_ordering):
    fig, ax = plt.subplots()
    sub_plot(ax, penalty_data_list, "Only-Cloud", 0, case_ordering)
    sub_plot(ax, penalty_data_list, "Aggressive-Wait", 1, case_ordering)
    sub_plot(ax, penalty_data_list, "Aggressive", 2, case_ordering)
    sub_plot(ax, penalty_data_list, "Adaptive", 3, case_ordering)
    sub_plot(ax, penalty_data_list, "Optimum", 4, case_ordering)

    plt.legend(
        [r'$\overline{t}_{tx}$', r'$\overline{t}_{process}$', r'$\overline{t}_{pool}$', r'$\overline{t}_{queue}$'])
    main_x = np.arange(5)
    plt.xticks(main_x, ['Only-Cloud', 'AGG-1', 'AGG-2', 'ADP', 'Q-OPT'])
    plt.show()


if __name__ == '__main__':
    result_data = get_multiple_files(REQUEST_INTERVAL_FILE_LIST)
    plot(result_data, ORDERING["request_interval"])
    # result_data = get_multiple_files(VEHICLE_SPEED_FILE_LIST)
    # plot(result_data, ORDERING["vehicle_speed"])
    # result_data = get_multiple_files(PROCESS_SPEED_FILE_LIST)
    # plot(result_data, ORDERING["process_speed"])
