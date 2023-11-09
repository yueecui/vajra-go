import json

from module_huiji.huijiWiki import HuijiWiki
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
            'gacha': {},
            'is_choice': 'choice_data' in gacha
        }

        if shabi_info['is_choice']:
            shabi_info['gacha'] = get_choice_shabi_info(gbf_sim, gacha)
        else:
            shabi_info['gacha'] = get_normal_shabi_info(gbf_sim, gacha)
        shabi_list.append(shabi_info)
    return shabi_list


def get_gacha_data(gbf_sim):
    gacha_data = gbf_sim.get('https://game.granbluefantasy.jp/gacha/list')
    assert gacha_data['data']['legend']['lineup']
    return gacha_data


def get_normal_shabi_info(gbf_sim, gacha):
    shabi_info_gacha = {}
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
        shabi_info_gacha[sub_gacha['id']] = sub_gacha

        print(f'必得【{sub_gacha["name"]}({sub_gacha["id"]})】数据读取完成')

    return shabi_info_gacha


def get_gacha_info(gbf_sim, gacha_id, page_num):
    gacha_info = gbf_sim.get(f'https://game.granbluefantasy.jp/gacha/provision_ratio/legend/{gacha_id}/{page_num}')
    if gacha_info['status_code'] == 500:
        return None
    assert len(gacha_info['data']['ratio']) == 1
    return gacha_info['data']['appear']


def get_choice_shabi_info(gbf_sim, gacha):
    assert len(gacha["campaign_gacha_ids"]) == 1
    choice_shabi = gacha["campaign_gacha_ids"][0]

    payload = json.dumps({
        "special_token": None,
        "campaign_id": gacha['campaign_id'],
        "list_kind": 1,
        "filter": {},
        "is_new": False
    })

    gacha_info = gbf_sim.post(f'https://game.granbluefantasy.jp/rest/gacha/starlegend/choice/lineup_master',
                              data_text=payload)
    item_list = []
    for sub_list in gacha_info['data']['list']:
        for item in sub_list:
            item_list.append(item)
    choice_shabi['list'] = item_list
    return {
        gacha["campaign_gacha_ids"][0]["id"]: choice_shabi
    }


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
            '{{记录项目',
            f'|id={sub_gacha_info["id"]}',
            f'|name={sub_gacha_info["name"]}',
            f'|banner={sub_gacha_info["payment_image"]}',
            f'|icon={sub_gacha_info["text_btn_image"]}',
        ]
        if shabi['is_choice']:
            sub_gacha_text_array.extend(get_choice_shabi_content(sub_gacha_info))
        else:
            sub_gacha_text_array.extend(get_normal_shabi_content(sub_gacha_info))
        gacha_text_array.append('|' + ''.join(sub_gacha_text_array))
        gacha_text_array.append('}}')

    content_array = [
        '{{必得记录',
        f'|id={shabi["id"]}',
        f'|name={shabi["name"]}',
        f'|start={shabi["start"].replace("/", "-")}',
        f'|end={shabi["end"].replace("/", "-")}',
        f'|image_path={shabi["image_path"]}',
        f'|is_choice=1' if shabi['is_choice'] else '',
        '|gacha={{记录列表',
        '\n'.join(gacha_text_array),
        '}}',
        '}}'
    ]

    return '\n'.join(content_array)


def get_normal_shabi_content(sub_gacha_info):
    sub_gacha_text_array = []
    for category_info in sub_gacha_info['list']:
        if category_info['category'] == 0:
            category_name = 'weapon'
        elif category_info['category'] == 2:
            category_name = 'summon'
        else:
            raise Exception(f'预料外的抽奖类型：{category_info["category"]}')
        sub_gacha_text_array.append(
            f'|{category_name}={",".join([str(item["reward_id"]) for item in category_info["item"]])}')
    # sub_gacha_text_array.append('}}')

    return sub_gacha_text_array


def get_choice_shabi_content(sub_gacha_info):
    sub_gacha_text_array = ['|is_choice=1']

    weapon_id_list = []
    summon_id_list = []

    for item in sub_gacha_info['list']:
        if str(item['item_id'])[0] == '1':
            weapon_id_list.append(str(item['item_id']))
        elif str(item['item_id'])[0] == '2':
            summon_id_list.append(str(item['item_id']))

    if len(weapon_id_list) > 0:
        sub_gacha_text_array.append(f'|weapon={",".join(weapon_id_list)}')
    if len(summon_id_list) > 0:
        sub_gacha_text_array.append(f'|summon={",".join(summon_id_list)}')

    return sub_gacha_text_array
