# 現在のスクリプトのディレクトリに移動する
Set-Location $PSScriptRoot

# pipのバージョンチェックを無効化する
$Env:PIP_DISABLE_PIP_VERSION_CHECK = 1

# Pythonの仮想環境を作成する
if (!(Test-Path -Path "venv")) {
    Write-Output "Creating Python virtual environment..."
    python -m venv venv
}
.\venv\Scripts\Activate

# pipをアップグレードする
Write-Output "pipをアップグレード"
python.exe -m pip install --upgrade pip

# リポジトリをクローンして特定のコミットにチェックアウトする
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git
cd stable-diffusion-webui-forge
git checkout 29be1da7cf2b5dccfc70fbdd33eb35c56a31ffb7

# 一つ上のディレクトリに移動する
cd ..

# stable-diffusion-webui-forgeの内容を上のディレクトリに再帰的にコピーする
$sourceDir = "stable-diffusion-webui-forge"
$excludeDirs = @("$sourceDir\.git", "$sourceDir\.github")

Get-ChildItem -Path $sourceDir -Recurse | Where-Object {
    $path = $_.FullName
    -not ($excludeDirs | Where-Object { $path.StartsWith($_) }) -or
    $path.StartsWith("$sourceDir\repositories\.git") -or
    $path.StartsWith("$sourceDir\repositories\.github")
} | ForEach-Object {
    $destPath = $_.FullName.Replace("$sourceDir\", "")
    if (-not $_.PSIsContainer) {
        $destDir = [System.IO.Path]::GetDirectoryName($destPath)
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir | Out-Null
        }
        Copy-Item -Path $_.FullName -Destination $destPath -Force
    } else {
        if (-not (Test-Path $destPath)) {
            New-Item -ItemType Directory -Path $destPath | Out-Null
        }
    }
}

# stable-diffusion-webui-forgeフォルダを削除する
Remove-Item -Path "stable-diffusion-webui-forge" -Recurse -Force

# Line2Normalmap_setup.pyを実行する
python .\Line2Normalmap_setup.py

# Line2Normalmap_model_DL.cmdを実行する
.\Line2Normalmap_model_DL.cmd

# webui-user.batを実行する
.\webui-user.bat

Write-Output "インストール完了"
Read-Host -Prompt "Press Enter to exit"
