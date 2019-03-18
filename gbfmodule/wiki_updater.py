import os
from huijiWiki import HuijiWiki
from huijiWikiTabx import HuijiWikiTabx
from danteng_lib import read_file, log
from config import EXCEL_PATH, WIKITEXT_PATH


def gbf_wiki_tabx_updater(cfg, args):
    cfg['wiki'] = HuijiWiki('gbf')

    if args.command == 'download':
        download_all_tabx(cfg, args)
    elif args.command == 'upload':
        upload_all_tabx(cfg, args)
    else:
        print('错误的指令')


# 下载所有tabx
def download_all_tabx(cfg, args):
    tabx_title_list = cfg['TABX']['list'].split(';')

    for title in tabx_title_list:
        page_title = f'Data:{title}.tabx'
        tabx_obj = HuijiWikiTabx(cfg['wiki'], page_title)

        save_filepath = os.path.join(EXCEL_PATH, f'{title}.xlsx')
        if not tabx_obj.compare_with_wikitext(WIKITEXT_PATH):
            tabx_obj.save_as_xlsx(save_filepath, title)
            tabx_obj.save_raw_to_wikitext(WIKITEXT_PATH)
            log(f'[[{page_title}]] 保存完成。')
        else:
            log(f'[[{page_title}]] 线上版本无变化，不进行保存。')

        # 生成excel数据
        # headers = {title: tabx_obj.get_header()}
        # contents = {title: tabx_obj.get_all_data()}
        # save_to_excel(headers, contents, save_filepath)

        # 生成wikitext备份
        # save_wikitext_file(page_title, tabx_obj.get_raw_text())


def save_wikitext_file(page_title, page_content):
    page_title = HuijiWiki.filename_fix(page_title)
    wikitext_filepath = os.path.join(WIKITEXT_PATH, f'{page_title}.txt')

    file_content, result = read_file(wikitext_filepath)
    if result and file_content.strip() == page_content.strip():
        return

    with open(wikitext_filepath, 'w', encoding='UTF-8') as f:
        f.write(page_content)


# 上传所有tabx
def upload_all_tabx(cfg, args):
    # 登录wiki
    if not cfg['wiki'].login(cfg['WIKI']['username'], cfg['WIKI']['password']):
        raise Exception('登录WIKI失败，请稍后再试')
    if not cfg['wiki'].get_edit_token():
        raise Exception('获取TOKEN失败，请稍后再试')

    # 进行编辑
    tabx_title_list = cfg['TABX']['list'].split(';')

    for title in tabx_title_list:
        page_title = f'Data:{title}.tabx'
        tabx_obj = HuijiWikiTabx(cfg['wiki'], page_title, load=False)

        xlsx_filepath = os.path.join(EXCEL_PATH, f'{title}.xlsx')

        tabx_obj.open_xlsx(xlsx_filepath)
        tabx_obj.save(WIKITEXT_PATH)
