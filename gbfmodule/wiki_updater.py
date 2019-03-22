import os
from huijiWiki import HuijiWiki
from danteng_lib import log, read_file, load_json
from config import WIKITEXT_SYNC_PATH, DATA_PATH
from .data.sim import GBFSim


def gbf_wiki_page_updater(cfg, args):
    cfg['wiki'] = HuijiWiki('gbf')
    # 登录wiki
    if not cfg['wiki'].login(cfg['WIKI']['username'], cfg['WIKI']['password']):
        raise Exception('登录WIKI失败，请稍后再试')
    if not cfg['wiki'].get_edit_token():
        raise Exception('获取TOKEN失败，请稍后再试')

    if args.command == 'all':
        pass
    elif args.command == 'summon':
        update_summon_page(cfg, args)
    else:
        print('错误的指令')


def update_summon_page(cfg, args):
    gbf_sim = GBFSim(cfg)

    for summon_id in gbf_sim.all_summon():
        page_title = f'Summon/{summon_id}'
        page_content = new_summon_page(summon_id)

        wikitext_sync_file_path = os.path.join(WIKITEXT_SYNC_PATH, HuijiWiki.filename_fix(f'{page_title}.txt'))
        wikitext_sync_file_content, read_result = read_file(wikitext_sync_file_path)

        # 文件不存在时才更新服务器
        if not read_result:
            cfg['wiki'].edit(page_title, page_content)

        # 不管文件是否存在，都会更新本地缓存，方便手工补充
        if wikitext_sync_file_content.strip() != page_content.strip():
            with open(wikitext_sync_file_path, 'w', encoding='UTF-8') as f:
                f.write(page_content)

    cfg['wiki'].wait_threads()


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
    main_aura_text = [note_data_jp["skill"]["comment"]]
    if uncap_data_jp:
        main_aura_text.append('<br><br>{{Evo|3}} ' + uncap_data_jp["skill"]["comment"])
    if final_uncap_data_jp:
        main_aura_text.append('<br>{{Evo|4}} ' + final_uncap_data_jp["skill"]["comment"])

    sub_aura_text = []
    has_sub = False
    if 'sub_skill' in note_data_jp:
        has_sub = True
        sub_aura_text.append(note_data_jp["sub_skill"]["comment"])
        if uncap_data_jp:
            sub_aura_text.append('<br><br>{{Evo|3}} ' + uncap_data_jp["sub_skill"]["comment"])
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
