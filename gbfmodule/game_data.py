from .image import *
from huijiWiki import HuijiWiki
from .data.sim import GBFSim


def download_game_data(cfg, args):
    gbf_sim = GBFSim(cfg)
    x = 1
