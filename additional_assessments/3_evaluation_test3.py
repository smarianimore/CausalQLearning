import os
import re
from itertools import product
import pandas as pd
import global_variables
import matplotlib.pyplot as plt
import json
import numpy as np
from scipy.ndimage import gaussian_filter1d
from decimal import *
from scripts.utils.others import extract_grid_size_and_n_enemies

# TODO: evaluation for the exact number of defeats
fontsize = 12
SIGMA_GAUSSIAN_FILTER = 3

dir_results = 'Test3_vecchio'
N_GAMES_PERFORMED = global_variables.N_SIMULATIONS_PAPER

n_episodes = global_variables.N_TRAINING_EPISODES

group_causality = ['env1causal', 'env2causal', 'env3causal']
group_test = ['env1test', 'env2test', 'env3test']
group_kind_algs = [
    f'{global_variables.LABEL_Q_LEARNING}_{global_variables.LABEL_CAUSAL_OFFLINE}_{global_variables.LABEL_EPSILON_GREEDY}',
    f'{global_variables.LABEL_Q_LEARNING}_{global_variables.LABEL_CAUSAL_ONLINE}_{global_variables.LABEL_EPSILON_GREEDY}']

vet_enemies = [1]
vet_grid_sizes = [(4, 4)]

combinations = list(product(group_kind_algs, group_causality, group_test))

dir_saving_plots_and_table = f'{global_variables.GLOBAL_PATH_REPO}/Plots_and_Tables/{dir_results}'
os.makedirs(dir_saving_plots_and_table, exist_ok=True)

dir_results = f'{global_variables.GLOBAL_PATH_REPO}/Results/{dir_results}'
files_inside_main_folder = os.listdir(dir_results)


def drop_characters_after_first_word(string: str, words_to_drop: list) -> str:
    for word in words_to_drop:
        if word in string:
            return string.split(word)[0]
    return string


def IQM_mean(data: list) -> Decimal:
    # Sort the data
    sorted_data = np.sort(data)

    # Calculate quartiles
    Q1 = np.percentile(sorted_data, 25)
    Q3 = np.percentile(sorted_data, 75)

    # Calculate IQR
    IQR = Q3 - Q1

    # Find indices of data within 1.5*IQR from Q1 and Q3
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    within_iqr_indices = np.where((sorted_data >= lower_bound) & (sorted_data <= upper_bound))[0]

    # Calculate IQM
    iq_mean = Decimal(np.mean(sorted_data[within_iqr_indices])).quantize(Decimal('0.01'))

    return iq_mean


def list_average(list_of_lists: list[list]) -> list:
    list_length = len(list_of_lists[0])  # Assuming all sublists have the same length
    averages = []
    for i in range(list_length):
        total = sum(sublist[i] for sublist in list_of_lists)
        averages.append(total / len(list_of_lists))
    return averages


def cumulative_list(input_list: list) -> list:
    cumulative_result = []
    cumulative_sum = 0
    for item in input_list:
        cumulative_sum += item
        cumulative_result.append(cumulative_sum)
    return cumulative_result


def compute_my_confidence_interval(data: list) -> Decimal:
    value = Decimal(np.std(data)).quantize(Decimal('.01'))
    return value


def compute_metrics(rewards: list, cumulative_rewards: list, actions: list, computation_times: list) -> dict:
    dict_out = {}
    IQM_cumulative_reward_value = cumulative_rewards[-1]
    confidence_interval_cumulative_reward_series = compute_my_confidence_interval(rewards)*len(rewards)
    dict_out[
        f'{col_average_cumulative_reward}'] = f'{IQM_cumulative_reward_value} \u00B1 {confidence_interval_cumulative_reward_series}'

    IQM_reward_value = IQM_mean(rewards)
    confidence_interval_reward_series = compute_my_confidence_interval(rewards)
    dict_out[f'{col_average_reward}'] = f'{IQM_reward_value} \u00B1 {confidence_interval_reward_series}'

    IQM_actions_needed = IQM_mean(actions)
    confidence_interval_actions_needed_series = compute_my_confidence_interval(actions)
    dict_out[
        f'{col_average_actions_needed}'] = f'{IQM_actions_needed} \u00B1 {confidence_interval_actions_needed_series}'

    IQM_computation_time = IQM_mean(computation_times)
    confidence_interval_computation_time_series = compute_my_confidence_interval(computation_times)
    dict_out[
        f'{col_average_computation_time}'] = f'{IQM_computation_time} \u00B1 {confidence_interval_computation_time_series}'

    return dict_out


