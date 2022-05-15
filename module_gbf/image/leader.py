from module_huiji.huijiWikiTabx import HuijiWikiTabx
from module_huiji.danteng_downloader import Downloader
from module_huiji.danteng_lib import log
import os
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_LEADER_PATH

TABX_TITLE = 'Data:主角.tabx'
TABX_KEY = 'ID'

IMG_CONFIG = [
    {'name': '大图', 'prefix': 'zoom', 'suffix': 'png', 'prefix_url': 'job_change', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '首页图', 'prefix': 'my', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '头像', 'prefix': 'a', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '奥义横图', 'prefix': 'cutin', 'suffix': 'jpg', 'prefix_url': 'cutin_special', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '图标', 'prefix': 'icon', 'suffix': 'png', 'prefix_url': 'job', 'no_sex': True, 'skin_has': False, 'job_has':True, 'has_01': False},
    {'name': '解锁图标', 'prefix': 'jobm', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '编成预览图标', 'prefix': 'quest', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '战斗中图标', 'prefix': 'raid_normal', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': 'SD图', 'prefix': 'sd', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': 'SNS图', 'prefix': 'sns', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': False, 'skin_has': False, 'job_has':True, 'has_01': False},
    {'name': 'LB配置界面', 'prefix': 'zenith', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '战斗结算', 'prefix': 'result', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '职业界面', 'prefix': 'jobon_z', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '组队界面', 'prefix': 'p', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '个人档案', 'prefix': 'pm', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '按钮', 'prefix': 'btn', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '列表OFF', 'prefix': 'jloff', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '列表ON', 'prefix': 'jlon', 'suffix': 'png', 'prefix_url': '', 'no_sex': False, 'skin_has': True, 'job_has':True, 'has_01': False},
    {'name': '职业树图L', 'prefix': 'jtl', 'suffix': 'png', 'prefix_url': 'jobtree_l_off', 'no_sex': True, 'skin_has': False, 'job_has':True, 'has_01': False},
    {'name': '职业树图M', 'prefix': 'jtm', 'suffix': 'png', 'prefix_url': 'jobtree_m', 'no_sex': True, 'skin_has': False, 'job_has':True, 'has_01': False},

    {'name': '皮肤大图标', 'prefix': 'm', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': True, 'skin_has': True, 'job_has':False, 'has_01': True},
    {'name': '皮肤小图标', 'prefix': 's', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': True, 'skin_has': True, 'job_has':False, 'has_01': True},
    {'name': '职业小图标', 'prefix': 's', 'suffix': 'jpg', 'prefix_url': '', 'no_sex': True, 'skin_has': False, 'job_has':True, 'has_01': True},
    {'name': '皮肤预览图', 'prefix': 'skin', 'suffix': 'png', 'prefix_url': '', 'no_sex': True, 'skin_has': True, 'job_has':False, 'has_01': True},
]

WEAPON_TYPE_MAP = {
    1: 'sw',
    2: 'kn',
    3: 'sp',
    4: 'ax',
    5: 'wa',
    6: 'gu',
    7: 'me',
    8: 'bw',
    9: 'mc',
    10: 'kt',
}


def leader(cfg):
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
    downloader = Downloader()
    downloader.set_try_count(retry_times)

    npc_base_url = cfg['base_url'] + 'assets/leader'
    ul_base_url = cfg['base_url'] + 'ui/icon'

    for leader_id, leader_info in tabx:
        if leader_id == 0:
            continue

        work_list = []

        for config in IMG_CONFIG:
            if not config['skin_has'] and leader_info['category'] == 0:
                continue
            if not config['job_has'] and leader_info['category'] > 0:
                continue
            base_url = ul_base_url if config['prefix'] in ['icon'] else npc_base_url
            sub_path = config['prefix'] if config['prefix_url'] == '' else config['prefix_url']
            if config['no_sex']:
                if config['has_01']:
                    img_url = '%s/%s/%d_01.%s' % (base_url, sub_path, leader_id, config['suffix'])
                else:
                    img_url = '%s/%s/%d.%s' % (base_url, sub_path, leader_id, config['suffix'])
                save_filename = '%s_%s.%s' % (config["prefix"], leader_id, config['suffix'])

                save_path = os.path.join(IMAGE_PATH, IMAGE_LEADER_PATH, str(leader_id), save_filename)
                save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, save_filename)
                if os.path.exists(save_path):
                    continue
                work_list.append({
                    'url': img_url,
                    'path': save_path,
                    'new': save_new_path,
                })
            else:
                weapon_text = WEAPON_TYPE_MAP[leader_info['weapon1']]
                for sex_index in range(0, 2):
                    img_url = '%s/%s/%d_%s_%d_01.%s' % (base_url, sub_path, leader_id, weapon_text, sex_index, config['suffix'])
                    save_filename = '%s_%s_%d.%s' % (config["prefix"], leader_id, sex_index, config['suffix'])

                    save_path = os.path.join(IMAGE_PATH, IMAGE_LEADER_PATH, str(leader_id), save_filename)
                    save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, save_filename)
                    if os.path.exists(save_path):
                        continue
                    work_list.append({
                        'url': img_url,
                        'path': save_path,
                        'new': save_new_path,
                    })

        if len(work_list) > 0:
            log('开始下载主角 %s(%d) 的图片资源（共%d个）' % (leader_info["name_chs"], leader_id, len(work_list)))
            for work_info in work_list:
                if save_to_new:
                    downloader.download_multi_copies(work_info['url'], [work_info['path'], work_info['new']])
                else:
                    downloader.download_multi_copies(work_info['url'], [work_info['path']])
        downloader.wait_threads()
