from set import *

# 记录统计数据的json文件地址
STATISTICS_JSON = 'game_db_bak.json'

RARITY_ID_LIST = [1, 2, 3, 4]

# 猜测ID时，深入设置
GUESS_CONFIG_BY_RARITY = {
    1: {
        'step': 2,
        'max_time': 1,
    },
    2: {
        'step': 2,
        'max_time': 1,
    },
    3: {
        'step': 3,
        'max_time': 2,
    },
    4: {
        'step': 10,
        'max_time': 2,
    },
}


# 武器ID编成规则
# 1位 - 固定为1，表示武器
# 2位 - 固定为0
# 3位 - 表示稀有度：N=1，R=2，SR=3，SSR=4
# 4位 - 固定为0
# 5位 - 武器类型
# 6-8位 - 类型内索引，从0开始
# 9-10位 - 固定为0

WEAPON_TYPE_MAP = {
    0: '剑',
    1: '短剑',
    2: '枪',
    3: '斧',
    4: '杖',
    5: '铳',
    6: '格斗',
    7: '弓',
    8: '乐器',
    9: '刀',
}

# 召唤石ID规则
# 1位 - 固定为2，表示召唤石
# 2位 - 固定为0
# 3位 - 表示稀有度：N=1，R=2，SR=3，SSR=4
# 4位 - 固定为0
# 5-7位 - 稀有度内索引
# 8-10位 - 固定为0
