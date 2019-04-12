import os
import time
import re
from huijiWiki import HuijiWiki
from huijiWikiTabx import HuijiWikiTabx
from danteng_lib import log, read_file, load_json
from config import WIKITEXT_SYNC_PATH, DATA_PATH, SKIP_SUMMON_ID_LIST_PATH, SKIP_WEAPON_ID_LIST_PATH, ELEMENT_JP_TO_CHS
from .data.sim import GBFSim


def gbf_wiki_page_updater(cfg, args):
    cfg['wiki'] = HuijiWiki('gbf')
    cfg['sim'] = GBFSim(cfg)
    # 登录wiki
    if not cfg['wiki'].login(cfg['WIKI']['username'], cfg['WIKI']['password']):
        raise Exception('登录WIKI失败，请稍后再试')
    if not cfg['wiki'].get_edit_token():
        raise Exception('获取TOKEN失败，请稍后再试')

    if args.command == 'all':
        update_weapon_tabx(cfg, args)
        update_weapon_page(cfg, args)
        update_summon_tabx(cfg, args)
        update_summon_page(cfg, args)
    elif args.command == 'summon':
        update_summon_tabx(cfg, args)
        update_summon_page(cfg, args)
    elif args.command == 'weapon':
        update_weapon_tabx(cfg, args)
        update_weapon_page(cfg, args)
    else:
        print('错误的指令')


def update_summon_tabx(cfg, args):
    gbf_sim = cfg['sim']
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["summon"]}.tabx'

    skip_summon_id_list = get_skip_summon_id_list()

    summon_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    tabx_mod = False

    for summon_id in gbf_sim.all_summon():
        summon_id = int(summon_id)
        if summon_id in skip_summon_id_list:
            continue
        if not summon_tabx.has_key(summon_id):
            summon_tabx.mod_row(summon_id, generate_summon_row(summon_id))
            tabx_mod = True

    # 保存
    if tabx_mod:
        summon_tabx.save()
    else:
        log('[[%s]]没有修改。' % cfg["TABX"]["summon"])


def generate_summon_row(summon_id):
    # 召唤石图鉴数据
    note_data_jp = load_json(os.path.join(DATA_PATH, 'summon', 'jp', f'{summon_id}.json'))
    note_data_en = load_json(os.path.join(DATA_PATH, 'summon', 'en', f'{summon_id}.json'))

    temp_row = {
        'name_jp': note_data_jp['name'],
        'series_name': note_data_jp['series_name'],
        'name_en': note_data_en['name'],
        'name_chs': '',
        'nickname': [],
        'search_nickname': [],
        'element': int(note_data_jp['attribute']),
        'rarity': int(note_data_jp['rarity']),
        'category': '',
        'tag': [],
        'is_free': False,
        'mypage': False,
        'skill_name_jp': '',
        'skill_prefix_jp': '',
        'skill_suffix_jp': '',
        'skill_name_en': '',
        'skill_prefix_en': '',
        'skill_suffix_en': '',
        'skill_name_cn': '',
        'skill_prefix_cn': '',
        'skill_suffix_cn': '',
        'link_enwiki': '',
        'link_gamewith': 0,
        'link_jpwiki': '',
        'link_kamigame': '',
        'uncap_img': [],
        'summon_id': 0,
        'tribe_id': 0,
        'release_date': time.strftime("##%Y-%m-%d", time.localtime()),
        'star4_date': '',
        'star5_date': '',
        'max_hp': 0,
        'max_atk': 0,
        'evo4_hp': 0,
        'evo4_atk': 0,
        'evo5_hp': 0,
        'evo5_atk': 0,
        'base_evo': 3,
        'max_evo': 3,
        'cv': note_data_jp['voice_acter'].split(' '),
        'has_sub_skill': 'sub_skill' in note_data_jp,
        'not_in_note': False,
        'no_combo_first': False,
    }

    uncap_data_jp = load_json(os.path.join(DATA_PATH, 'summon', 'uncap', f'{summon_id}.json'))
    if uncap_data_jp:
        temp_row.update({
            'skill_name_jp': uncap_data_jp['special_skill']['name'],
            'skill_prefix_jp': uncap_data_jp['special_skill']['coalescence_name1'],
            'skill_suffix_jp': uncap_data_jp['special_skill']['coalescence_name2'],
            'skill_name_en': uncap_data_jp['special_skill']['name_en'].strip(),
            'skill_prefix_en': uncap_data_jp['special_skill']['coalescence_name1_en'].strip(),
            'skill_suffix_en': uncap_data_jp['special_skill']['coalescence_name2_en'].strip(),
            'summon_id': int(uncap_data_jp['master']['summon_id']),
            'tribe_id': int(uncap_data_jp['master']['tribe']),
            'max_hp': int(uncap_data_jp['param']['hp']),
            'max_atk': int(uncap_data_jp['param']['attack']),
        })

    final_uncap_data_jp = load_json(os.path.join(DATA_PATH, 'summon', 'final_uncap', f'{summon_id}.json'))
    if final_uncap_data_jp:
        temp_row.update({
            'evo4_hp': int(final_uncap_data_jp['param']['hp']),
            'evo4_atk': int(final_uncap_data_jp['param']['attack']),
            'max_evo': 4,
        })

    return temp_row


def get_skip_summon_id_list():
    content, result = read_file(SKIP_SUMMON_ID_LIST_PATH)
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


