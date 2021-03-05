import matplotlib.pyplot as plt
import numpy as np
import pickle

file_name = "situation-156760280.pkl"

bar_width = 0.35
time_stops = [16, 17, 18, 19]

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "26"

time_stop_ids = np.arange(len(time_stops))
number_of_active_drones = []
requests_from_depleted_drones = []
number_of_requests_connection_is_missing = []
file_request_number_except_depleted_drones = []
satisfied_requests = []
satisfaction_ratio_all = []
satisfaction_ratio_all_from_own_cache = []
satisfaction_ratio_all_h2h = []
satisfaction_ratio_all_from_switch = []
satisfaction_ratio_all_from_content_server = []
satisfaction_ratio_actives = []
satisfaction_ratio_actives_from_own_cache = []
satisfaction_ratio_actives_h2h = []
satisfaction_ratio_actives_from_switch = []
satisfaction_ratio_actives_from_content_server = []
obtained_from_own_cache = []
obtained_h2h = []
obtained_from_switch = []
obtained_from_content_server = []
results = {}
with open(file_name, 'rb') as fp:
    results = pickle.load(fp)

number_of_drones = results["settings"]["NUMBER_OF_SWITCHES"]


def combine_values_from_time_stops():
    for currentTime in time_stops:
        time_in_sec = 60 * currentTime
        number_of_depleted_drones = len(results[time_in_sec]['depleted_battery_ids'])
        number_of_active_drones.append(number_of_drones - number_of_depleted_drones)
        requests_from_depleted_drones.append(results[time_in_sec]['requests_from_depleted_drones'])
        current_number_of_requests_connection_is_missing = results[time_in_sec]['mediaServerLogs'][
            'number_of_requests_connection_is_missing']

        obtained_from_own_cache.append(results[time_in_sec]['mediaServerLogs']['cache_found_at_requester'])
        obtained_h2h.append(results[time_in_sec]['mediaServerLogs']['cacheTakenFromHost'])
        obtained_from_switch.append(results[time_in_sec]['mediaServerLogs']['cacheTakenFromSwitch'])
        obtained_from_content_server.append(results[time_in_sec]['mediaServerLogs']['media_server_selected_as_source'])

        number_of_requests_connection_is_missing.append(current_number_of_requests_connection_is_missing)
        current_file_request_number_except_depleted_drones = results[time_in_sec]['mediaServerLogs'][
            'file_request_number']
        file_request_number_except_depleted_drones.append(current_file_request_number_except_depleted_drones)
        satisfied_requests.append(
            current_file_request_number_except_depleted_drones - current_number_of_requests_connection_is_missing)


def calculate_ratios():
    for stopID in time_stop_ids:
        satisfaction_ratio_all.append(
            100 * float(satisfied_requests[stopID]) / (file_request_number_except_depleted_drones[stopID] +
                                                       requests_from_depleted_drones[stopID]))
        satisfaction_ratio_all_from_own_cache.append(
            100 * float(obtained_from_own_cache[stopID]) / (file_request_number_except_depleted_drones[stopID] +
                                                            requests_from_depleted_drones[stopID]))
        satisfaction_ratio_all_h2h.append(
            100 * float(obtained_h2h[stopID]) / (file_request_number_except_depleted_drones[stopID] +
                                                 requests_from_depleted_drones[stopID]))
        satisfaction_ratio_all_from_switch.append(
            100 * float(obtained_from_switch[stopID]) / (file_request_number_except_depleted_drones[stopID] +
                                                         requests_from_depleted_drones[stopID]))
        satisfaction_ratio_all_from_content_server.append(
            100 * float(obtained_from_content_server[stopID]) / (file_request_number_except_depleted_drones[stopID] +
                                                                 requests_from_depleted_drones[stopID]))

        satisfaction_ratio_actives.append(
            100 * float(satisfied_requests[stopID]) / file_request_number_except_depleted_drones[stopID])
        satisfaction_ratio_actives_from_own_cache.append(
            100 * float(obtained_from_own_cache[stopID]) / file_request_number_except_depleted_drones[stopID])
        satisfaction_ratio_actives_h2h.append(
            100 * float(obtained_h2h[stopID]) / file_request_number_except_depleted_drones[stopID])
        satisfaction_ratio_actives_from_switch.append(
            100 * float(obtained_from_switch[stopID]) / file_request_number_except_depleted_drones[stopID])
        satisfaction_ratio_actives_from_content_server.append(
            100 * float(obtained_from_content_server[stopID]) / file_request_number_except_depleted_drones[stopID])


# def autolabel(ax, rects):
#     """
#     Attach a text label above each bar displaying its height
#     """
#     for rect in rects:
#         height = rect.get_height()
#         ax.text(rect.get_x() + rect.get_width() / 2., 10,
#                 '%d %%' % int(height),
#                 ha='center', va='bottom',color='white')
def auto_label(current_ax, rects):
    for rect in rects:
        height = rect.get_height()
        y_val = rect.get_y() + rect.get_height() - rect.get_height() / 2

        current_ax.text(rect.get_x() + rect.get_width() / 2., y_val,
                        '%.1f%%' % round(rect.get_height(), 1),
                        ha='center', va='bottom', color='white', fontsize=29, fontweight="bold")


