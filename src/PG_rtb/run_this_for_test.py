from src.PG_rtb.env import AD_env
from src.PG_rtb.RL_brain_for_test import PolicyGradientForTest
import numpy as np
import pandas as pd
import copy
import datetime
from src.config import config
import matplotlib.pyplot as plt

def test_env(budget, auc_num, budget_para):
    env.build_env(budget, auc_num) # 参数为测试集的(预算， 总展示次数)
    state = env.reset(budget, auc_num) # 参数为测试集的(预算， 总展示次数)

    test_data = pd.read_csv("../../data/fm/test_fm.csv", header=None)
    test_data.iloc[:, config['data_hour_index']] = test_data.iloc[:, config['data_hour_index']].astype(int)
    test_ctr = pd.read_csv("../../data/fm/test_ctr_pred.csv", header=None).drop(0, axis=0)  # 读取测试数据集中每条数据的pctr
    test_ctr.iloc[:, 1] = test_ctr.iloc[:, 1].astype(float)
    test_ctr = test_ctr.iloc[:, 1].values
    embedding_v = pd.read_csv("../../data/fm/embedding_v.csv", header=None)
    test_avg_ctr = pd.read_csv("../../transform_precess/test_avg_ctrs.csv", header=None).iloc[:,1].values  # 测试集中每个时段的平均点击率

    test_total_clks = np.sum(test_data.iloc[:, config['data_clk_index']])
    result_array = []  # 用于记录每一轮的最终奖励，以及赢标（展示的次数）
    hour_clks = [0 for i in range(0, 24)]
    real_hour_clks = [0 for i in range(0, 24)]

    total_reward_clks = 0
    total_reward_profits = 0
    total_imps = 0
    real_clks = 0
    bid_nums = 0 # 出价次数
    real_imps = 0 # 真实曝光数

    current_with_clk_aucs = 0  # 当前时刻有点击的曝光数量
    current_no_clk_aucs = 0  # 当前时刻没有点击的曝光数量
    current_clk_no_win_aucs = 0  # 当前时刻有点击没赢标的曝光数量
    current_no_clk_no_win_aucs = 0  # 当前时刻没有点击且没赢标的曝光数量
    current_no_clk_win_aucs = 0
    # current_no_clk_budget = 0  # 当前时刻所有的没有点击的预算
    # current_no_clk_win_spent = 0  # 当前时刻没有点击却赢标了的曝光花费

    ctr_action_records = []  # 记录模型出价以及真实出价，以及ctr（在有点击数的基础上）
    for i in range(len(test_data)):

        real_imps += 1

        # auction全部数据
        auc_data = test_data.iloc[i: i + 1, :].values.flatten().tolist()

        # auction所在小时段索引
        hour_index = auc_data[config['data_hour_index']]

        feature_data = [test_ctr[i] * 10] # ctr特征
        # 二维矩阵转一维，用flatten函数
        # auction特征（除去click，payprice, hour）
        for feat in auc_data[0: config['data_feature_index']]:
            feature_data += embedding_v.iloc[feat, :].values.tolist()
        state[2: config['feature_num']] = feature_data
        state_full = np.array(state, dtype=float)

        state_deep_copy = copy.deepcopy(state_full)
        state_deep_copy[0], state_deep_copy[1] = state_deep_copy[0] / budget, state_deep_copy[1] / auc_num

        current_data_ctr = test_ctr[i]  # 当前数据的ctr，原始为str，应该转为float

        if current_data_ctr >= test_avg_ctr[int(hour_index)]:
            bid_nums += 1

            # RL代理根据状态选择动作
            action = RL.choose_action(state_deep_copy)

            # 获取剩下的数据
            next_auc_datas = test_data.iloc[i + 1:, :].values
            compare_ctr = test_ctr[i + 1:] >= test_avg_ctr[next_auc_datas[:, config['data_hour_index']]]
            compare_index_array = np.where(compare_ctr == True)[0]

            last_bid_index = 0  # 最后一个出价的下标
            if len(compare_index_array) != 0:
                next_index = compare_index_array[0] + i + 1  # 下一条数据的在元数据集中的下标，加式前半段为获取第一个为True的下标
                if len(compare_index_array) == 1:
                    last_bid_index = compare_index_array[0] + i + 1
            else:
                continue

            # 下一个状态的特征（除去预算、剩余拍卖数量）
            auc_data_next = test_data.iloc[next_index: next_index + 1, :].values.flatten().tolist()[0: config['data_feature_index']]
            if next_index != len(test_data) - 1:
                next_feature_data = [test_ctr[next_index] * 100]
                for feat_next in auc_data_next:
                    next_feature_data += embedding_v.iloc[feat_next, :].values.tolist()
                auc_data_next = np.array(next_feature_data, dtype=float).tolist()
            else:
                auc_data_next = [0 for i in range(config['state_feature_num'])]

            # 获得remainClks和remainBudget的比例，以及punishRate
            remainClkRate = np.sum(test_data.iloc[i + 1:, config['data_clk_index']]) / test_total_clks
            remainBudgetRate = state[0] / budget
            punishRate = remainClkRate / remainBudgetRate

            # 记录当前时刻有点击没赢标的曝光数量以及punishNoWinRate
            if auc_data[config['data_clk_index']] == 1:
                current_with_clk_aucs += 1
                if action < auc_data[config['data_marketprice_index']]:
                    current_clk_no_win_aucs += 1
            else:
                # current_no_clk_budget += auc_data[config['data_marketprice_index']]
                current_no_clk_aucs += 1
                if action > auc_data[config['data_marketprice_index']]:
                    # current_no_clk_win_spent += auc_data[config['data_marketprice_index']]
                    current_no_clk_win_aucs += 1
                else:
                    current_no_clk_no_win_aucs += 1

            temp_adjust_rate = (current_clk_no_win_aucs / current_with_clk_aucs) if current_with_clk_aucs > 0 else 1
            punishNoWinRate = (1 - temp_adjust_rate) if temp_adjust_rate != 1 else 1

            # 记录基础鼓励值baseEncourage，及鼓励比例encourageRate
            baseEncourage = auc_data[config['data_marketprice_index']]
            encourageRate = (1 - current_no_clk_no_win_aucs / current_no_clk_aucs) if current_no_clk_aucs > 0 else 0
            encourageNoClkNoWin = (baseEncourage / encourageRate) if encourageRate > 0 else 1

            # RL采用动作后获得下一个状态的信息以及奖励
            state_, reward, done, is_win = env.step_profit(auc_data, action, auc_data_next, current_data_ctr,
                                                           punishRate, punishNoWinRate, encourageNoClkNoWin)

            if is_win:
                hour_clks[int(hour_index)] += auc_data[config['data_clk_index']]
                total_reward_profits += (current_data_ctr * 30000 - auc_data[config['data_marketprice_index']])
                total_reward_clks += auc_data[config['data_clk_index']]
                total_imps += 1

            if int(auc_data[config['data_clk_index']]) == 1:
                ctr_action_records.append([auc_data[config['data_clk_index']], current_data_ctr, action, auc_data[config['data_marketprice_index']]])
            else:
                ctr_action_records.append([auc_data[config['data_clk_index']],current_data_ctr, action, auc_data[config['data_marketprice_index']]])

            if done:
                if state_[0] < 0:
                    spent = budget
                else:
                    spent = budget - state_[0]
                cpm = (spent / total_imps) if total_imps > 0 else 0
                result_array.append(
                    [total_reward_clks, real_imps, bid_nums, total_imps, budget, spent, cpm, real_clks, total_reward_profits])
                break
            elif last_bid_index:
                if state_[0] < 0:
                    spent = budget
                else:
                    spent = budget - state_[0]
                cpm = (spent / total_imps) if total_imps > 0 else 0
                result_array.append(
                    [total_reward_clks, real_imps, bid_nums, total_imps, budget, spent, cpm, real_clks, total_reward_profits])
                break

            if bid_nums % 1000 == 0:
                now_spent = budget - state_[0]
                if total_imps != 0:
                    now_cpm = now_spent / total_imps
                else:
                    now_cpm = 0
                print('当前: 真实曝光数{}, 出价数{}, 赢标数{}, 当前利润{}, 当前点击数{}, 真实点击数{}, 预算{}, 花费{}, CPM{}\t{}'.format(
                                           real_imps, bid_nums, total_imps, total_reward_profits, total_reward_clks,
                                           real_clks, budget, now_spent, now_cpm, datetime.datetime.now()))

        real_clks += int(auc_data[config['data_clk_index']])
        real_hour_clks[int(hour_index)] += int(auc_data[config['data_clk_index']])

    if len(result_array) == 0:
        result_array = [[0 for i in range(9)]]
    print('\n测试集中: 真实曝光数{}，出价数{}, 赢标数{}, 总点击数{}, '
          '真实点击数{}, 预算{}, 总花费{}, CPM{}，总利润{}\n'.format(result_array[0][1], result_array[0][2],
                                  result_array[0][3],result_array[0][0], result_array[0][7], result_array[0][4],
                                  result_array[0][5], result_array[0][6], result_array[0][8]))
    result_df = pd.DataFrame(data=result_array, columns=['clks', 'real_imps', 'bids', 'imps(wins)', 'budget', 'spent', 'cpm', 'real_clks', 'profits'])
    result_df.to_csv('../../result/PG/profits/result_' + str(budget_para) + '.txt')

    hour_clks_array = {'hour_clks': hour_clks, 'real_hour_clks': real_hour_clks}
    hour_clks_df = pd.DataFrame(hour_clks_array)
    hour_clks_df.to_csv('../../result/PG/profits/test_hour_clks_' + str(budget_para) + '.csv')

    ctr_action_df = pd.DataFrame(data=ctr_action_records)
    ctr_action_df.to_csv('../../result/PG/profits/test_ctr_action_' + str(budget_para) + '.csv', index=None, header=None)

if __name__ == '__main__':
    env = AD_env()
    RL = PolicyGradientForTest(
        action_nums = env.action_numbers,
        feature_nums = env.feature_numbers,
        # output_graph=True # 是否输出tensorboard文件
        )

    budget_para = config['budget_para']
    for i in range(len(budget_para)):
        test_budget, test_auc_numbers = config['test_budget']*budget_para[i], int(config['test_auc_num'])
        print('########测试结果########\n')
        test_env(test_budget, test_auc_numbers, budget_para[i])