def update_summon_page(cfg, args):
    gbf_sim = cfg['sim']
    gbf_wiki = cfg['wiki']

    skip_summon_id_list = get_skip_summon_id_list()

    for summon_id in gbf_sim.all_summon():
        if int(summon_id) in skip_summon_id_list:
            continue
        page_title = f'Summon/{summon_id}'
        page_content = new_summon_page(summon_id)

        wikitext_sync_file_path = os.path.join(WIKITEXT_SYNC_PATH, HuijiWiki.filename_fix(f'{page_title}.txt'))
        wikitext_sync_file_content, read_result = read_file(wikitext_sync_file_path)

        # 文件不存在时才更新服务器
        if not read_result:
            gbf_wiki.edit(page_title, page_content)
            gbf_wiki.wait_threads()

        # 不管文件是否存在，都会更新本地缓存，方便手工补充
        if wikitext_sync_file_content.strip() != page_content.strip():
            with open(wikitext_sync_file_path, 'w', encoding='UTF-8') as f:
                f.write(page_content)


def new_summon_page(summon_id):
    page_content_rows = list()

    # 召唤石图鉴数据
    note_data_jp = load_json(os.path.join(DATA_PATH, 'summon', 'jp', f'{summon_id}.json'))
    note_data_en = load_json(os.path.join(DATA_PATH, 'summon', 'en', f'{summon_id}.json'))
    uncap_data_jp = load_json(os.path.join(DATA_PATH, 'summon', 'uncap', f'{summon_id}.json'))
    final_uncap_data_jp = load_json(os.path.join(DATA_PATH, 'summon', 'final_uncap', f'{summon_id}.json'))
    if not note_data_jp:
        raise Exception(f'召唤石{summon_id}的日文数据文件未找到')
    if not note_data_en:
        raise Exception(f'召唤石{summon_id}的英文数据文件未找到')

    page_content_rows.append('{{召唤石信息')
    page_content_rows.append('|背景日文=' + note_data_jp['comment'])
    page_content_rows.append('|背景英文=' + note_data_en['comment'])
    page_content_rows.append('|背景中文=')
    page_content_rows.append('}}')
    page_content_rows.append('')

    page_content_rows.append('{{待整理}}')
    page_content_rows.append('')

    # 主动技能文本
    special_skill_text = [note_data_jp["special_skill"]["comment"]]
    if uncap_data_jp:
        special_skill_text.append('<br><br>{{Evo|3}} ' + uncap_data_jp["special_skill"]["comment"])
    if final_uncap_data_jp:
        special_skill_text.append('<br>{{Evo|4}} ' + final_uncap_data_jp["special_skill"]["comment"])

    cd_text = []
    if 'start_recast' in note_data_jp["special_skill"] and note_data_jp["special_skill"]['start_recast'] != '':
        cd_text.append('{{CD|初次}} ' + note_data_jp["special_skill"]['start_recast'] + '回合')
    if 'recast' in note_data_jp["special_skill"] and note_data_jp["special_skill"]['recast'] != '':
        cd_text.append(note_data_jp["special_skill"]['recast'] + '回合')

    page_content_rows.append(f'=={{{{召唤石标题|召唤|{note_data_jp["special_skill"]["name"]}}}}}==')
    page_content_rows.append('')
    page_content_rows.append('{{召唤主动')
    page_content_rows.append('|name=' + note_data_jp["special_skill"]["name"])
    page_content_rows.append('|name_chs=')
    page_content_rows.append('|cd=' + '<br>'.join(cd_text))
    page_content_rows.append('|desc=' + ''.join(special_skill_text))
    page_content_rows.append('|tag=')
    page_content_rows.append('}}')
    page_content_rows.append('')

    # 主加护文本
    main_aura_text = ['{{Evo|0}} ' + note_data_jp["skill"]["comment"]]
    if uncap_data_jp:
        main_aura_text.append('<br>{{Evo|3}} ' + uncap_data_jp["skill"]["comment"])
    if final_uncap_data_jp:
        main_aura_text.append('<br>{{Evo|4}} ' + final_uncap_data_jp["skill"]["comment"])

    sub_aura_text = []
    has_sub = False
    if 'sub_skill' in note_data_jp:
        has_sub = True
        sub_aura_text.append('{{Evo|0}} ' + note_data_jp["sub_skill"]["comment"])
        if uncap_data_jp:
            sub_aura_text.append('<br>{{Evo|3}} ' + uncap_data_jp["sub_skill"]["comment"])
        if final_uncap_data_jp:
            sub_aura_text.append('<br>{{Evo|4}} ' + final_uncap_data_jp["sub_skill"]["comment"])

    page_content_rows.append(f'=={{{{召唤石标题|加护|{note_data_jp["skill"]["name"]}}}}}==')
    page_content_rows.append('')

    if has_sub:
        page_content_rows.append('===主召时===')

    page_content_rows.append('{{召唤加护')
    page_content_rows.append('|name=' + note_data_jp["skill"]["name"])
    page_content_rows.append('|name_chs=')
    page_content_rows.append('|desc=' + ''.join(main_aura_text))
    page_content_rows.append('|tag=')
    page_content_rows.append('}}')
    page_content_rows.append('')

    if has_sub:
        page_content_rows.append('===副召时===')

        page_content_rows.append('{{召唤加护')
        page_content_rows.append('|name=' + note_data_jp["skill"]["name"])
        page_content_rows.append('|name_chs=')
        page_content_rows.append('|desc=' + ''.join(sub_aura_text))
        page_content_rows.append('|tag=')
        page_content_rows.append('}}')
        page_content_rows.append('')

    page_content_rows.append('{{召唤石信息|结束}}')

    return '\n'.join(page_content_rows)


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
