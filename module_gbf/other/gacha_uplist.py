import json

from module_huiji.huijiWiki import HuijiWiki
from ..data.sim_v2 import GBFSim
from config import WIKITEXT_PATH
import time
import os


def update_gachauplist(cfg, args):
    # 获取傻必数据
    uplist_list = get_gachauplist_list(cfg)
    if len(uplist_list) == 0:
        print('卡池可能是全up池，也可能普池格式可能有所改动，有问题请联系大橘子（∠・ω ‹ )⌒☆')
    gbf_wiki = login_gbf_wiki(cfg)
    for upitem in uplist_list:
        page_title = get_uplist_title(upitem)
        page_content = get_shabi_content(upitem)
        wikitext_file_path = os.path.join(WIKITEXT_PATH, HuijiWiki.filename_fix(f'{page_title}.txt'))
        gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()


def get_gachauplist_list(cfg):
    gbf_sim = GBFSim(cfg)
    gacha_data = get_gacha_data(gbf_sim)
    uplist_list = []
    for gacha in gacha_data['data']['legend']['lineup']:
        if gacha['class_name'] == 'prt-title-legend10':
            jiangchi_info = {
                'id': gacha['id'],
                'name': gacha['name'],
                'start': gacha['service_start'],
                'end': gacha['service_end'],
                'image_path': gacha['image_path'],
                'gacha': {}
            }
            gacha_info = get_gacha_info(gbf_sim, jiangchi_info['id'], 1)
            write_json_file(gacha_info, jiangchi_info)
            tianjing_list=get_tianjing_info(gbf_sim)
            jiangchi_info['gacha']['item']=tianjing_list

            print(f'卡池数据读取完成')

            uplist_list.append(jiangchi_info)

    return uplist_list


def get_gacha_data(gbf_sim):
    gacha_data = gbf_sim.get('https://game.granbluefantasy.jp/gacha/list')
    assert gacha_data['data']['legend']['lineup']
    return gacha_data


def get_gacha_info(gbf_sim, gacha_id, page_num):
    gacha_info = gbf_sim.get(f'https://game.granbluefantasy.jp/gacha/provision_ratio/legend/{gacha_id}/{page_num}')
    if gacha_info['status_code'] == 500:
        return None
    assert len(gacha_info['data']['ratio']) == 3
    return gacha_info['data']['appear']


def login_gbf_wiki(cfg):
    gbf_wiki = HuijiWiki('gbf')
    # 登录wiki
    if not gbf_wiki.login(cfg['WIKI']['username'], cfg['WIKI']['password']):
        raise Exception('登录WIKI失败，请稍后再试')
    if not gbf_wiki.get_edit_token():
        raise Exception('获取TOKEN失败，请稍后再试')
    return gbf_wiki


def get_uplist_title(item):
    start_time = time.strptime(item['start'], "%Y/%m/%d %H:%M")
    return f'卡池记录/{time.strftime("%Y/%m%d", start_time)}'


def get_shabi_content(shabi):
    gacha_text_array = []
    sub_gacha_info = shabi
    sub_gacha_text_array = [
        '{{记录项目',
        f'|id={sub_gacha_info["id"]}',
        f'|name={"苍光的御印可兑换角色"}',
        # f'|banner={sub_gacha_info["payment_image"]}',
        # f'|icon={sub_gacha_info["text_btn_image"]}',
    ]
    category_name = {
        'weapon': [],
        'summon': [],
    }
    for category_info in sub_gacha_info['gacha']['item']:
        if category_info['item_kind'] == 1:
            category_name['weapon'].append(category_info['item_id'])
        elif category_info['item_kind'] == 2:
            category_name['summon'].append(category_info['item_id'])
        else:
            raise Exception(f'预料外的抽奖类型：{category_info["item_kind"]}')
    # print(f'category_name={category_name}')
    if len(category_name['weapon']) > 0:
        sub_gacha_text_array.append(
            f'|weapon={",".join(category_name["weapon"])}')
    if len(category_name['summon']) > 0:
        sub_gacha_text_array.append(
            f'|summon={",".join(category_name["summon"])}')
    sub_gacha_text_array.append('}}')
    gacha_text_array.append('|' + ''.join(sub_gacha_text_array))


    content_array = [
        '{{卡池记录',
        f'|id={shabi["id"]}',
        f'|name={shabi["name"]}',
        f'|start={shabi["start"].replace("/", "-")}',
        f'|end={shabi["end"].replace("/", "-")}',
        f'|image_path={shabi["image_path"]}',
        '|gacha={{记录列表',
        '\n'.join(gacha_text_array),
        '}}',
        '}}'
    ]

    return '\n'.join(content_array)


def get_tianjing_info(gbf_sim):
    gacha_info = gbf_sim.get(f'https://game.granbluefantasy.jp/gacha/ceiling_list')
    if gacha_info['status_code'] == 500:
        return None
    return gacha_info['data']['list']


def write_json_file(data, list):
    title = get_uplist_title(list)
    HuijiWiki.filename_fix(f'{title}.txt')
    # file_path=f'{WIKITEXT_PATH}/{title}.json'
    # file = json.dumps(data, indent=4, ensure_ascii=False)

