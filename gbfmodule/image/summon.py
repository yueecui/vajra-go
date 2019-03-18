from huijiWikiTabx import HuijiWikiTabx
from danteng_downloader import Downloader
from danteng_lib import log
from ..util import get_skip_list
import os
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_SUMMON_PATH

TABX_TITLE = 'Data:召唤石列表.tabx'
TABX_KEY = 'ID'

IMG_CONFIG = [
    {'name': '立绘大图', 'filename_prefix': 'b', 'sub_url': 'b', 'suffix': 'png', 'has_extra': True},
    {'name': '详情横图', 'filename_prefix': 'detail', 'sub_url': 'detail', 'suffix': 'png', 'has_extra': True},
    {'name': '横图标', 'filename_prefix': 'm', 'sub_url': 'm', 'suffix': 'jpg', 'has_extra': True},
    {'name': '方图标', 'filename_prefix': 's', 'sub_url': 's', 'suffix': 'jpg', 'has_extra': True},
    {'name': '主召图标', 'filename_prefix': 'party_main', 'sub_url': 'party_main', 'suffix': 'jpg', 'has_extra': True},
    {'name': '副召图标', 'filename_prefix': 'party_sub', 'sub_url': 'party_sub', 'suffix': 'jpg', 'has_extra': True},
]


def summon(cfg):
    tabx = HuijiWikiTabx(cfg['wiki'], TABX_TITLE, TABX_KEY)

    # 开关
    save_to_new = False
    retry_times = 5
    if 'OPTION' in cfg:
        if 'new' in cfg['OPTION'] and cfg['OPTION']['new'].lower() == 'yes':
            save_to_new = True
        if 'retry' in cfg['OPTION']:
            try:
                retry_times = int(cfg['OPTION']['retry'])
            except:
                pass

    # 配置下载器
    skip_list = get_skip_list()

    downloader = Downloader()
    downloader.set_try_count(retry_times)

    npc_base_url = cfg['base_url'] + 'assets/summon'

    for summon_id, summon_info in tabx:
        # 生成需要下载的list
        index_list = ['']
        for uncap_index in summon_info['uncap_img']:
            index_list.append('%02d' % int(uncap_index))

        work_list = []

        for config in IMG_CONFIG:
            config_index_list = index_list.copy()
            for index in config_index_list:
                if index == '':
                    img_base_name = str(summon_id)
                else:
                    img_base_name = '%d_%s' % (summon_id, index)
                img_name_list = [img_base_name]

                for img_name in img_name_list:
                    img_url = '%s/%s/%s.%s' % (npc_base_url, config["sub_url"], img_name, config["suffix"])
                    if img_url in skip_list:
                        continue

                    folder_name = config['folder'] if 'folder' in config else ''
                    save_filename = '%s_%s.%s' % (config["filename_prefix"], img_name, config["suffix"])

                    save_path = os.path.join(IMAGE_PATH, IMAGE_SUMMON_PATH, '%s_%s' % (str(summon_id), summon_info["name_jp"]), folder_name, save_filename)
                    save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, folder_name, save_filename)

                    if os.path.exists(save_path):
                        continue
                    work_list.append({
                        'url': img_url,
                        'path': save_path,
                        'new': save_new_path,
                    })

        if len(work_list) > 0:
            log('开始下载召唤石 %s(%d) 的图片资源（共%d个）' % (summon_info["name_chs"], summon_id, len(work_list)))
            for work_info in work_list:
                if save_to_new:
                    downloader.download_multi_copies(work_info['url'], [work_info['path'], work_info['new']])
                else:
                    downloader.download_multi_copies(work_info['url'], [work_info['path']])
        downloader.wait_threads()
