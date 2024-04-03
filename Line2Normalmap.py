import os
import sys
from modules import launch_utils_Line2Normalmap

# Default arguments
default_args = ["--nowebui", "--xformers", "--skip-python-version-check", "--skip-torch-cuda-test", "--skip-torch-cuda-test"]

# Check if custom arguments are provided; if not, append default arguments
if len(sys.argv) == 1:
    sys.argv.extend(default_args)
else:
    # 独自の引数がある場合、default_argsの中で未指定の引数のみを追加する
    # 引数を解析しやすくするため、setを使用
    provided_args_set = set(sys.argv)
    for arg in default_args:
        # "--"で始まるオプションのみを考慮する
        if arg.startswith("--"):
            option = arg.split("=")[0] if "=" in arg else arg
            if option not in provided_args_set:
                sys.argv.append(arg)
        else:
            # "--"で始まらないオプションは直接追加
            sys.argv.append(arg)

args = launch_utils_Line2Normalmap.args

start = launch_utils_Line2Normalmap.start

def main():
    start()

if __name__ == "__main__":
    main()