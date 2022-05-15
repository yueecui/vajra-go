import os
from module_huiji.danteng_lib import log
from module_huiji.huijiWiki import HuijiWiki


def upload_image(cfg, args):
    folder_name = os.path.join(args.path)
    if not os.path.exists(folder_name):
        log('目录“%s”不存在，请检查！' % folder_name)
        return False
    file_list = os.listdir(folder_name)

    if len(file_list) == 0:
        log('目录“%s”没有要上传的文件！请检查！' % folder_name)
        return False
    else:
        log('共有 %d 个文件需要上传！' % len(file_list))

    wiki = HuijiWiki('gbf')
    # 登录wiki
    if not wiki.login(cfg['WIKI']['username'], cfg['WIKI']['password']):
        raise Exception('登录WIKI失败，请稍后再试')
    if not wiki.get_edit_token():
        raise Exception('获取TOKEN失败，请稍后再试')

    for img_filename in file_list:
        src_img_filepath = os.path.join(folder_name, img_filename)
        wiki_file_name = img_filename
        wiki.upload_image_by_path(wiki_file_name, src_img_filepath, keepfile=False, overwrite=False)
