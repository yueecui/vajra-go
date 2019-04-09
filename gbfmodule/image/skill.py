from danteng_downloader import Downloader
from danteng_lib import log
from ..util import get_skip_list
import os
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_SKILL_PATH

DOWNLOAD_TYPE = 'skill'


def skill(cfg):
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

    # 获取范围
    start = 0
    end = 0
    if 'IMAGE' in cfg:
        if 'sk_start' in cfg['IMAGE']:
            try:
                start = int(cfg['IMAGE']['sk_start'])
            except:
                pass
        if 'sk_end' in cfg['IMAGE']:
            try:
                end = int(cfg['IMAGE']['sk_end'])
            except:
                pass

    if start == 0 or end == 0 or start > end:
        log('抓取技能图标的ID范围有误，请检查')
        return False

    # 配置下载器
    skip_list = get_skip_list()

    downloader = Downloader()
    downloader.set_try_count(retry_times)

    # http://game-a.granbluefantasy.jp/assets/img/sp/
    # ui/icon/ability/m/17_1.png
    skill_base_url = cfg['base_url'] + 'ui/icon/ability/m/'

    for sk_id in range(start, end + 1):
        for sk_type in range(1, 6):
            save_filename = '%s_%s.png' % (sk_id, sk_type)
            skill_icon_url = skill_base_url + save_filename
            if skill_icon_url in skip_list:
                continue

            save_filename = 'SK_' + save_filename
            save_path = os.path.join(IMAGE_PATH, IMAGE_SKILL_PATH, save_filename)
            if os.path.exists(save_path):
                continue
            save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, save_filename)

            if save_to_new:
                downloader.download_multi_copies(skill_icon_url, [save_path, save_new_path])
            else:
                downloader.download_multi_copies(skill_icon_url, [save_path])
    downloader.wait_threads()
