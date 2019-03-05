from .data.sim import GBFSim


# 下载新的游戏数据
def download_game_data(cfg, args):
    gbf_sim = GBFSim(cfg)

    # 获取武器数据
    gbf_sim.download_weapon_data()
    # 获取召唤数据
    gbf_sim.download_summon_data()