def auto_text_label(current_ax, rects, text_string):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        current_ax.text(rect.get_x() + rect.get_width() / 2., 2,
                        text_string,
                        ha='center', va='bottom', color='white', fontsize=26, fontweight="bold")


if __name__ == '__main__':
    with open(file_name, 'rb') as handle:
        results = pickle.load(handle)
    combine_values_from_time_stops()
    calculate_ratios()

    fig, ax = plt.subplots()
    # Create green Bars
    # barSatisfactionRatioAll = plt.bar(time_stop_ids, satisfaction_ratio_all, color='#f9bc86', edgecolor='white',width=bar_width,label="Satisfaction ratio of all UAVs")
    bar_satisfaction_ratio_all_from_content_server = plt.bar(time_stop_ids, satisfaction_ratio_all_from_content_server,
                                                             color='blue',
                                                             edgecolor='black', width=bar_width, label="Content server")
    bar_satisfaction_ratio_all_from_switch = plt.bar(time_stop_ids, satisfaction_ratio_all_from_switch,
                                                     bottom=satisfaction_ratio_all_from_content_server, color='green',
                                                     edgecolor='black', width=bar_width, label="UAV cache")
    bar_satisfaction_ratio_all_from_own_cache = plt.bar(time_stop_ids, satisfaction_ratio_all_from_own_cache,
                                                        bottom=np.array(
                                                            satisfaction_ratio_all_from_content_server) + np.array(
                                                            satisfaction_ratio_all_from_switch), color='purple',
                                                        edgecolor='black', width=bar_width, label="Other host cache")
    bar_satisfaction_ratio_all_h2h = plt.bar(time_stop_ids, satisfaction_ratio_all_h2h,
                                             bottom=np.array(satisfaction_ratio_all_from_content_server) + np.array(
                                                 satisfaction_ratio_all_from_switch) + np.array(
                                                 satisfaction_ratio_all_from_own_cache), color='red', edgecolor='black',
                                             width=bar_width, label="Local hit")
    # bar_satisfaction_ratio_actives = plt.bar(time_stop_ids + bar_width, satisfaction_ratio_actives, color='#b5ffb9', edgecolor='white', width=bar_width,label="Satisfaction ratio of the active UAVs")
    bar_satisfaction_ratio_actives = plt.bar(time_stop_ids + bar_width, satisfaction_ratio_actives, color='#b5ffb9',
                                             edgecolor='white', width=bar_width)
    bar_satisfaction_ratio_actives_from_content_server = plt.bar(time_stop_ids + bar_width,
                                                                 satisfaction_ratio_actives_from_content_server,
                                                                 color='blue',
                                                                 edgecolor='black', width=bar_width)
    bar_satisfaction_ratio_actives_from_switch = plt.bar(time_stop_ids + bar_width,
                                                         satisfaction_ratio_actives_from_switch,
                                                         bottom=satisfaction_ratio_actives_from_content_server,
                                                         color='green',
                                                         edgecolor='black', width=bar_width)
    bar_satisfaction_ratio_actives_from_own_cache = plt.bar(time_stop_ids + bar_width,
                                                            satisfaction_ratio_actives_from_own_cache,
                                                            bottom=np.array(
                                                                satisfaction_ratio_actives_from_content_server) + np.array(
                                                                satisfaction_ratio_actives_from_switch), color='purple',
                                                            edgecolor='black', width=bar_width)
    bar_satisfaction_ratio_actives_h2h = plt.bar(time_stop_ids + bar_width, satisfaction_ratio_actives_h2h,
                                                 bottom=np.array(
                                                     satisfaction_ratio_actives_from_content_server) + np.array(
                                                     satisfaction_ratio_actives_from_switch) + np.array(
                                                     satisfaction_ratio_actives_from_own_cache), color='red',
                                                 edgecolor='black',
                                                 width=bar_width)

    auto_label(ax, bar_satisfaction_ratio_all_from_content_server)
    auto_label(ax, bar_satisfaction_ratio_all_from_switch)
    auto_label(ax, bar_satisfaction_ratio_all_from_own_cache)
    auto_label(ax, bar_satisfaction_ratio_all_h2h)
    auto_label(ax, bar_satisfaction_ratio_actives_from_content_server)
    auto_label(ax, bar_satisfaction_ratio_actives_from_switch)
    auto_label(ax, bar_satisfaction_ratio_actives_from_own_cache)
    auto_label(ax, bar_satisfaction_ratio_actives_h2h)

    auto_text_label(ax, bar_satisfaction_ratio_all_from_content_server, 'All')
    auto_text_label(ax, bar_satisfaction_ratio_actives_from_content_server, 'Active')
    fig.subplots_adjust(bottom=0.1, top=0.88, left=0.05, right=0.9,
                        wspace=0.02, hspace=0.02)
    x_labels = []
    for index, timeStop in enumerate(time_stops):
        label = "t={} min\n # of working UAVs={}".format(timeStop, number_of_active_drones[index])
        x_labels.append(label)
    plt.xticks(time_stop_ids + bar_width / 2, x_labels)
    ax.legend(loc="upper right", bbox_to_anchor=(1.01, 1.175), ncol=2)
    # plt.suptitle('Request Satisfaction Statistics')

    plt.show()
