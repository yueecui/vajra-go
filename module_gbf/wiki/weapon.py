import os
import time
import re
from module_huiji.huijiWiki import HuijiWiki
from module_huiji.huijiWikiTabx import HuijiWikiTabx
from module_huiji.danteng_lib import log, read_file, load_json
from config import WIKITEXT_PATH, WIKITEXT_SYNC_PATH, DATA_PATH, SKIP_WEAPON_ID_LIST_PATH, ELEMENT_JP_TO_CHS
from module_huiji.pyvar_to_lua import pyvar_to_lua


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
        log('[[%s.tabx]]没有修改。' % cfg["TABX"]["weapon"])


def generate_weapon_row(weapon_id):
    # 召唤石图鉴数据
    shop_data_jp = load_json(os.path.join(DATA_PATH, 'weapon', 'shop', f'{weapon_id}.json'))['data']
    shop_data_en = load_json(os.path.join(DATA_PATH, 'weapon', 'shop_en', f'{weapon_id}.json'))['data']
    # 图鉴数据可能不存在（例如活动武器之类的）
    note_data_jp = load_json(os.path.join(DATA_PATH, 'weapon', 'note', f'{weapon_id}.json'))
    if note_data_jp is not None:
        note_data_jp = note_data_jp['data']

    temp_row = {
        'name_jp': shop_data_jp['name'],
        'title_jp': '',
        'series_name': '',
        'name_en': shop_data_en['name'],
        'name_chs': '',
        'tag_title': '',
        'nickname': [],
        'search_nickname': [],
        'element': note_data_jp is None and -1 or int(
            note_data_jp.get('attribute') or note_data_jp.get('element') or -1),
        'kind': int(shop_data_jp['kind']),
        'rarity': int(shop_data_jp['rarity']),
        'category': '',
        'tag': [],
        'release_date': time.strftime("##%Y-%m-%d", time.localtime()),
        'star4_date': '',
        'star5_date': '',
        'unlock_char': 0,
        'link_enwiki': '',
        'link_gamewith': 0,
        'link_jpwiki': '',
        'link_kamigame': '',
        'user_level': -1,
        'max_hp': int(shop_data_jp['max_hp']),
        'max_atk': int(shop_data_jp['max_attack']),
        'evo4_hp': 0,
        'evo4_atk': 0,
        'evo5_hp': 0,
        'evo5_atk': 0,
        'base_evo': 3,
        'max_evo': 3,
        'is_archaic': False,
        'sk_icon': [],
        'sk_name': [],
    }

    if note_data_jp is not None:
        for skill_key in ['skill1', 'skill2', 'skill3']:
            if skill_key in note_data_jp and not (note_data_jp[skill_key] is None):
                temp_row['sk_icon'].append(note_data_jp[skill_key]['image'].strip())
                temp_row['sk_name'].append(note_data_jp[skill_key]['name'].strip())
    else:
        if 'skill' in shop_data_jp:
            for index in ['1', '2', '3']:
                if index in shop_data_jp['skill'] and type(shop_data_jp['skill'][index]) != list:
                    temp_row['sk_name'].append(shop_data_jp['skill'][index]['name'].strip())

        # for key in ['skill1', 'skill2', 'skill3']:
        #     if key in shop_data_jp and 'name' in shop_data_jp[key]:
        #         temp_row['sk_name'].append(shop_data_jp[key]['name'].strip())

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
        if int(weapon_id) != 1040619900:
            continue
        if int(weapon_id) in skip_weapon_id_list:
            continue
        page_title = f'Weapon/{weapon_id}'
        page_content = new_weapon_page(weapon_id)

        wikitext_sync_file_path = os.path.join(WIKITEXT_SYNC_PATH, HuijiWiki.filename_fix(f'{page_title}.txt'))
        wikitext_sync_file_content, read_result = read_file(wikitext_sync_file_path)

        # 文件不存在时
        if not read_result:
            # 先尝试从服务器拉取
            gbf_wiki.raw(page_title)
            gbf_wiki.wait_threads()
            result = gbf_wiki.get_result_rawtextlist()

            if not result.get(page_title):
                # 如果没有才更新服务器
                gbf_wiki.edit(page_title, page_content)
                gbf_wiki.wait_threads()

        # 不管文件是否存在，都会更新本地缓存，方便手工补充
        if wikitext_sync_file_content.strip() != page_content.strip():
            with open(wikitext_sync_file_path, 'w', encoding='UTF-8') as f:
                f.write(page_content)


