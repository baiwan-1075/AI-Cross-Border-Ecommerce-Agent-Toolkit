"""Sovyn local workflow helpers. No network, model calls or external writes."""
import argparse
from decimal import InvalidOperation
import json
import os
from pathlib import Path
import sqlite3
import sys
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from toolkit.context import ROOT, bind, doctor, inventory, load_binding, load_json, save_new
from toolkit.metrics import diagnose
from toolkit.pricing import review_pricing
from toolkit.workflow import check_repository, prepare


def main():
    parser = argparse.ArgumentParser(description='Sovyn MY 宠物运营工具箱（只读业务资料）')
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('bind', help='绑定本地业务项目；新建Git忽略的配置')
    for option in ('project-root', 'assets-root', 'pricing-root'):
        setup.add_argument('--' + option, required=True)
    commands.add_parser('doctor', help='检查当前权威文档与本地工具来源')
    commands.add_parser('check', help='检查本仓库结构与链接')
    inv = commands.add_parser('inventory', help='只读原图清单并按资料路径匹配工作台')
    inv.add_argument('--folder', required=True)
    task = commands.add_parser('prepare', help='整理交给现有智能体的任务包，不调用模型')
    task.add_argument('--module', choices=['market', 'strategy', 'listing', 'image', 'video', 'performance', 'review', 'workflow'], required=True)
    task.add_argument('--brief', required=True)
    metrics = commands.add_parser('funnel', help='计算同窗口同归因的自然流量指标')
    metrics.add_argument('--input', required=True)
    price = commands.add_parser('pricing', help='只读保存参数，复用本地现役定价内核')
    price.add_argument('--product-cost-cny')
    price.add_argument('--weight-g')
    price.add_argument('--pricing-date')
    price.add_argument('--database', help='默认现役本地库，也可指定只读核验副本')
    for command in (inv, task, metrics, price):
        command.add_argument('--out', required=True, help='本仓库.local内新的输出文件')
    args = parser.parse_args()
    try:
        if args.command == 'bind':
            result = bind(args.project_root, args.assets_root, args.pricing_root)
        elif args.command == 'doctor':
            result = doctor()
        elif args.command == 'check':
            result = check_repository()
        elif args.command == 'inventory':
            result = inventory(load_binding(), args.folder)
        elif args.command == 'prepare':
            result = prepare(load_binding(), load_json(args.brief), args.module)
        elif args.command == 'funnel':
            result = diagnose(load_json(args.input))
        else:
            database = args.database or str(Path(os.environ['LOCALAPPDATA']) / 'Xiaomian/HomeProfitSpaceCalculator/calculator.db')
            result = review_pricing(load_binding(), database, args.product_cost_cny, args.weight_g, args.pricing_date)
        if hasattr(args, 'out'):
            path = save_new(ROOT, args.out, result)
            print(json.dumps({'status': 'WRITTEN_LOCAL_ONLY', 'path': str(path)}, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if isinstance(result, dict) and result.get('status') in ('FAIL', 'MISSING') else 0
    except (ValueError, KeyError, OSError, ImportError, InvalidOperation,
            sqlite3.Error, BadZipFile, ParseError, IndexError) as exc:
        print(json.dumps({'status': 'ERROR', 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
