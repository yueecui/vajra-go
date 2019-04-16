import os
import time
import re
from huijiWiki import HuijiWiki
from huijiWikiTabx import HuijiWikiTabx
from danteng_lib import log, read_file, load_json
from config import WIKITEXT_SYNC_PATH, DATA_PATH, SKIP_WEAPON_ID_LIST_PATH, ELEMENT_JP_TO_CHS


def update_weapon_tabx(cfg, args):
    gbf_sim = cfg['sim']
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["weapon"]}.tabx'

    skip_weapon_id_list = get_skip_weapon_id_list()

    weapon_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    tabx_mod = False

    for weapon_id in gbf_sim.all_weapon():
        weapon_id = int(weapon_id)
        if weapon_id in skip_weapon_id_list:
            continue
        if not weapon_tabx.has_key(weapon_id):
            weapon_tabx.mod_row(weapon_id, generate_weapon_row(weapon_id))
            tabx_mod = True

    # 保存
    if tabx_mod:
        weapon_tabx.save()
    else:
        log('[[%s]]没有修改。' % cfg["TABX"]["summon"])


def generate_weapon_row(weapon_id):
    # 召唤石图鉴数据
    note_data_jp = load_json(os.path.join(DATA_PATH, 'weapon', 'jp', f'{weapon_id}.json'))
    note_data_en = load_json(os.path.join(DATA_PATH, 'weapon', 'en', f'{weapon_id}.json'))

    temp_row = {
        'name_jp': note_data_jp['name'],
        'title_jp': '',
        'series_name': note_data_jp['series_name'],
        'name_en': note_data_en['name'],
        'name_chs': '',
        'nickname': [],
        'search_nickname': [],
        'element': int(note_data_jp['attribute']),
        'kind': int(note_data_jp['kind']),
        'rarity': int(note_data_jp['rarity']),
        'category': '',
        'tag': [],
        'release_date': time.strftime("##%Y-%m-%d", time.localtime()),
        'star4_date': '',
        'star5_date': '',
        'link_enwiki': '',
        'link_gamewith': 0,
        'link_jpwiki': '',
        'link_kamigame': '',
        'user_level': int(note_data_jp['user_level']),
        'max_hp': int(note_data_jp['max_hp']),
        'max_atk': int(note_data_jp['max_attack']),
        'evo4_hp': 0,
        'evo4_atk': 0,
        'evo5_hp': 0,
        'evo5_atk': 0,
        'base_evo': 3,
        'max_evo': 3,
        'is_archaic': False,
    }

    return temp_row


def get_skip_weapon_id_list():
    content, result = read_file(SKIP_WEAPON_ID_LIST_PATH)
    if not result:
        return []
    else:
        raw_list = content.split('\n')
        skip_id_list = []
        for skip_id_text in raw_list:
            skip_id_text = skip_id_text.strip()
            if skip_id_text == '':
                continue
            if skip_id_text[0:1] == '#':
                continue
            try:
                skip_id_list.append(int(skip_id_text))
            except ValueError:
                continue
        return skip_id_list


def update_weapon_page(cfg, args):
    gbf_sim = cfg['sim']
    gbf_wiki = cfg['wiki']

    skip_weapon_id_list = get_skip_weapon_id_list()

    for weapon_id in gbf_sim.all_weapon():
        if int(weapon_id) in skip_weapon_id_list:
            continue
        page_title = f'Weapon/{weapon_id}'
        page_content = new_weapon_page(weapon_id)

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


def new_weapon_page(weapon_id):
    page_content_rows = list()

    # 召唤石图鉴数据
    note_data_jp = load_json(os.path.join(DATA_PATH, 'weapon', 'jp', f'{weapon_id}.json'))
    note_data_en = load_json(os.path.join(DATA_PATH, 'weapon', 'en', f'{weapon_id}.json'))

    if not note_data_jp:
        raise Exception(f'武器{weapon_id}的日文数据文件未找到')
    if not note_data_en:
        raise Exception(f'武器{weapon_id}的英文数据文件未找到')

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
            page_content_rows.append('{{武器技能')
            page_content_rows.append('|name=' + note_data_jp["skill2"]["name"])
            page_content_rows.append('|name_chs=')
            page_content_rows.append('|icon=' + note_data_jp["skill2"]["image"])
            page_content_rows.append('|desc=' + note_data_jp["skill2"]["comment"])
            page_content_rows.append('|use_desc=no')
            page_content_rows.append('|tag=')
            page_content_rows.append('}}')

        if 'skill3' in note_data_jp and note_data_jp['skill3']:
            page_content_rows.append('{{武器技能')
            page_content_rows.append('|name=' + note_data_jp["skill3"]["name"])
            page_content_rows.append('|name_chs=')
            page_content_rows.append('|icon=' + note_data_jp["skill3"]["image"])
            page_content_rows.append('|desc=' + note_data_jp["skill3"]["comment"])
            page_content_rows.append('|use_desc=no')
            page_content_rows.append('|tag=')
            page_content_rows.append('}}')

        page_content_rows.append('{{武器技能|e}}')
        page_content_rows.append('')

    page_content_rows.append('{{武器信息|结束}}')

    return '\n'.join(page_content_rows)
