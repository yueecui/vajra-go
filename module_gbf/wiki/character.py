import os
from module_huiji.huijiWikiTabx import HuijiWikiTabx
from config import WIKITEXT_PATH
from module_huiji.pyvar_to_lua import pyvar_to_lua


def update_character_auto_db(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["character"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    item_db_auto = {}

    for item_id, item_info in item_tabx.get_all_data().items():
        if item_id == 0:
            continue
        item_db_auto[item_id] = item_info['tag_title'] if item_info['tag_title'] else (item_info['name_chs'] if item_info['name_chs'] else item_info['name_jp'])

    output = []

    output.append('----------------------------------------------')
    output.append('-- 本文件由机器人自动维护，请勿手工修改')
    output.append('-- 内容来源：[[Data:角色列表.tabx]]')
    output.append('-- 手工添加请访问：[[Module:Util/LinkNickname]]')
    output.append('----------------------------------------------')
    output.append('')
    output.append('local p = {}')
    output.append('')
    output.append('p.db = ' + pyvar_to_lua(item_db_auto).dump_to_luatable())
    output.append('')
    output.append('return p')

    page_title = 'Module:Character/AutoDB'
    page_content = '\n'.join(output)

    wikitext_file_path = os.path.join(WIKITEXT_PATH, gbf_wiki.filename_fix(f'{page_title}.txt'))

    gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()
