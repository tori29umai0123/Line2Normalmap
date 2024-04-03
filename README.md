# Line2Normalmap

[stable-diffusion-webui-forge](https://github.com/lllyasviel/stable-diffusion-webui-forge/tree/main) をバックエンドに組み込んだ、線画→ノーマルマップを生成するGUIアプリです。

![1](https://github.com/tori29umai0123/Line2Normalmap/assets/72191117/2147f6f7-32d0-46af-a967-b340ce1d6888)

# ビルド設定（開発者向け）
①Line2Normalmap_install.ps1を実行してインストール<br>
②セキュリティーソフトの設定で、フォルダと実行ファイル名を除外リストに追加する。<br>
例：Windows Defenderの場合、Windows セキュリティ→ウイルスと脅威の防止→ウイルスと脅威の防止の設定→設定の管理→除外<br>
Line2Normalmap.exe(プロセス)<br>
C:\Line2Normalmap（フォルダ）<br>
のように指定する。<br>
③venv.cmdを実行。
```
pyinstaller "C:\Line2Normalmap\Line2Normalmap.py" ^
--clean ^
--collect-data tkinterdnd2 ^
--add-data "C:\Line2Normalmap\javascript;.\javascript" ^
--add-data "C:\Line2Normalmap\ldm_patched;.\ldm_patched" ^
--add-data "C:\Line2Normalmap\localizations;.\localizations" ^
--add-data "C:\Line2Normalmap\modules;.\modules" ^
--add-data "C:\Line2Normalmap\modules_forge;.\modules_forge" ^
--add-data "C:\Line2Normalmap\repositories;.\repositories" ^
--add-data "C:\Line2Normalmap\cache.json;." ^
--add-data "C:\Line2Normalmap\script.js;." ^
--add-data "C:\Line2Normalmap\ui-config.json;." ^
--add-data "C:\Line2Normalmap\config_states;.\config_states" ^
--add-data "C:\Line2Normalmap\configs;.\configs" ^
--add-data "C:\Line2Normalmap\extensions-builtin;.\extensions-builtin" ^
--add-data "C:\Line2Normalmap\html;.\html"

xcopy /E /I /Y venv\Lib\site-packages\xformers dist\Line2Normalmap\_internal\xformers
xcopy /E /I /Y venv\Lib\site-packages\pytorch_lightning dist\Line2Normalmap\_internal\pytorch_lightning
xcopy /E /I /Y venv\Lib\site-packages\lightning_fabric dist\Line2Normalmap\_internal\lightning_fabric
xcopy /E /I /Y venv\Lib\site-packages\gradio dist\Line2Normalmap\_internal\gradio
xcopy /E /I /Y venv\Lib\site-packages\gradio_client dist\Line2Normalmap\_internal\gradio_client
xcopy /E /I /Y venv\Lib\site-packages\kornia dist\Line2Normalmap\_internal\kornia
xcopy /E /I /Y venv\Lib\site-packages\open_clip dist\Line2Normalmap\_internal\open_clip
xcopy /E /I /Y venv\Lib\site-packages\jsonmerge dist\Line2Normalmap\_internal\jsonmerge
xcopy /E /I /Y venv\Lib\site-packages\torchdiffeq dist\Line2Normalmap\_internal\torchdiffeq
xcopy /E /I /Y venv\Lib\site-packages\cleanfid dist\Line2Normalmap\_internal\cleanfid
xcopy /E /I /Y venv\Lib\site-packages\clip dist\Line2Normalmap\_internal\clip
xcopy /E /I /Y venv\Lib\site-packages\resize_right dist\Line2Normalmap\_internal\resize_right
xcopy /E /I /Y venv\Lib\site-packages\diffusers dist\Line2Normalmap\_internal\diffusers
xcopy /E /I /Y venv\Lib\site-packages\onnx dist\Line2Normalmap\_internal\onnx
xcopy /E /I /Y venv\Lib\site-packages\onnxruntime dist\Line2Normalmap\_internal\onnxruntime
xcopy /E /I /Y config_states dist\Line2Normalmap\config_states
xcopy /E /I /Y configs dist\Line2Normalmap\configs
xcopy /E /I /Y embeddings dist\Line2Normalmap\embeddings
xcopy /E /I /Y extensions-builtin dist\Line2Normalmap\extensions-builtin
xcopy /E /I /Y html dist\Line2Normalmap\html
xcopy /E /I /Y javascript dist\Line2Normalmap\javascript
xcopy /E /I /Y ldm_patched dist\Line2Normalmap\ldm_patched
xcopy /E /I /Y localizations dist\Line2Normalmap\localizations
xcopy /E /I /Y modules dist\Line2Normalmap\modules
xcopy /E /I /Y modules_forge dist\Line2Normalmap\modules_forge
xcopy /E /I /Y repositories dist\Line2Normalmap\repositories
xcopy /E /I /Y scripts dist\Line2Normalmap\scripts
copy script.js dist\Line2Normalmap\script.js
copy Line2Normalmap_model_DL.cmd dist\Line2Normalmap\Line2Normalmap_model_DL.cmd
copy Line2Normalmap_ReadMe.txt dist\Line2Normalmap\Line2Normalmap_ReadMe.txt 
```
