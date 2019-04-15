import os
import time
import re
from huijiWiki import HuijiWiki
from huijiWikiTabx import HuijiWikiTabx
from danteng_lib import log, read_file, load_json
from config import WIKITEXT_SYNC_PATH, DATA_PATH, SKIP_WEAPON_ID_LIST_PATH, ELEMENT_JP_TO_CHS, IMAGE_PATH


item_jp_json_path = r'data\item_jp.json'
item_en_json_path = r'data\item_en.json'


def update_item_tabx(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["item"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    # 从本地json添加新数据
    item_jp_json = load_json(item_jp_json_path)

    for item_info in item_jp_json:
        item_id = int(item_info['item_id'])
        item_tabx.mod_row(item_id, generate_item_row(item_info))

    # 从本地json添加新数据
    item_en_json = load_json(item_en_json_path)

    for item_info in item_en_json:
        item_id = int(item_info['item_id'])
        row_info = item_tabx.get_row(item_id)
        if row_info:
            row_info['name_en'] = item_info['name']
            row_info['comment_en'] = item_info['comment'].replace('\n', '<br>').strip()
        item_tabx.mod_row(item_id, row_info)

    # 从本地图标文件添加空的数据
    # 先检查本地
    item_icon_path = os.path.join(IMAGE_PATH, 'item', 'article_s')
    all_item_icon_list = os.listdir(item_icon_path)
    for sub_path_name in all_item_icon_list:
        name_split = os.path.splitext(sub_path_name)

        if len(name_split) != 2 or name_split[1] != '.jpg':
            continue

        item_id = int(name_split[0])

        if not item_tabx.has_row(item_id):
            item_tabx.mod_row(item_id, generate_item_row(blank_item_row()))

    # 保存
    item_tabx.save()


def generate_item_row(item_info):
    # 召唤石图鉴数据
    temp_row = {
        'name_jp': item_info['name'],
        'name_en': '',
        'name_chs': '',
        'search_nickname': [],
        'seq_id': int(item_info['seq_id']),
        'category_type': item_info['category_type'],
        'comment_jp': item_info['comment'].replace('\n', '<br>').strip(),
        'comment_en': '',
        'comment_chs': '',
    }
    return temp_row


def blank_item_row():
    return {
        'name': '',
        'comment': '',
        'seq_id': 999999,
        'category_type': []
    }


def update_item_page(cfg, args):
    gbf_sim = cfg['sim']
    gbf_wiki = cfg['wiki']

    for item_id in gbf_sim.all_item():
        if int(item_id) in skip_item_id_list:
            continue
        page_title = f'Weapon/{item_id}'
        page_content = new_item_page(item_id)

        wikitext_sync_file_path = os.path.join(WIKITEXT_SYNC_PATH, HuijiWiki.filename_fix(f'{page_title}.txt'))
        wikitext_sync_file_content, read_result = read_file(wikitext_sync_file_path)

        # 文件不存在时才更新服务器
        if not read_result:
            gbf_wiki.edit(page_title, page_content)
            # gbf_wiki.wait_threads()

        # 不管文件是否存在，都会更新本地缓存，方便手工补充
        if wikitext_sync_file_content.strip() != page_content.strip():
            with open(wikitext_sync_file_path, 'w', encoding='UTF-8') as f:
                f.write(page_content)
    gbf_wiki.wait_threads()


def new_item_page(item_id):
    page_content_rows = list()

    # 召唤石图鉴数据
    note_data_jp = load_json(os.path.join(DATA_PATH, 'item', 'jp', f'{item_id}.json'))
    note_data_en = load_json(os.path.join(DATA_PATH, 'item', 'en', f'{item_id}.json'))

    if not note_data_jp:
        raise Exception(f'武器{item_id}的日文数据文件未找到')
    if not note_data_en:
        raise Exception(f'武器{item_id}的英文数据文件未找到')

    page_content_rows.append('{{武器信息')
    page_content_rows.append('|背景日文=' + note_data_jp['comment'])
    page_content_rows.append('|背景英文=' + note_data_en['comment'])
    page_content_rows.append('|背景中文=')
    page_content_rows.append('}}')
    page_content_rows.append('')

    # 替换奥义文本
    charge_attack_find = re.findall(r'(.+?)属性ダメージ\(.+?\)(.*)', note_data_jp['special_skill']['comment'])

    charge_text = charge_attack_find[0][0]
    if charge_text == '武器':
        charge_text = note_data_jp['attribute']
    charge_text = f'对敌方单体造成{ELEMENT_JP_TO_CHS[charge_text]}属性伤害'
    if charge_attack_find[0][1] != '':
        charge_text += '<br><br>' + charge_attack_find[0][1]

        page_content_rows.append('{{待整理}}')
        page_content_rows.append('')

    # 奥义
    page_content_rows.append('==奥义==')
    page_content_rows.append('')
    page_content_rows.append('{{武器奥义|s}}')
    page_content_rows.append('{{武器奥义')
    page_content_rows.append('|name=' + note_data_jp["special_skill"]["name"])
    page_content_rows.append('|name_chs=')
    page_content_rows.append('|desc=' + charge_text)
    page_content_rows.append('|tag=')
    page_content_rows.append('}}')
    page_content_rows.append('{{武器奥义|e}}')
    page_content_rows.append('')

    # 主加护文本
    if 'skill1' in note_data_jp and note_data_jp['skill1']:
        page_content_rows.append('==技能==')
        page_content_rows.append('')
        page_content_rows.append('{{武器技能|s}}')
        page_content_rows.append('{{武器技能')
        page_content_rows.append('|name=' + note_data_jp["skill1"]["name"])
        page_content_rows.append('|name_chs=')
        page_content_rows.append('|icon=' + note_data_jp["skill1"]["image"])
        page_content_rows.append('|desc=' + note_data_jp["skill1"]["comment"])
        page_content_rows.append('|use_desc=no')
        page_content_rows.append('|tag=')
        page_content_rows.append('}}')

        if 'skill2' in note_data_jp and note_data_jp['skill2']:
            page_content_rows.append('')
            page_content_rows.append('{{武器技能')
            page_content_rows.append('|name=' + note_data_jp["skill2"]["name"])
            page_content_rows.append('|name_chs=')
            page_content_rows.append('|icon=' + note_data_jp["skill2"]["image"])
            page_content_rows.append('|desc=' + note_data_jp["skill2"]["comment"])
            page_content_rows.append('|use_desc=no')
            page_content_rows.append('|tag=')
            page_content_rows.append('}}')

        page_content_rows.append('{{武器技能|e}}')
        page_content_rows.append('')

    page_content_rows.append('{{武器信息|结束}}')

    return '\n'.join(page_content_rows)
