from module_huiji.huijiWikiTabx import HuijiWikiTabx
from module_huiji.danteng_downloader import Downloader
from module_huiji.danteng_lib import log
from ..util import get_skip_list
import os
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_SKIN_PATH

TABX_TITLE = 'Data:皮肤.tabx'
TABX_KEY = 'ID'

IMG_CONFIG = [
    {'name': '立绘', 'filename_prefix': 'zoom', 'sub_url': 'zoom', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True, 'multi_allow_index': ['01']},
    {'name': '详情横图', 'filename_prefix': 'detail', 'sub_url': 'detail', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '首页图', 'filename_prefix': 'my', 'sub_url': 'my', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '横图标', 'filename_prefix': 'm', 'sub_url': 'm', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '方图标', 'filename_prefix': 's', 'sub_url': 's', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '编成图标', 'filename_prefix': 'f', 'sub_url': 'f', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '战斗图标', 'filename_prefix': 'raid', 'sub_url': 'raid_normal', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '模组', 'filename_prefix': 'sd', 'sub_url': 'sd', 'suffix': 'png', 'has_extra': False, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': False},
    {'name': '奥义横图', 'filename_prefix': 'cutin', 'sub_url': 'cutin_special', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True, 'multi_allow_index': ['01']},
    {'name': '奥义连锁图', 'filename_prefix': 'chain', 'sub_url': 'raid_chain', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    # {'name': '推特图', 'filename_prefix': 'sns', 'sub_url': 'sns', 'suffix': 'jpg', 'has_extra': True, 'skip_index': ['02'], 'multi_element': False, 'skin': False, 'multi': True, 'multi_disable_normal': True},

    {'name': '列表大图', 'filename_prefix': 'skin', 'sub_url': 'skin', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '皮肤方图标', 'filename_prefix': 'skin_s', 'folder': 'skin', 'sub_url': 's/skin', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': False, 'skin': True, 'multi': True},
    {'name': '皮肤编成图标', 'filename_prefix': 'skin_f', 'folder': 'skin', 'sub_url': 'f/skin', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': False, 'skin': True, 'multi': True},
]


def skin(cfg):
    tabx = HuijiWikiTabx(cfg['wiki'], TABX_TITLE, TABX_KEY)

    # 开关
    download_skin = False
    save_to_new = False
    retry_times = 5
    if 'IMAGE' in cfg:
        if 'skin' in cfg['IMAGE'] and cfg['IMAGE']['skin'].lower() == 'yes':
            download_skin = True
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

    npc_base_url = cfg['base_url'] + 'assets/npc'

    for npc_id, npc_info in tabx:
        if npc_id == 0:
            continue
        # 生成需要下载的list
        index_list = ['01']

        work_list = []

        for config in IMG_CONFIG:
            config_index_list = index_list.copy()
            for index in config_index_list:
                if index in config['skip_index']:
                    continue
                if not download_skin and config['skin']:
                    continue

                img_base_name = '%d_%s' % (npc_id, index)
                img_name_list = [img_base_name]

                if config['skin'] and download_skin:
                    new_img_name_list = []
                    for img_name in img_name_list:
                        for e_index in range(1, 7):
                            new_img_name_list.append('%s_s%d' % (img_name, e_index))
                    img_name_list = new_img_name_list

                for img_name in img_name_list:
                    img_url = '%s/%s/%s.%s' % (npc_base_url, config["sub_url"], img_name, config["suffix"])
                    if img_url in skip_list:
                        continue

                    folder_name = config['folder'] if 'folder' in config else ''
                    save_filename = '%s_%s.%s' % (config["filename_prefix"], img_name, config["suffix"])

                    save_path = os.path.join(IMAGE_PATH, IMAGE_SKIN_PATH, '%s_%s_%s' % (str(npc_id), npc_info["comment"], npc_info["name_jp"]), folder_name, save_filename)
                    save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, folder_name, save_filename)

                    if os.path.exists(save_path):
                        continue
                    work_list.append({
                        'url': img_url,
                        'path': save_path,
                        'new': save_new_path,
                    })

        if len(work_list) > 0:
            log('开始下载角色 %s(%d) 的图片资源（共%d个）' % (npc_info["comment"], npc_id, len(work_list)))
            for work_info in work_list:
                if save_to_new:
                    downloader.download_multi_copies(work_info['url'], [work_info['path'], work_info['new']])
                else:
                    downloader.download_multi_copies(work_info['url'], [work_info['path']])
        downloader.wait_threads()
