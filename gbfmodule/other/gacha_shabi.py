from huijiWiki import HuijiWiki
from ..data.sim_v2 import GBFSim
from config import WIKITEXT_PATH
import time
import os


def update_shabi(cfg, args):
    # 获取傻必数据
    shabi_list = get_shabi_list(cfg)

    if len(shabi_list) == 0:
        print('没有发现必得，请检查账号是否能看到必得')

    gbf_wiki = login_gbf_wiki(cfg)
    for shabi in shabi_list:
        page_title = get_shabi_title(shabi)
        page_content = get_shabi_content(shabi)

        wikitext_file_path = os.path.join(WIKITEXT_PATH, HuijiWiki.filename_fix(f'{page_title}.txt'))
        gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()


def get_shabi_list(cfg):
    gbf_sim = GBFSim(cfg)
    gacha_data = get_gacha_data(gbf_sim)
    shabi_list = []
    for gacha in gacha_data['data']['legend']['lineup']:
        if gacha['stone_flg'] is True:
            continue
        print(f'发现付费抽奖项目：{gacha["name"]}，共有{len(gacha["campaign_gacha_ids"])}个子项目')
        shabi_info = {
            'id': gacha['campaign_id'],
            'name': gacha['name'],
            'start': gacha['service_start'],
            'end': gacha['service_end'],
            'image_path': gacha['image_path'],
            'gacha': {}
        }
        if gacha.get('campaign_gacha_ids'):
            gacha_list = gacha['campaign_gacha_ids']
        else:
            # 如果没有list的情况下，再补充处理方案
            gacha_list = []
            pass
        for sub_gacha in gacha_list:
            gacha_info = get_gacha_info(gbf_sim, sub_gacha['id'], 3)
            if gacha_info is None:
                print(f'抽奖项目【{sub_gacha["name"]}({sub_gacha["id"]})】不是必得')
                continue
            sub_gacha['list'] = gacha_info
            shabi_info['gacha'][sub_gacha['id']] = sub_gacha

            print(f'必得【{sub_gacha["name"]}({sub_gacha["id"]})】数据读取完成')
        shabi_list.append(shabi_info)
    return shabi_list


def get_gacha_data(gbf_sim):
    gacha_data = gbf_sim.get('http://game.granbluefantasy.jp/gacha/list')
    assert gacha_data['data']['legend']['lineup']
    return gacha_data


def get_gacha_info(gbf_sim, gacha_id, page_num):
    gacha_info = gbf_sim.get(f'http://game.granbluefantasy.jp/gacha/provision_ratio/{gacha_id}/{page_num}')
    if gacha_info['status_code'] == 500:
        return None
    assert len(gacha_info['data']['ratio']) == 1
    return gacha_info['data']['appear']


def login_gbf_wiki(cfg):
    gbf_wiki = HuijiWiki('gbf')
    # 登录wiki
    if not gbf_wiki.login(cfg['WIKI']['username'], cfg['WIKI']['password']):
        raise Exception('登录WIKI失败，请稍后再试')
    if not gbf_wiki.get_edit_token():
        raise Exception('获取TOKEN失败，请稍后再试')
    return gbf_wiki


def get_shabi_title(shabi):
    start_time = time.strptime(shabi['start'], "%Y/%m/%d %H:%M")
    return f'必得记录/{time.strftime("%Y/%m%d", start_time)}'


def get_shabi_content(shabi):
    gacha_text_array = []
    for sub_gacha_id, sub_gacha_info in shabi['gacha'].items():
        sub_gacha_text_array = [
            '{{必得信息',
            f'|id={sub_gacha_info["id"]}',
            f'|name={sub_gacha_info["name"]}',
            f'|banner={sub_gacha_info["payment_image"]}',
            f'|icon={sub_gacha_info["text_btn_image"]}',
        ]
        for category_info in sub_gacha_info['list']:
            if category_info['category'] == 0:
                category_name = 'weapon'
            elif category_info['category'] == 2:
                category_name = 'summon'
            else:
                raise Exception(f'预料外的抽奖类型：{category_info["category"]}')
            sub_gacha_text_array.append(f'|{category_name}={",".join([str(item["reward_id"]) for item in category_info["item"]])}')
        sub_gacha_text_array.append('}}')
        gacha_text_array.append(''.join(sub_gacha_text_array))

    content_array = [
        '{{必得记录',
        f'|id={shabi["id"]}',
        f'|name={shabi["name"]}',
        f'|start={shabi["start"]}',
        f'|end={shabi["end"]}',
        f'|image_path={shabi["image_path"]}',
        '|gacha={{列表',
        '\n'.join(gacha_text_array),
        '}}',
        '}}'
    ]

    return '\n'.join(content_array)