def upload_fig(ax_n: plt.axes, values: list, value_to_display: str, label_series: str,
               str_timeout: str):
    # TODO: FIX COLORS
    # color_algo = global_variables.COLORS_ALGORITHMS[label_series]
    series_smooth = gaussian_filter1d(values, SIGMA_GAUSSIAN_FILTER)
    x_data = np.arange(0, len(series_smooth), 1)
    if str_timeout is not None:
        ax_n.plot(x_data, series_smooth,  # color=color_algo,
                  label=f'{label_series}: {value_to_display} ({str_timeout})')
    else:
        ax_n.plot(x_data, series_smooth,  # color=color_algo,
                  label=f'{label_series}: {value_to_display}')

    mean_str, std_str = value_to_display.split(' ± ')
    confidence_interval = float(std_str)
    ax_n.fill_between(x_data, (series_smooth - confidence_interval), (series_smooth + confidence_interval),
                      # color=color_algo,
                      alpha=0.2)

    ax_n.legend(fontsize='small')


col_average_reward = 'IQM_average_reward'
col_average_cumulative_reward = 'IQM_average_cumulative_reward'
col_average_actions_needed = 'IQM_average_actions_needed'
col_average_computation_time = 'IQM_average_computation_time'
columns_table_results = ['grid_size', 'n_enemies', 'algo', f'{col_average_reward}', f'{col_average_cumulative_reward}',
                         f'{col_average_actions_needed}', f'{col_average_computation_time}']

table_results = pd.DataFrame(columns=columns_table_results)

name_rewards_series = 'rewards'
name_actions_series = 'actions'
name_computation_time_series = 'computation_time'
name_timeout_series = 'timeout'

