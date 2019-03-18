from gbfmodule.image import *
from huijiWiki import HuijiWiki


DOWNLOAD_TYPE = {
    'npc': npc,
    'skill': skill,
    'skin': skin,
    'summon': summon,
}


def download_data_image(cfg, args):
    cfg['wiki'] = HuijiWiki('gbf')
    cfg['base_url'] = 'http://game-a.granbluefantasy.jp/assets/img/sp/'

    if args.img_type == 'all':
        for img_type, download_fun in DOWNLOAD_TYPE.items():
            download_fun(cfg)
    elif args.img_type in DOWNLOAD_TYPE:
        DOWNLOAD_TYPE[args.img_type](cfg)
    else:
        return {'c': 1000, 'msg': '错误的下载类型！'}
