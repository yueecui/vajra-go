import argparse
from config_loader import config_loader
from gbfmodule import *


def main():
    # 读取配置文件
    cfg = config_loader('config.ini')

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='GBF WIKI Helper(https://gbf.huijiwiki.com)',
                                     epilog='Last Update: 2018-12-12')
    subparsers = parser.add_subparsers(title='sub modules')

    # 更新版本信息
    extract_parser = subparsers.add_parser('image', help='download all image')
    extract_parser.add_argument('img_type', type=str)
    extract_parser.set_defaults(callback=download_all_image)

    # 获取解析后的参数
    args = parser.parse_args()

    if hasattr(args, 'callback'):
        args.callback(cfg, args)
    else:
        print('error command')
        parser.print_help()


if __name__ == '__main__':
    main()
