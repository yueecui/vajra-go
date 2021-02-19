import argparse
from config_loader import config_loader
from gbfmodule import *


def main():
    # 读取配置文件
    cfg = config_loader('config.ini')

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='GBF WIKI Bot(https://gbf.huijiwiki.com)',
                                     epilog='Last Update: 2020-3-9')
    subparsers = parser.add_subparsers(title='sub modules')

    # 下载图片信息
    extract_parser = subparsers.add_parser('image', help='download all image')
    extract_parser.add_argument('img_type', type=str)
    extract_parser.set_defaults(callback=download_data_image)

    # 抓取游戏数据
    extract_parser = subparsers.add_parser('data', help='download game data')
    extract_parser.set_defaults(callback=download_game_data)

    # 重新下载数据
    extract_parser = subparsers.add_parser('reload', help='download game data')
    extract_parser.set_defaults(callback=reload_all_data)

    # 重新下载数据
    extract_parser = subparsers.add_parser('news', help='download game news')
    extract_parser.set_defaults(callback=download_all_news)

    # 抓取游戏数据
    extract_parser = subparsers.add_parser('find', help='find new game data')
    extract_parser.add_argument('find_order', nargs='?', default='new', type=str)
    extract_parser.set_defaults(callback=find_new_game_data)

    # 下载上传tabx数据
    extract_parser = subparsers.add_parser('tabx', help='wiki tabx updater')
    extract_parser.add_argument('command', type=str)
    extract_parser.set_defaults(callback=gbf_wiki_tabx_updater)

    # 更新WIKI页面
    extract_parser = subparsers.add_parser('wiki', help='wiki page updater')
    extract_parser.add_argument('command',  nargs='?', default='all', type=str)
    extract_parser.set_defaults(callback=gbf_wiki_page_updater)

    # 更新WIKI页面
    extract_parser = subparsers.add_parser('gacha', help='gacha data update to wiki')
    extract_parser.set_defaults(callback=update_shabi)

    # 上传图片
    extract_parser = subparsers.add_parser('upload', help='upload all image')
    extract_parser.add_argument('path', type=str)
    extract_parser.set_defaults(callback=upload_image)

    # 获取解析后的参数
    args = parser.parse_args()

    if hasattr(args, 'callback'):
        args.callback(cfg, args)
    else:
        print('error command')
        parser.print_help()


if __name__ == '__main__':
    main()
