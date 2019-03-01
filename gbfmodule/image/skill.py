from danteng_downloader import Downloader
from danteng_lib import log
from ..util import get_skip_list
import os

DOWNLOAD_TYPE = 'skill'


def skill(cfg):
    # 开关
    save_to_new = False
    retry_times = 5
    skip_list_filename = ''
    if 'OPTION' in cfg:
        if 'new' in cfg['OPTION'] and cfg['OPTION']['new'].lower() == 'yes':
            save_to_new = True
        if 'retry' in cfg['OPTION']:
            try:
                retry_times = int(cfg['OPTION']['retry'])
            except:
                pass
        if 'skip_list' in cfg['OPTION']:
            skip_list_filename = cfg['OPTION']['skip_list']

    # 获取范围
    start = 0
    end = 0
    if 'SETTING' in cfg:
        if 'sk_start' in cfg['SETTING']:
            try:
                start = int(cfg['SETTING']['sk_start'])
            except:
                pass
        if 'sk_end' in cfg['SETTING']:
            try:
                end = int(cfg['SETTING']['sk_end'])
            except:
                pass

    if start == 0 or end == 0 or start > end:
        log('抓取技能图标的ID范围有误，请检查')
        return False

    # 配置下载器
    skip_list = get_skip_list(skip_list_filename)

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
            save_path = os.path.join(cfg['PATH']['skill'], save_filename)
            if os.path.exists(save_path):
                continue
            save_new_path = os.path.join(cfg['PATH']['new'], save_filename)

            if save_to_new:
                downloader.download_multi_copies(skill_icon_url, [save_path, save_new_path])
            else:
                downloader.download_multi_copies(skill_icon_url, [save_new_path])
    downloader.wait_threads()
