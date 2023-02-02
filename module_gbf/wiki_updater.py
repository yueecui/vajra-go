from module_huiji.huijiWiki import HuijiWiki
from .data.sim import GBFSim
from .wiki import *


def gbf_wiki_page_updater(cfg, args):
    cfg['wiki'] = HuijiWiki('gbf')
    if args.command not in ['item']:
        cfg['sim'] = GBFSim(cfg, check_ver=False)
    # 登录wiki
    if not cfg['wiki'].login(cfg['WIKI']['username'], cfg['WIKI']['password']):
        raise Exception('登录WIKI失败，请稍后再试')
    if not cfg['wiki'].get_edit_token():
        raise Exception('获取TOKEN失败，请稍后再试')

    if args.command == 'summon':
        update_summon_tabx(cfg, args)
        update_summon_page(cfg, args)
        update_summon_auto_db(cfg, args)
    elif args.command == 'weapon':
        update_weapon_tabx(cfg, args)
        update_weapon_page(cfg, args)
        update_weapon_auto_db(cfg, args)
    elif args.command == 'item':
        update_item_tabx(cfg, args)
        update_item_auto_db(cfg, args)
    elif args.command == 'char':
        update_character_auto_db(cfg, args)
    elif args.command == 'leader':
        update_leader_auto_db(cfg, args)
    elif args.command == 'skin':
        update_skin_auto_db(cfg, args)
    elif args.command == 'anime':
        merge_anime_excel(cfg, args)
        check_anime_file(cfg, args)
        update_anime_page(cfg, args)
    elif args.command == 'autodb':
        update_summon_auto_db(cfg, args)
        update_weapon_auto_db(cfg, args)
        update_item_auto_db(cfg, args)
        update_character_auto_db(cfg, args)
        update_leader_auto_db(cfg, args)
        update_skin_auto_db(cfg, args)
    else:
        print('错误的指令')
