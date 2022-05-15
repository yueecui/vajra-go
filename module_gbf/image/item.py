from module_huiji.danteng_downloader import Downloader
from module_huiji.huijiWikiTabx import HuijiWikiTabx
from ..util import get_skip_list
import os
import re
import shutil
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_WEAPON_SKILL_PATH, DATA_PATH
from ..data.sim import GBFSim


def item(cfg):
    # 开关
    retry_times = 5
    if 'IMAGE' in cfg:
        if 'retry' in cfg['IMAGE']:
            try:
                retry_times = int(cfg['IMAGE']['retry'])
            except:
                pass

    # 先检查本地
    data_base_path = os.path.join(IMAGE_PATH, 'item')
    image_base_url = r'http://game-a.granbluefantasy.jp/assets/img/sp/assets/item/'

    # 配置下载器
    downloader = Downloader()
    downloader.set_try_count(retry_times)

    # 下载普通素材道具图标
    # 其他道具图标需要手工下载
    tabx_page_title = f'Data:{cfg["TABX"]["item"]}.tabx'
    item_tabx = HuijiWikiTabx(cfg['wiki'], tabx_page_title, 'ID')
    article_path = os.path.join(data_base_path, 'article_s')
    for item_index, item_info in item_tabx:
        if item_info['ID'] == 0:
            continue
        file_name = f'{item_info["ID"]}.jpg'
        file_path = os.path.join(article_path, file_name)
        if os.path.exists(file_path):
            continue
        download_url = f'{image_base_url}/article/s/{file_name}'
        downloader.download_multi_copies(download_url, [file_path])
    downloader.wait_threads()

    all_list = os.listdir(data_base_path)

    checked_data = {}

    for sub_path_name in all_list:
        sub_full_path = os.path.join(data_base_path, sub_path_name)
        if not os.path.isdir(sub_full_path):
            continue

        sub_path_info = sub_path_name.split('_')
        if len(sub_path_info) != 2 or sub_path_info[1] not in ['s', 'm']:
            continue

        sub_name = sub_path_info[0]
        if sub_name not in checked_data:
            checked_data[sub_name] = []

        all_sub_list = os.listdir(sub_full_path)

        for filename in all_sub_list:
            if filename in checked_data[sub_name]:
                continue
            else:
                checked_data[sub_name].append(filename)

            src_m_path = os.path.join(data_base_path, f'{sub_name}_m', filename)
            src_s_path = os.path.join(data_base_path, f'{sub_name}_s', filename)

            if not os.path.exists(src_m_path):
                download_url = f'{image_base_url}/{sub_name}/m/{filename}'
                downloader.download_multi_copies(download_url, [src_m_path])
            if not os.path.exists(src_s_path):
                download_url = f'{image_base_url}/{sub_name}/s/{filename}'
                downloader.download_multi_copies(download_url, [src_s_path])
        downloader.wait_threads()

    # 复制到wiki目录中，如果有新图片就复制到new里
    for sub_name, all_sub_list in checked_data.items():
        for filename in all_sub_list:
            dst_filename = filename.replace('item_', '')
            for sub_type in ['s', 'm']:

                src_path = os.path.join(data_base_path, f'{sub_name}_{sub_type}', filename)
                if sub_name == 'article':
                    dst_path = os.path.join(data_base_path, 'wiki', f'IT_{sub_type}_{dst_filename}')
                    new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, f'IT_{sub_type}_{dst_filename}')
                else:
                    dst_path = os.path.join(data_base_path, 'wiki', f'IT_{sub_name}_{sub_type}_{dst_filename}')
                    new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, f'IT_{sub_name}_{sub_type}_{dst_filename}')

                if os.path.exists(dst_path):
                    continue

                shutil.copy2(src_path, dst_path)
                shutil.copy2(src_path, new_path)

