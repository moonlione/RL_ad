import random
import pandas as pd

random.seed(999)

# path = '../../output/pnn/'
'''
原始数据统计
0606 448164 328 30096630
0607 478109 307 30228554
0608 413804 347 30615541 √ 训练
0609 423726 351 30548604 √ 测试
0610 434240 370 30303929 
0611 437520 395 30309883
0612 447493 356 30297100
'''
# 负采样后达到的点击率
CLICK_RATE = 0.001  # 1:1000

# 20130608一天
def getSampleRate():
    click = 347  #20130608 1天
    total = 413804  # 20130608 1天
    rate = click / (CLICK_RATE * (total - click))
    # 原始数据中的点击和曝光总数
    print('clicks: {0} impressions: {1}\n'.format(click, total))
    # 一个负例被选中的概率，每多少个负例被选中一次
    # print('sample rate: {0} sample num: {1}'.format(rate, 1 / rate))
    print('sample_rate is:',rate)
    return rate

# 获取训练样本
sample_rate = getSampleRate()

with open( '../../sample/20130608_train_sample.csv', 'w') as fo:
    fi = open('../../data/20130608_train_data.csv')
    p = 0 # 原始正样本
    n = 0 # 原始负样本
    nn = 0 # 剩余的负样本
    c = 0 # 总数
    for t, line in enumerate(fi, start=1):
        if t == 1:
            fo.write(line)
        else:
            c += 1
            label = line.split(',')[0] # 是否点击标签
            if int(label) == 0:
                n += 1
                if random.randint(0, 413804) <= 413804 * sample_rate:  # down sample, 选择对应数据量的负样本
                    fo.write(line)
                    nn += 1
            else:
                p += 1
                fo.write(line)

        if t % 1000000 == 0:
            print(t)
    fi.close()
# print(c, n, p+nn, p, nn, (p+nn)/c, nn / n, p / nn)
print('训练数据负采样完成')

# 20130609一天
def getTestSampleRate():
    click = 351  # 20130609一天
    total = 423726  # 20130609一天
    rate = click / (CLICK_RATE * (total - click))
    # 原始数据中的点击和曝光总数
    print('clicks: {0} impressions: {1}\n'.format(click, total))
    # 一个负例被选中的概率，每多少个负例被选中一次
    # print('sample rate: {0} sample num: {1}'.format(rate, 1 / rate))
    print('sample_rate is:',rate)
    return rate

# 获取训练样本
test_sample_rate = getTestSampleRate()

# 获取测试样本,20130612一天
with open( '../../sample/20130609_test_sample.csv', 'w') as fo:
    fi = open('../../data/20130609_test_data.csv')
    p = 0 # 原始正样本
    n = 0 # 原始负样本
    nn = 0 # 剩余的负样本
    c = 0 # 总数
    for t, line in enumerate(fi, start=1):
        if t==1:
            fo.write(line)
        else:
            c += 1
            label = line.split(',')[0] # 是否点击标签
            if int(label) == 0:
                n += 1
                if random.randint(0, 423726) <= 423726 * test_sample_rate:  # down sample, 选择对应数据量的负样本
                    fo.write(line)
                    nn += 1
            else:
                p += 1
                fo.write(line)

        if t % 10000 == 0:
            print(t)
    fi.close()
print('测试数据负采样完成')


