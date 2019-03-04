from .image import *
from huijiWiki import HuijiWiki
from .data.sim import GBFSim


def download_game_data(cfg, args):
    gbf_sim = GBFSim(cfg)
    # gbf_sim.set_language(2)
    gbf_sim.download_weapon_data()
    x = 1
