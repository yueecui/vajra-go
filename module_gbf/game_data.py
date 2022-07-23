from .data.sim import GBFSim


# 下载新的游戏数据
def download_game_data(cfg, args):
    gbf_sim = GBFSim(cfg)

    # # 先检查check_new_id目录里是否有json文件，如果有按照名字下载数据
    # gbf_sim.download_data_by_new_id()
    #
    # # 获取武器数据
    # gbf_sim.download_weapon_data()
    # # 获取召唤数据
    # gbf_sim.download_summon_data()

    # 新流程
    # 武器（补齐英文商店数据）
    gbf_sim.download_weapon_data_v2()
    gbf_sim.download_weapon_data_v2_note()

    # 召唤石（补齐编成数据）
    gbf_sim.download_summon_data_v2()


# 尝试查找新的游戏数据
def find_new_game_data(cfg, args):
    gbf_sim = GBFSim(cfg)

    # 检查所有以前空缺的数据位置
    if args.find_order == 'old':
        gbf_sim.check_miss_weapon_data()
        gbf_sim.check_miss_summon_data()
    else:
        gbf_sim.check_new_weapon_data()
        gbf_sim.check_new_summon_data()


# 重新下载所有数据
def reload_all_data(cfg, args):
    gbf_sim = GBFSim(cfg)

    gbf_sim.reload_weapon_data()


# 重新下载所有数据
def download_all_news(cfg, args):
    gbf_sim = GBFSim(cfg)

    gbf_sim.download_all_news()
