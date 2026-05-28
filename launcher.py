# -*- coding: utf-8 -*-
"""Open-source launcher for Whitehole Plan.

This launcher intentionally contains no license check, launch guard, or machine binding.
It is kept only so existing habits like `python launcher.py run` and `run.bat` continue to work.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from fx_product import PRODUCT_ID, PRODUCT_NAME, PRODUCT_VERSION, ENTRY_KIND, ENTRY_TARGET

ROOT = Path(__file__).resolve().parent


def cmd_run(_args):
    if ENTRY_KIND == "file":
        cmd = [sys.executable, ENTRY_TARGET]
    elif ENTRY_KIND == "module":
        cmd = [sys.executable, "-m", ENTRY_TARGET]
    else:
        raise SystemExit(f"Unsupported entry kind: {ENTRY_KIND}")
    print(f"[OPEN] Starting {PRODUCT_NAME} {PRODUCT_VERSION} ({PRODUCT_ID})")
    return subprocess.call(cmd, cwd=str(ROOT))


def cmd_info(_args):
    print(f"{PRODUCT_NAME} {PRODUCT_VERSION}")
    print("License gate: disabled / removed for open-source release")
    print(f"Entry: {ENTRY_KIND}:{ENTRY_TARGET}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(description=f"{PRODUCT_NAME} launcher")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="launch the app without license checks")
    sub.add_parser("info", help="print package information")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "info":
        return cmd_info(args)
    raise SystemExit("unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
