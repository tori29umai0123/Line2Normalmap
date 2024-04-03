@echo off
setlocal enabledelayedexpansion

REM モデルディレクトリの基本パスを実行ディレクトリのmodelsサブディレクトリに設定
set "dpath=%~dp0models"

REM Taggerモデルダウンロード
set "MODEL_DIR=%dpath%\tagger"
set "MODEL_ID=SmilingWolf/wd-swinv2-tagger-v3"
set "FILES=config.json model.onnx selected_tags.csv sw_jax_cv_config.json"

if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"

for %%f in (%FILES%) do (
    set "FILE_PATH=%MODEL_DIR%\%%f"
    if not exist "!FILE_PATH!" (
        curl -L "https://huggingface.co/%MODEL_ID%/resolve/main/%%f" -o "!FILE_PATH!"
        echo Downloaded %%f
    ) else (
        echo %%f already exists.
    )
)

REM Loraモデルダウンロード
set "MODEL_DIR=%dpath%\Lora"
set "MODEL_ID=tori29umai/SDXL_shadow"
set "FILES=sdxl-testlora-normalmap_04b_dim32.safetensors"

if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
for %%f in (%FILES%) do (
    set "FILE_PATH=%MODEL_DIR%\%%f"
    if not exist "!FILE_PATH!" (
        curl -L "https://huggingface.co/%MODEL_ID%/resolve/main/%%f" -o "!FILE_PATH!"
        echo Downloaded %%f
    ) else (
        echo %%f already exists.
    )
)

REM ControlNetモデルダウンロード
set "MODEL_DIR=%dpath%\ControlNet"
set "MODEL_ID=stabilityai/control-lora"
set "FILES=control-lora-canny-rank256.safetensors"

if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
for %%f in (%FILES%) do (
    set "FILE_PATH=%MODEL_DIR%\%%f"
    if not exist "!FILE_PATH!" (
        curl -L "https://huggingface.co/%MODEL_ID%/resolve/main/control-LoRAs-rank256/%%f" -o "!FILE_PATH!"
        echo Downloaded %%f
    ) else (
        echo %%f already exists.
    )
)

REM Stable-diffusionモデルダウンロード
set "MODEL_DIR=%dpath%\Stable-diffusion"
set "MODEL_ID=cagliostrolab/animagine-xl-3.0"
set "FILES=animagine-xl-3.0.safetensors"

if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
for %%f in (%FILES%) do (
    set "FILE_PATH=%MODEL_DIR%\%%f"
    if not exist "!FILE_PATH!" (
        curl -L "https://huggingface.co/%MODEL_ID%/resolve/main/%%f" -o "!FILE_PATH!"
        echo Downloaded %%f
    ) else (
        echo %%f already exists.
    )
)

endlocal
exit
