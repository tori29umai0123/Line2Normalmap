import os
import re
import shutil

# 絶対パスで作業ディレクトリを指定
script_path = os.path.abspath(__file__)
target_directory = os.path.dirname(script_path)

# 追加するコードの定義
prepend_code = """import sys
# 'frozen' 状態に応じて適切なファイルパスを取得する関数
def get_appropriate_file_path():
    if getattr(sys, 'frozen', False):
        return sys.executable + "/Line2Normalmap/"
    else:
        return __file__
appropriate_file_path = get_appropriate_file_path()
"""

ldm_special_prepend_code = """import sys
import os
def get_appropriate_file_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) + "/ldm_patched/modules"
    else:
        return os.path.dirname(__file__)
appropriate_file_path = get_appropriate_file_path()
"""

exclude_files = []

ldm_patched_files = [
    os.path.join(target_directory, "ldm_patched/modules/sd1_clip.py"),
    os.path.join(target_directory, "ldm_patched/modules/sd2_clip.py"),
    os.path.join(target_directory, "ldm_patched/modules/sdxl_clip.py"),
]

exclude_folders = [
    os.path.join(target_directory, "venv"),
    os.path.join(target_directory, "Line2Normalmap_modules"),
    os.path.join(target_directory, "utils"),   
]

# 新しいファイルの追加に加えて既存のコピー機能
files_to_copy = {
    os.path.join(target_directory, "Line2Normalmap_modules/config_states.py"): os.path.join(target_directory, "modules/config_states.py"),
    os.path.join(target_directory, "Line2Normalmap_modules/gitpython_hack.py"): os.path.join(target_directory, "modules/gitpython_hack.py"),  
    os.path.join(target_directory, "Line2Normalmap_modules/launch_utils_Line2Normalmap.py"): os.path.join(target_directory, "modules/launch_utils_Line2Normalmap.py"),
    os.path.join(target_directory, "Line2Normalmap_modules/sdxl_clip.py"): os.path.join(target_directory, "ldm_patched/modules/sdxl_clip.py"),
    os.path.join(target_directory, "Line2Normalmap_modules/sd1_clip.py"): os.path.join(target_directory, "ldm_patched/modules/sd1_clip.py"),
    os.path.join(target_directory, "Line2Normalmap_modules/sd2_clip.py"): os.path.join(target_directory, "ldm_patched/modules/sd2_clip.py"),
    os.path.join(target_directory, "Line2Normalmap_modules/shared_cmd_options.py"): os.path.join(target_directory, "modules/shared_cmd_options.py"),
    os.path.join(target_directory, "Line2Normalmap_modules/ui_extensions.py"): os.path.join(target_directory, "modules/ui_extensions.py"),    
}

def file_needs_update(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            return re.search(r'(?<!")(__file__)(?!")', content) is not None
    except UnicodeDecodeError:
        print(f"ファイル {filepath} でUnicodeDecodeErrorが発生しました。")
        return False

def file_already_prepared(filepath, code_snippet):
    """
    ファイルが指定されたコードスニペットをすでに含んでいるかどうかを確認します。

    :param filepath: 検証するファイルのパス
    :param code_snippet: チェックするコードスニペット
    :return: コードスニペットが存在する場合は True、そうでない場合は False
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            return code_snippet.strip() in content
    except UnicodeDecodeError:
        # ファイルがテキストファイルではない可能性があるため、False を返します
        return False

def update_file(filepath, special=False):
    # スクリプト自体をスキップする
    if filepath == script_path:
        print(f"ファイル {filepath} はこのスクリプトなのでスキップします。")
        return

    # exclude_filesに含まれるファイルをスキップする
    if filepath in exclude_files:
        print(f"ファイル {filepath} はexclude_filesに含まれているのでスキップします。")
        return

    # prepend_code または ldm_special_prepend_code が既に含まれているかどうかを確認
    prepend = ldm_special_prepend_code if special else prepend_code
    if file_already_prepared(filepath, prepend):
        print(f"ファイル {filepath} はすでに更新されています。スキップします。")
        return  # このファイルはすでに更新されているため、処理をスキップ

    if not any(filepath.startswith(excluded) for excluded in exclude_folders) and filepath not in exclude_files:
        with open(filepath, 'r+', encoding='utf-8') as file:
            content = file.read()
            updated_content = re.sub(r'(?<!")(__file__)(?!")', 'appropriate_file_path', content)
            file.seek(0)
            file.write(prepend + updated_content)
            file.truncate()

for root, dirs, files in os.walk(target_directory):
    dirs[:] = [d for d in dirs if os.path.join(root, d) not in exclude_folders]
    for file in files:
        filepath = os.path.join(root, file)
        if file.endswith('.py'):
            if filepath in ldm_patched_files:
                update_file(filepath, special=True)
            elif file_needs_update(filepath):
                update_file(filepath)

# ファイルをコピー
for src, dst in files_to_copy.items():
    try:
        shutil.copy2(src, dst)
        print(f"{src} から {dst} へコピーしました。")
    except IOError as e:
        print(f"{src} から {dst} へのコピーに失敗しました。エラー: {e}")

print("ファイルのコピーが完了しました。")

# webui-user.bat の内容を書き換え
webui_user_bat_path = os.path.join(target_directory, "webui-user.bat")
try:
    with open(webui_user_bat_path, 'r', encoding='utf-8') as bat_file:
        content = bat_file.read()
        updated_content = re.sub(r'set COMMANDLINE_ARGS=.*$', 'set COMMANDLINE_ARGS=--nowebui --xformers\n', content, flags=re.MULTILINE)
    with open(webui_user_bat_path, 'w', encoding='utf-8') as bat_file:
        bat_file.write(updated_content)
    print(f"{webui_user_bat_path} を更新しました")
except Exception as e:
    print(f"{webui_user_bat_path} の更新に失敗しました。エラー: {e}")

# 追加するパッケージのリスト
packages_to_add = [
    "tkinterdnd2==0.3.0",
    "onnx==1.15.0",
    "onnxruntime==1.17.1",
    "onnxruntime-gpu==1.17.1",
    "pyinstaller==6.4.0",
    "pygit2==1.14.1"
]

# requirements_versions.txt ファイルのパス
requirements_versions_path = os.path.join(target_directory, "requirements_versions.txt")

try:
    with open(requirements_versions_path, 'r', encoding='utf-8') as req_file:
        lines = req_file.readlines()
        last_line = lines[-1].strip() if lines else ''
        if last_line not in packages_to_add:
            with open(requirements_versions_path, 'a', encoding='utf-8') as req_file:
                for package in packages_to_add:
                    req_file.write(f"{package}\n")
            print("requirements_versions.txt にパッケージを追加しました")
        else:
            print("requirements_versions.txt には既にパッケージが存在しています。追加されませんでした。")
except Exception as e:
    print(f"requirements_versions.txt の更新に失敗しました。エラー: {e}")

print("処理が完了しました。")
