from module_gbf.image import *
from module_huiji.huijiWiki import HuijiWiki


DOWNLOAD_TYPE = {
    'npc': npc,
    'skill': skill,
    'skin': skin,
    'summon': summon,
    'weapon': weapon,
    'weapon_skill': weapon_skill,
    'item': item,
    'leader': leader,
}


def download_data_image(cfg, args):
    cfg['wiki'] = HuijiWiki('gbf')
    cfg['base_url'] = 'https://prd-game-a-granbluefantasy.akamaized.net/assets/img/sp/'

    if args.img_type == 'all':
        for img_type, download_fun in DOWNLOAD_TYPE.items():
            download_fun(cfg)
    elif args.img_type in DOWNLOAD_TYPE:
        DOWNLOAD_TYPE[args.img_type](cfg)
    else:
        return {'c': 1000, 'msg': '错误的下载类型！'}