for file_main_folder in files_inside_main_folder:

    save_plot = f'{dir_saving_plots_and_table}/{file_main_folder}'

    file_main_folder = f'{dir_results}/{file_main_folder}'
    files_inside_second_folder = os.listdir(file_main_folder)

    dict_values = {f'{comb[0]}_{comb[1]}_{comb[2]}': {f'{name_rewards_series}': [],
                                                      f'{name_actions_series}': [],
                                                      f'{name_computation_time_series}': [],
                                                      f'{name_timeout_series}': []} for comb in combinations}

    grid_size, n_enemies = extract_grid_size_and_n_enemies(os.path.basename(file_main_folder))
    figures_subtitle = f'{os.path.basename(file_main_folder).replace("_", " ")} - Averaged over {N_GAMES_PERFORMED} games'

    # for make order
    for algorithm in dict_values.keys():
        with open(f'{file_main_folder}/{algorithm}.json', 'r') as file:
            series = json.load(file)

        dict_values[algorithm][f'{name_rewards_series}'].append(series[global_variables.KEY_METRIC_REWARDS_EPISODE])
        dict_values[algorithm][f'{name_actions_series}'].append(series[global_variables.KEY_METRICS_STEPS_EPISODE])
        dict_values[algorithm][f'{name_computation_time_series}'].append(
            series[global_variables.KEY_METRIC_TIME_EPISODE])
        dict_values[algorithm][f'{name_timeout_series}'].append(
            series[global_variables.KEY_METRIC_TIMEOUT_CONDITION])

    # for table
    for algorithm, series in dict_values.items():
        if series[f'{name_rewards_series}']:
            rewards_series = list_average(series[f'{name_rewards_series}'])
            cumulative_rewards_series = cumulative_list(rewards_series)
            actions_series = list_average(series[f'{name_actions_series}'])
            computation_time_series = list_average(series[f'{name_computation_time_series}'])

            dict_metrics = compute_metrics(rewards_series, cumulative_rewards_series, actions_series,
                                           computation_time_series)

            cumulative_rewards_value_to_save = dict_metrics[f'{col_average_cumulative_reward}']
            actions_value_to_save = dict_metrics[f'{col_average_actions_needed}']
            reward_value_to_save = dict_metrics[f'{col_average_reward}']
            computation_time_value_to_save = dict_metrics[f'{col_average_computation_time}']

            new_row_dict = {'grid_size': f'{grid_size[0]}x{grid_size[1]}', 'n_enemies': n_enemies, 'algo': algorithm,
                            f'{col_average_reward}': reward_value_to_save,
                            f'{col_average_cumulative_reward}': cumulative_rewards_value_to_save,
                            f'{col_average_actions_needed}': actions_value_to_save,
                            f'{col_average_computation_time}': computation_time_value_to_save}

            new_row_df = pd.DataFrame([new_row_dict])
            table_results = pd.concat([table_results, new_row_df], ignore_index=True)

    # for plots and tables
    os.makedirs(save_plot, exist_ok=True)
    for item_chosen in group_test:
        print(item_chosen)
        algos_chosen_from_dict = {key: value for key, value in dict_values.items() if item_chosen in key}

        fig_reward, ax_iqm_reward = plt.subplots(dpi=1000)
        ax_iqm_reward.set_title(f'Average reward {item_chosen}')
        fig_reward.suptitle(f'{figures_subtitle}', fontsize=fontsize + 3)

        fig_cum_reward, ax_cum_reward = plt.subplots(dpi=1000)
        ax_cum_reward.set_title(f'Cumulative reward {item_chosen}')
        fig_cum_reward.suptitle(f'{figures_subtitle}', fontsize=fontsize + 3)

        fig_actions, ax_actions = plt.subplots(dpi=1000)
        ax_actions.set_title(f'Actions needed {item_chosen}')
        fig_actions.suptitle(f'{figures_subtitle}', fontsize=fontsize + 3)

        """fig_time, ax_time = plt.subplots(dpi=1000)
        ax_time.set_title(f'Computation time {item_chosen}')
        fig_time.suptitle(f'{figures_subtitle}', fontsize=fontsize + 3)"""

        for algorithm, series in algos_chosen_from_dict.items():
            if series[f'{name_rewards_series}']:

                # label_plot, for_title = re.split(r'(?<=EG)', algorithm, maxsplit=1)
                label_plot = algorithm.replace(f'{item_chosen}', '')

                n_games_performed = len(series[f'{name_timeout_series}'])
                n_games_ok = series[f'{name_timeout_series}'].count(False)

                if n_games_ok < n_games_performed:
                    str_timeout = f'{n_games_ok}/{n_games_performed}'
                elif n_games_ok == n_games_performed:
                    str_timeout = None
                else:
                    print(
                        f'*** Problem with timeout counter: n_games_performed: {n_games_performed} - n_games_ok: {n_games_ok}')
                    str_timeout = None

                indices_to_remove = [i for i, value in enumerate(series[f'{name_timeout_series}']) if value]
                for key in series:
                    if key != f'{name_timeout_series}':
                        series[key] = [sublist for i, sublist in enumerate(series[key]) if
                                       i not in indices_to_remove]

                rewards_series = list_average(series[f'{name_rewards_series}'])
                cumulative_rewards_series = cumulative_list(rewards_series)
                actions_series = list_average(series[f'{name_actions_series}'])
                computation_time_series = list_average(series[f'{name_computation_time_series}'])

                dict_metrics = compute_metrics(rewards_series, cumulative_rewards_series, actions_series,
                                               computation_time_series)

                cumulative_rewards_value_to_save = dict_metrics[f'{col_average_cumulative_reward}']
                actions_value_to_save = dict_metrics[f'{col_average_actions_needed}']
                reward_value_to_save = dict_metrics[f'{col_average_reward}']
                computation_time_value_to_save = dict_metrics[f'{col_average_computation_time}']

                upload_fig(ax_iqm_reward, rewards_series, reward_value_to_save, label_plot, str_timeout)
                upload_fig(ax_cum_reward, cumulative_rewards_series, cumulative_rewards_value_to_save, label_plot,
                           str_timeout)
                upload_fig(ax_actions, actions_series, actions_value_to_save, label_plot, str_timeout)
                # upload_fig(ax_time, computation_time_series, computation_time_value_to_save, label_plot, str_timeout)

        # fig_time.savefig(f'{save_plot}/time_{item_chosen}.png')
        fig_actions.savefig(f'{save_plot}/actions_{item_chosen}.png')
        fig_cum_reward.savefig(f'{save_plot}/cum_reward_{item_chosen}.png')
        fig_reward.savefig(f'{save_plot}/reward_{item_chosen}.png')

        plt.show()
        # plt.close(fig_time)
        plt.close(fig_actions)
        plt.close(fig_cum_reward)
        plt.close(fig_reward)

table_results.to_excel(f'{dir_saving_plots_and_table}/results.xlsx')
table_results.to_pickle(f'{dir_saving_plots_and_table}/results.pkl')