# 快速安裝與啟動腳本

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  網路安全威脅視覺化分析系統 - 安裝程式" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Conda 是否安裝
Write-Host "[1/5] 檢查 Conda 環境..." -ForegroundColor Yellow
try {
    $condaVersion = conda --version 2>&1
    Write-Host "✓ Conda 已安裝: $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 找不到 Conda！請先安裝 Anaconda 或 Miniconda" -ForegroundColor Red
    exit 1
}

# 檢查 data_visual 環境是否存在
Write-Host ""
Write-Host "[2/5] 檢查 data_visual 環境..." -ForegroundColor Yellow
$envExists = conda env list | Select-String "data_visual"
if ($envExists) {
    Write-Host "✓ 找到 data_visual 環境" -ForegroundColor Green
    Write-Host "正在啟動環境..." -ForegroundColor Cyan
    conda activate data_visual
} else {
    Write-Host "! data_visual 環境不存在" -ForegroundColor Yellow
    Write-Host "是否要建立 data_visual 環境？[Y/n]" -ForegroundColor Yellow
    $createEnv = Read-Host
    if ($createEnv -eq "" -or $createEnv -eq "Y" -or $createEnv -eq "y") {
        Write-Host "正在建立 data_visual 環境..." -ForegroundColor Cyan
        conda create -n data_visual python=3.11 -y
        Write-Host "正在啟動環境..." -ForegroundColor Cyan
        conda activate data_visual
        Write-Host "✓ data_visual 環境已建立並啟動" -ForegroundColor Green
    } else {
        Write-Host "✗ 已取消安裝" -ForegroundColor Red
        exit 1
    }
}

# 安裝相依套件
Write-Host ""
Write-Host "[3/5] 安裝相依套件..." -ForegroundColor Yellow
Write-Host "這可能需要幾分鐘時間..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 套件安裝完成" -ForegroundColor Green
} else {
    Write-Host "✗ 套件安裝失敗" -ForegroundColor Red
    exit 1
}

# 檢查資料檔案
Write-Host ""
Write-Host "[4/5] 檢查資料檔案..." -ForegroundColor Yellow
if (Test-Path "data\cybersecurity_threats.csv") {
    Write-Host "✓ 找到資料檔案" -ForegroundColor Green
} else {
    Write-Host "! 找不到資料檔案" -ForegroundColor Yellow
    Write-Host "  系統將使用範例資料，或請手動下載資料集" -ForegroundColor Cyan
    Write-Host "  詳見 DATA_SETUP.md" -ForegroundColor Cyan
}

# 完成
Write-Host ""
Write-Host "[5/5] 安裝完成！" -ForegroundColor Green
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  準備啟動系統" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "執行以下指令啟動伺服器：" -ForegroundColor Yellow
Write-Host "  conda activate data_visual" -ForegroundColor White
Write-Host "  python app.py" -ForegroundColor White
Write-Host ""
Write-Host "然後在瀏覽器開啟：" -ForegroundColor Yellow
Write-Host "  http://localhost:5000" -ForegroundColor White
Write-Host ""

# 詢問是否立即啟動
Write-Host "是否要立即啟動伺服器？[Y/n]" -ForegroundColor Yellow
$startNow = Read-Host
if ($startNow -eq "" -or $startNow -eq "Y" -or $startNow -eq "y") {
    Write-Host ""
    Write-Host "正在啟動伺服器..." -ForegroundColor Cyan
    Write-Host "按 Ctrl+C 可以停止伺服器" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "注意：請確保已啟動 data_visual 環境" -ForegroundColor Yellow
    Write-Host ""
    python app.py
}
