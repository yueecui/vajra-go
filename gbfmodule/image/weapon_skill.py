from danteng_downloader import Downloader
from danteng_lib import log, load_json
from ..util import get_skip_list
import os
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_WEAPON_SKILL_PATH, DATA_PATH
from ..data.sim import GBFSim


def weapon_skill(cfg):
    # 开关
    save_to_new = False
    retry_times = 5
    if 'IMAGE' in cfg:
        if 'new' in cfg['IMAGE'] and cfg['IMAGE']['new'].lower() == 'yes':
            save_to_new = True
        if 'retry' in cfg['IMAGE']:
            try:
                retry_times = int(cfg['IMAGE']['retry'])
            except:
                pass

    # 配置下载器
    downloader = Downloader()
    downloader.set_try_count(retry_times)

    # 数据循环
    gbf_sim = GBFSim(cfg)
    data_base_path = os.path.join(DATA_PATH, 'weapon', 'jp')
    image_base_url = 'http://game-a.granbluefantasy.jp/assets_en/img/sp/ui/icon/skill/'

    for weapon_id in gbf_sim.all_weapon():
        weapon_json_path = os.path.join(data_base_path, f'{weapon_id}.json')
        weapon_info = load_json(weapon_json_path)

        for skill_key in ['skill1', 'skill2', 'skill3']:
            if skill_key not in weapon_info or not weapon_info[skill_key]:
                continue
            skill_icon_name = weapon_info[skill_key]['image'].strip()

            save_filename = f'WS_{skill_icon_name}.png'
            save_path = os.path.join(IMAGE_PATH, IMAGE_WEAPON_SKILL_PATH, save_filename)
            if os.path.exists(save_path):
                continue

            skill_icon_url = image_base_url + f'{skill_icon_name}.png'
            save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, save_filename)

            if save_to_new:
                downloader.download_multi_copies(skill_icon_url, [save_path, save_new_path])
            else:
                downloader.download_multi_copies(skill_icon_url, [save_path])
    downloader.wait_threads()
