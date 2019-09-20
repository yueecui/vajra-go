from huijiWikiTabx import HuijiWikiTabx
from danteng_downloader import Downloader
from danteng_lib import log
from ..util import get_skip_list
import os
from config import IMAGE_PATH, IMAGE_NEW_PATH, IMAGE_NPC_PATH, SKIP_LOG

TABX_TITLE = 'Data:角色列表.tabx'
TABX_KEY = 'ID'

RES_TABX_TITLE = 'Data:角色资源数据补充.tabx'
RES_TABX_KEY = 'ID'

IMG_CONFIG = [
    {'name': '立绘', 'filename_prefix': 'zoom', 'sub_url': 'zoom', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True, 'multi_allow_index': ['01']},
    # {'name': '图鉴', 'filename_prefix': 'b', 'sub_url': 'b', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True, 'multi_allow_index': ['01']},
    {'name': '详情横图', 'filename_prefix': 'detail', 'sub_url': 'detail', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '首页图', 'filename_prefix': 'my', 'sub_url': 'my', 'suffix': 'png', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True, 'multi_allow_index': ['01']},
    {'name': '横图标', 'filename_prefix': 'm', 'sub_url': 'm', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '方图标', 'filename_prefix': 's', 'sub_url': 's', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '编成图标', 'filename_prefix': 'f', 'sub_url': 'f', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '战斗图标', 'filename_prefix': 'raid', 'sub_url': 'raid_normal', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '模组', 'filename_prefix': 'sd', 'sub_url': 'sd', 'suffix': 'png', 'has_extra': False, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': False},
    {'name': '奥义横图', 'filename_prefix': 'cutin', 'sub_url': 'cutin_special', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True, 'multi_allow_index': ['01']},
    {'name': '奥义连锁图', 'filename_prefix': 'chain', 'sub_url': 'raid_chain', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': True, 'skin': False, 'multi': True},
    {'name': '推特图', 'filename_prefix': 'sns', 'sub_url': 'sns', 'suffix': 'jpg', 'has_extra': True, 'skip_index': ['02'], 'multi_element': False, 'skin': False, 'multi': True, 'multi_disable_normal': True},

    {'name': '皮肤方图标', 'filename_prefix': 'skin_s', 'folder': 'skin', 'sub_url': 's/skin', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': False, 'skin': True, 'multi': True},
    {'name': '皮肤编成图标', 'filename_prefix': 'skin_f', 'folder': 'skin', 'sub_url': 'f/skin', 'suffix': 'jpg', 'has_extra': True, 'skip_index': [], 'multi_element': False, 'skin': True, 'multi': True},
]


def npc(cfg):
    tabx = HuijiWikiTabx(cfg['wiki'], TABX_TITLE, TABX_KEY)
    res_tabx = HuijiWikiTabx(cfg['wiki'], RES_TABX_TITLE, RES_TABX_KEY)

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

    skip_log_f = open(SKIP_LOG, 'w')

    for npc_id, npc_info in tabx:
        if npc_id == 0:
            continue

        # 生成需要下载的list
        index_list = ['01', '02']
        if npc_info['max_evo'] == 5:
            index_list.append('03')
        extra_index_list = npc_info['extra_img']

        work_list = []

        for config in IMG_CONFIG:
            config_index_list = index_list.copy()
            if config['has_extra']:
                config_index_list.extend(extra_index_list)
            for index in config_index_list:
                if index in config['skip_index']:
                    continue
                if not download_skin and config['skin']:
                    continue

                img_base_name = '%d_%s' % (npc_id, index)
                img_name_list = [img_base_name]
                if config['multi'] and npc_info['char_count'] > 0:
                    # 检测是否为允许的key
                    multi_allow_index_list = config['multi_allow_index'] if 'multi_allow_index' in config else []
                    if len(multi_allow_index_list) > 0:
                        allow = index in multi_allow_index_list
                    else:
                        allow = True

                    # 检测是否为允许的项目
                    res_info = res_tabx.get_row(npc_info['ID'])
                    multi_count = res_info['img_count']
                    if config['filename_prefix'] in res_info:
                        res_value = res_info[config['filename_prefix']]
                        if type(res_value) == bool:
                            if not res_value:
                                allow = False
                        elif type(res_value) == int:
                            multi_count = res_value

                    if allow:
                        for m_index in range(1, multi_count+1):
                            img_name_list.append('%s_10%d' % (img_base_name, m_index))

                        # 如果移除普通
                        flag_disable_normal_name = config['multi_disable_normal'] if 'multi_disable_normal' in config else False
                        if flag_disable_normal_name:
                            img_name_list.remove(img_base_name)
                if config['skin'] and download_skin:
                    new_img_name_list = []
                    for img_name in img_name_list:
                        for e_index in range(1, 7):
                            new_img_name_list.append('%s_s%d' % (img_name, e_index))
                    img_name_list = new_img_name_list
                if config['multi_element'] and npc_info['element'] == '可变化':
                    new_img_name_list = []
                    for img_name in img_name_list:
                        for e_index in range(1, 7):
                            new_img_name_list.append('%s_0%d' % (img_name, e_index))
                    img_name_list = new_img_name_list

                for img_name in img_name_list:
                    img_url = '%s/%s/%s.%s' % (npc_base_url, config["sub_url"], img_name, config["suffix"])
                    if img_url in skip_list:
                        continue

                    folder_name = config['folder'] if 'folder' in config else ''
                    save_filename = '%s_%s.%s' % (config["filename_prefix"], img_name, config["suffix"])

                    save_path = os.path.join(IMAGE_PATH, IMAGE_NPC_PATH, str(npc_id), folder_name, save_filename)
                    save_new_path = os.path.join(IMAGE_PATH, IMAGE_NEW_PATH, folder_name, save_filename)

                    if os.path.exists(save_path):
                        continue
                    work_list.append({
                        'url': img_url,
                        'path': save_path,
                        'new': save_new_path,
                    })

        if len(work_list) > 0:
            log('开始下载角色 %s(%d) 的图片资源（共%d个）' % (npc_info["name_chs"], npc_id, len(work_list)))
            for work_info in work_list:
                if save_to_new:
                    downloader.download_multi_copies(work_info['url'], [work_info['path'], work_info['new']], log_handle=skip_log_f)
                else:
                    downloader.download_multi_copies(work_info['url'], [work_info['path']], log_handle=skip_log_f)
        downloader.wait_threads()
    skip_log_f.close()
