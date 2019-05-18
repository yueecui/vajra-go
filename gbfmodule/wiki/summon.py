import os
import time
from huijiWiki import HuijiWiki
from huijiWikiTabx import HuijiWikiTabx
from danteng_lib import log, read_file, load_json
from config import WIKITEXT_PATH, WIKITEXT_SYNC_PATH, DATA_PATH, SKIP_SUMMON_ID_LIST_PATH
from pyvar_to_lua import pyvar_to_lua


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


def update_summon_auto_db(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["summon"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    item_db_auto = {}

    for item_id, item_info in item_tabx.get_all_data().items():
        if item_id == 0:
            continue
        item_db_auto[item_id] = item_info['name_chs'] if item_info['name_chs'] else item_info['name_jp']

    output = []

    output.append('----------------------------------------------')
    output.append('-- 本文件由机器人自动维护，请勿手工修改')
    output.append('-- 内容来源：[[Data:召唤石列表.tabx]]')
    output.append('-- 手工添加请访问：[[Module:Util/LinkNickname]]')
    output.append('----------------------------------------------')
    output.append('')
    output.append('local p = {}')
    output.append('')
    output.append('p.db = ' + pyvar_to_lua(item_db_auto).dump_to_luatable())
    output.append('')
    output.append('return p')

    page_title = 'Module:Summon/AutoDB'
    page_content = '\n'.join(output)

    wikitext_file_path = os.path.join(WIKITEXT_PATH, gbf_wiki.filename_fix(f'{page_title}.txt'))

    gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()
