import argparse
from config_loader import config_loader
from gbfmodule import *


def main():
    # 读取配置文件
    cfg = config_loader('config.ini')

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='GBF WIKI Bot(https://gbf.huijiwiki.com)',
                                     epilog='Last Update: 2019-3-1')
    subparsers = parser.add_subparsers(title='sub modules')

    # 下载图片信息
    extract_parser = subparsers.add_parser('image', help='download all image')
    extract_parser.add_argument('img_type', type=str)
    extract_parser.set_defaults(callback=download_data_image)

    # 抓取游戏数据
    extract_parser = subparsers.add_parser('data', help='download game data')
    extract_parser.set_defaults(callback=download_game_data)

    # 抓取游戏数据
    extract_parser = subparsers.add_parser('find', help='find new game data')
    extract_parser.add_argument('find_order', nargs='?', default='new', type=str)
    extract_parser.set_defaults(callback=find_new_game_data)

    # 抓取游戏数据
    extract_parser = subparsers.add_parser('tabx', help='wiki tabx updater')
    extract_parser.add_argument('command', type=str)
    extract_parser.set_defaults(callback=gbf_wiki_tabx_updater)

    # 获取解析后的参数
    args = parser.parse_args()

    if hasattr(args, 'callback'):
        args.callback(cfg, args)
    else:
        print('error command')
        parser.print_help()


if __name__ == '__main__':
    main()
