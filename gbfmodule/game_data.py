from .data.sim import GBFSim


# 下载新的游戏数据
def download_game_data(cfg, args):
    gbf_sim = GBFSim(cfg)

    # 初始化本地数据
    gbf_sim.init_local_db()

    # 获取武器数据
    gbf_sim.download_weapon_data()
    x = 1
