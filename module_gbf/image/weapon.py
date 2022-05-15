from module_huiji.huijiWikiTabx import HuijiWikiTabx
from module_huiji.danteng_downloader import Downloader
from module_huiji.danteng_lib import log
from ..util import get_skip_list
import os
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_WEAPON_PATH

TABX_TITLE = 'Data:武器列表.tabx'
TABX_KEY = 'ID'

IMG_CONFIG = [
    {'name': '立绘大图', 'filename_prefix': 'b', 'sub_url': 'b', 'suffix': 'png', 'has_extra': True},
    # g和b好像是一样的
    # {'name': '立绘大图', 'filename_prefix': 'g', 'sub_url': 'g', 'suffix': 'png', 'has_extra': True},
    {'name': '横图标', 'filename_prefix': 'm', 'sub_url': 'm', 'suffix': 'jpg', 'has_extra': True},
    {'name': '方图标', 'filename_prefix': 's', 'sub_url': 's', 'suffix': 'jpg', 'has_extra': True},
    {'name': '主武器图标', 'filename_prefix': 'ls', 'sub_url': 'ls', 'suffix': 'jpg', 'has_extra': True},
    {'name': '战斗用图', 'filename_prefix': 'cjs', 'sub_url': 'cjs', 'suffix': 'png', 'has_extra': True},
]


def weapon(cfg):
    tabx = HuijiWikiTabx(cfg['wiki'], TABX_TITLE, TABX_KEY)

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
    skip_list = get_skip_list()

    downloader = Downloader()
    downloader.set_try_count(retry_times)

    weapon_base_url = cfg['base_url'] + 'assets/weapon'
    cjs_base_url = cfg['base_url'] + 'cjs'

    for weapon_id, weapon_info in tabx:
        if weapon_id == 0:
            continue
        # 生成需要下载的list
        work_list = []

        for config in IMG_CONFIG:
            img_base_name = str(weapon_id)
            if config['sub_url'] == 'cjs':
                if weapon_info['kind'] == 7:
                    img_name_list = ['%s_1' % img_base_name, '%s_2' % img_base_name]
                else:
                    img_name_list = [img_base_name]
            else:
                img_name_list = [img_base_name]

            for img_name in img_name_list:
                if config['sub_url'] == 'cjs':
                    img_url = '%s/%s.%s' % (cjs_base_url, img_name, config["suffix"])
                else:
                    img_url = '%s/%s/%s.%s' % (weapon_base_url, config["sub_url"], img_name, config["suffix"])
                if img_url in skip_list:
                    continue

                folder_name = config['folder'] if 'folder' in config else ''
                save_filename = '%s_%s.%s' % (config["filename_prefix"], img_name, config["suffix"])

                save_path = os.path.join(IMAGE_PATH, IMAGE_WEAPON_PATH, '%s_%s' % (str(weapon_id), weapon_info["name_en"]), folder_name, save_filename)
                save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, folder_name, save_filename)

                if os.path.exists(save_path):
                    continue
                work_list.append({
                    'url': img_url,
                    'path': save_path,
                    'new': save_new_path,
                })

        if len(work_list) > 0:
            log('开始下载武器 %s(%d) 的图片资源（共%d个）' % (weapon_info["name_en"], weapon_id, len(work_list)))
            for work_info in work_list:
                if save_to_new:
                    downloader.download_multi_copies(work_info['url'], [work_info['path'], work_info['new']])
                else:
                    downloader.download_multi_copies(work_info['url'], [work_info['path']])
        downloader.wait_threads()
