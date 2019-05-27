import os
from huijiWikiTabx import HuijiWikiTabx
from config import WIKITEXT_PATH
from pyvar_to_lua import pyvar_to_lua


def update_leader_auto_db(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["leader"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    item_db_auto = {}
    item_replace_map = {}

    for item_id, item_info in item_tabx.get_all_data().items():
        if item_id == 0:
            continue
        if item_info['category'] == 0:
            continue
        item_db_auto[item_id] = item_info['name_chs']

        item_replace_map[item_info['name_chs']] = item_id
        for nickname in item_info['nickname']:
            item_replace_map[nickname] = item_id

    output = []

    output.append('----------------------------------------------')
    output.append('-- 本文件由机器人自动维护，请勿手工修改')
    output.append('-- 内容来源：[[Data:主角.tabx]]')
    output.append('----------------------------------------------')
    output.append('')
    output.append('local p = {}')
    output.append('')
    output.append('p.replace = ' + pyvar_to_lua(item_replace_map).dump_to_luatable())
    output.append('')
    output.append('p.db = ' + pyvar_to_lua(item_db_auto).dump_to_luatable())
    output.append('')
    output.append('return p')

    page_title = 'Module:Leader/AutoDB'
    page_content = '\n'.join(output)

    wikitext_file_path = os.path.join(WIKITEXT_PATH, gbf_wiki.filename_fix(f'{page_title}.txt'))

    gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()
