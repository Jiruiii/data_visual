# 組員開發環境設定指南

> 這是給組員的完整設定教學，跟著步驟做就能開始開發！

---

## 🚀 第一次設定（5分鐘）

### 步驟 1：Clone 專案

```powershell
# Clone 專案到你的電腦
git clone https://github.com/Jiruiii/data_visual.git
cd data-visual
```

### 步驟 2：建立 Python 環境

```powershell
# 建立 conda 環境
conda create -n data_visual python=3.11 -y

# 啟動環境
conda activate data_visual
```

### 步驟 3：建立 .env 檔案

```powershell
# 複製範本
copy .env.example .env

# 用記事本編輯
notepad .env
```

在 `.env` 中填入**組長給你的 Kaggle 憑證**：
```
KAGGLE_USERNAME=你的kaggle使用者名稱
KAGGLE_KEY=你的kaggle_api_金鑰
```

> ⚠️ 這些憑證應該由組長透過私訊（LINE/Discord）告訴你，**不要公開分享！**

### 步驟 4：安裝套件

```powershell
# 直接從 requirements.txt 安裝所有套件
pip install -r requirements.txt
```

### 步驟 5：執行專案

```powershell
python app.py
```

然後在瀏覽器開啟：**http://localhost:5000**

看到網站和所有圖表就代表成功了！🎉

---

## 📝 一鍵安裝指令

如果你想一次複製貼上所有指令：

```powershell
# Clone 並進入專案（改成你們的 GitHub URL）
git clone https://github.com/你們組的帳號/data-visual.git
cd data-visual

# 建立並啟動環境
conda create -n data_visual python=3.11 -y
conda activate data_visual

# 安裝所有套件
pip install -r requirements.txt

# 建立 .env（記得編輯內容！）
copy .env.example .env
notepad .env

# 執行專案
python app.py
```

---

## 🔧 每次開發時的流程

```powershell
# 1. 進入專案資料夾
cd data-visual

# 2. 啟動環境
conda activate data_visual

# 3. 更新程式碼（如果組員有修改）
git pull

# 4. 執行專案
python app.py
```

---

## 🔄 修改程式碼後如何更新

### 如果你修改了程式碼：

```powershell
# 1. 查看改了什麼
git status

# 2. 加入修改
git add .

# 3. Commit（描述你做了什麼）
git commit -m "修改了 XXX 功能"

# 4. Push 到 GitHub
git push
```

### 如果組員修改了程式碼：

```powershell
# 拉取最新版本
git pull
```

---

## ⚠️ 重要提醒

### ✅ 一定要做的事：
- 確保 `.env` 檔案在專案根目錄
- 填入正確的 Kaggle 憑證
- 每次開發前執行 `conda activate data_visual`
- 修改程式碼後要 commit 和 push

### ❌ 絕對不要做的事：
- **不要 commit `.env` 檔案**（憑證會外洩！）
- **不要把憑證貼在公開地方**（GitHub issue、討論區等）
- **不要分享含有憑證的截圖**
- **不要直接修改 `main` 分支**（如果有使用分支的話）

---

## 🐛 常見問題

### 問題 1：找不到 `conda` 指令
**原因：** 沒有安裝 Anaconda 或 Miniconda

**解決：**
1. 下載 Miniconda：https://docs.conda.io/en/latest/miniconda.html
2. 安裝後重新啟動 PowerShell
3. 執行 `conda --version` 確認

### 問題 2：找不到 data_visual 環境
**原因：** 環境還沒建立

**解決：**
```powershell
conda create -n data_visual python=3.11 -y
conda activate data_visual
```

### 問題 3：下載資料失敗
**原因：** `.env` 檔案格式錯誤或憑證不正確

**解決：**
- 檢查 `.env` 檔案中**沒有多餘空格**
- 確認憑證是組長給的
- 確認網路連線正常

### 問題 4：Import 錯誤
**原因：** 套件沒安裝或環境沒啟動

**解決：**
```powershell
# 確保環境已啟動
conda activate data_visual

# 重新安裝套件
pip install -r requirements.txt
```

### 問題 5：Port 5000 被占用
**原因：** 其他程式正在使用 Port 5000

**解決：** 修改 `app.py` 最後一行：
```python
app.run(debug=True, port=5001)  # 改成 5001 或其他 port
```

### 問題 6：Git push 失敗
**原因：** 沒有設定 Git 帳號或權限不足

**解決：**
```powershell
# 設定 Git 帳號
git config --global user.name "你的名字"
git config --global user.email "你的Email"

# 如果是權限問題，向組長確認你有寫入權限
```

---

## ✅ 安裝完成檢查清單

在開始開發前，確認這些都完成了：

- [ ] 已 clone 專案到本地
- [ ] 已建立 `data_visual` 環境
- [ ] 已建立 `.env` 檔案並填入憑證
- [ ] 已安裝所有套件
- [ ] 執行 `python app.py` 成功
- [ ] 瀏覽器能開啟 http://localhost:5000
- [ ] 能看到網站首頁
- [ ] 所有 6 個圖表都能正常顯示

---

## 📂 專案結構說明

```
data-visual/
├── app.py              # Flask 主程式（後端邏輯）
├── requirements.txt    # Python 套件清單
├── .env               # Kaggle 憑證（你建立的，不會 commit）
├── .env.example       # 憑證範本（會 commit）
├── .gitignore         # Git 忽略清單
├── data/              # 資料集資料夾
├── templates/         # HTML 模板
│   ├── base.html     # 基礎模板
│   ├── index.html    # 首頁
│   ├── overview.html # 統計概覽
│   ├── map.html      # 地圖分析
│   ├── charts.html   # 基本圖表
│   └── advanced.html # 進階圖表
└── static/           # 靜態檔案
    └── css/
        └── custom.css # 自訂樣式
```

---

## 🎯 開發注意事項

### 修改程式碼時：
- **後端邏輯** → 修改 `app.py`
- **前端樣式** → 修改 `static/css/custom.css`
- **頁面內容** → 修改 `templates/*.html`

### 測試流程：
1. 修改程式碼
2. 按 Ctrl+C 停止伺服器
3. 重新執行 `python app.py`
4. 重新整理瀏覽器

### 團隊協作：
- 開始工作前先 `git pull`
- 完成功能後立即 `git push`
- Commit message 要清楚描述
- 遇到衝突先跟組員討論

---

## 📞 還有問題？

1. **先檢查錯誤訊息** - PowerShell 會顯示詳細錯誤
2. **查看這份文件** - 大部分問題都有解答
3. **Google 錯誤訊息** - 很多問題都有人遇過
4. **問組長或其他組員** - 不要自己卡住太久

---

## 🎉 準備好了嗎？

當你完成所有設定，就可以開始開發了！

祝你開發順利！有問題隨時問組長！💪

---

**最後提醒：不要把 `.env` 檔案 commit 到 GitHub！**
