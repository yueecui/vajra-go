import os
from huijiWikiTabx import HuijiWikiTabx
from config import WIKITEXT_PATH
from pyvar_to_lua import pyvar_to_lua


def update_skin_auto_db(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["skin"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    item_db_auto = {}
    item_replace_map = {}

    for item_id, item_info in item_tabx.get_all_data().items():
        if item_id == 0:
            continue
        item_db_auto[item_id] = item_info['name_chs'] if item_info['name_chs'] else item_info['name_jp']

    output = []

    output.append('----------------------------------------------')
    output.append('-- 本文件由机器人自动维护，请勿手工修改')
    output.append('-- 内容来源：[[Data:皮肤.tabx]]')
    output.append('----------------------------------------------')
    output.append('')
    output.append('local p = {}')
    output.append('')
    output.append('p.db = ' + pyvar_to_lua(item_db_auto).dump_to_luatable())
    output.append('')
    output.append('return p')

    page_title = 'Module:Character/SkinAutoDB'
    page_content = '\n'.join(output)

    wikitext_file_path = os.path.join(WIKITEXT_PATH, gbf_wiki.filename_fix(f'{page_title}.txt'))

    gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()