def new_weapon_page(weapon_id):
    page_content_rows = list()

    # 召唤石图鉴数据
    shop_data_jp = load_json(os.path.join(DATA_PATH, 'weapon', 'shop', f'{weapon_id}.json'))['data']
    shop_data_en = load_json(os.path.join(DATA_PATH, 'weapon', 'shop_en', f'{weapon_id}.json'))['data']

    note_data_jp = load_json(os.path.join(DATA_PATH, 'weapon', 'note', f'{weapon_id}.json'))
    if note_data_jp is not None:
        note_data_jp = note_data_jp['data']

    if not shop_data_jp:
        raise Exception(f'武器{weapon_id}的日文数据文件未找到')
    if not shop_data_en:
        raise Exception(f'武器{weapon_id}的英文数据文件未找到')

    page_content_rows.append('{{武器信息')
    page_content_rows.append('|背景日文=')
    page_content_rows.append('|背景英文=')
    page_content_rows.append('|背景中文=')
    page_content_rows.append('}}')
    page_content_rows.append('')

    # 替换奥义文本
    charge_attack_find = re.findall(r'(.+?)属性ダメージ\(.+?\)(.*)', shop_data_jp['special_skill']['comment'])

    if charge_attack_find:
        charge_text = charge_attack_find[0][0]
        if charge_text == '武器':
            charge_text = '未知'
        if charge_text in ELEMENT_JP_TO_CHS:
            charge_text = f'对敌方单体造成{ELEMENT_JP_TO_CHS[charge_text]}属性伤害'
        else:
            charge_text = f'对敌方单体造成{charge_text}属性伤害'

        if charge_attack_find[0][1] != '':
            extra_text = charge_attack_find[0][1]
            if extra_text[0:1] == '/':
                extra_text = extra_text[1:]
            charge_text += '<br><br>' + extra_text

            page_content_rows.append('{{待整理}}')
            page_content_rows.append('')
    else:
        charge_text = ''

    # 奥义
    page_content_rows.append('==奥义==')
    page_content_rows.append('')
    page_content_rows.append('{{武器奥义|s}}')
    page_content_rows.append('{{武器奥义')
    page_content_rows.append('|name=' + shop_data_jp["special_skill"]["name"])
    page_content_rows.append('|name_chs=')
    page_content_rows.append('|desc=' + charge_text)
    page_content_rows.append('|tag=')
    page_content_rows.append('}}')
    page_content_rows.append('{{武器奥义|e}}')
    page_content_rows.append('')

    # 技能
    skill_data = note_data_jp is None and shop_data_jp or note_data_jp
    if '1' in skill_data['skill'] is not None and type(skill_data['skill']['1']) != list:
        page_content_rows.append('==技能==')
        page_content_rows.append('')
        page_content_rows.append('{{武器技能|s}}')
        page_content_rows.append('{{武器技能')
        page_content_rows.append('|name=' + skill_data['skill']['1']["name"])
        page_content_rows.append('|name_chs=')
        if skill_data['skill']['1']['masterable_level'] != '1':
            page_content_rows.append('|learn=' + skill_data['skill']['1']['masterable_level'])
        page_content_rows.append('|icon=' + ('image' in skill_data['skill']['1'] and skill_data['skill']['1']['image'] or ''))
        page_content_rows.append('|desc=' + skill_data['skill']['1']["comment"])
        page_content_rows.append('|use_desc=no')
        page_content_rows.append('|tag=')
        page_content_rows.append('}}')

        if '2' in skill_data['skill'] is not None and type(skill_data['skill']['2']) != list:
            page_content_rows.append('{{武器技能')
            page_content_rows.append('|name=' + skill_data['skill']['2']["name"])
            page_content_rows.append('|name_chs=')
            if skill_data['skill']['2']['masterable_level'] != '1':
                page_content_rows.append('|learn=' + skill_data['skill']['2']['masterable_level'])
            page_content_rows.append(
                '|icon=' + ('image' in skill_data['skill']['2'] and skill_data['skill']['2']['image'] or ''))
            page_content_rows.append('|desc=' + skill_data['skill']['2']["comment"])
            page_content_rows.append('|use_desc=no')
            page_content_rows.append('|tag=')
            page_content_rows.append('}}')

        if '3' in skill_data['skill'] is not None and type(skill_data['skill']['3']) != list:
            page_content_rows.append('{{武器技能')
            page_content_rows.append('|name=' + skill_data['skill']['3']["name"])
            page_content_rows.append('|name_chs=')
            if skill_data['skill']['3']['masterable_level'] != '1':
                page_content_rows.append('|learn=' + skill_data['skill']['3']['masterable_level'])
            page_content_rows.append(
                '|icon=' + ('image' in skill_data['skill']['3'] and skill_data['skill']['3']['image'] or ''))
            page_content_rows.append('|desc=' + skill_data['skill']['3']["comment"])
            page_content_rows.append('|use_desc=no')
            page_content_rows.append('|tag=')
            page_content_rows.append('}}')

        page_content_rows.append('{{武器技能|e}}')
        page_content_rows.append('')

    page_content_rows.append('{{武器信息|结束}}')

    return '\n'.join(page_content_rows)


def update_weapon_auto_db(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["weapon"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    item_db_auto = {}

    for item_id, item_info in item_tabx.get_all_data().items():
        if item_id == 0:
            continue
        item_db_auto[item_id] = item_info['tag_title'] if item_info['tag_title'] else (
            item_info['name_chs'] if item_info['name_chs'] else item_info['name_jp'])

    output = []

    output.append('----------------------------------------------')
    output.append('-- 本文件由机器人自动维护，请勿手工修改')
    output.append('-- 内容来源：[[Data:武器列表.tabx]]')
    output.append('-- 手工添加请访问：[[Module:Util/LinkNickname]]')
    output.append('----------------------------------------------')
    output.append('')
    output.append('local p = {}')
    output.append('')
    output.append('p.db = ' + pyvar_to_lua(item_db_auto).dump_to_luatable())
    output.append('')
    output.append('return p')

    page_title = 'Module:Weapon/AutoDB'
    page_content = '\n'.join(output)

    wikitext_file_path = os.path.join(WIKITEXT_PATH, gbf_wiki.filename_fix(f'{page_title}.txt'))

    gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()
