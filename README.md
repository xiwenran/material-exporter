# 资料导出工具

原 `ppt-batch-tool`，现更名为 `material-exporter`。工具从 PPT 批量转图片扩展为更通用的资料导出工具，目前支持 PPT / Word 导出为 PNG 图片，并支持递归扫描子文件夹。

## 功能

- 递归扫描指定文件夹中所有支持的资料文件
  （`.ppt` `.pptx` `.pps` `.ppsx` `.doc` `.docx` `.docm` `.dot` `.dotx` `.dotm`）
- 自动跳过 Office 临时文件（`~$` 开头）
- 支持单个文件直接输入（通过 CLI `--only-file`）
- 每个文件导出前 N 页为 PNG 图片（默认 17 页，可调整）
- 自动清理文件名（去除版权声明、平台标记等）
- 每个文件的图片存入独立文件夹
- 显示详细的成功/失败统计和日志
- 中文图形界面，双击即可使用

## 转换引擎

程序会自动检测并使用你电脑上已安装的办公软件：

| 平台 | 优先使用 | 备选 |
|------|---------|------|
| Windows | PowerPoint（PPT）/ Word（Word） | LibreOffice |
| macOS | PowerPoint AppleScript（PPT）/ Word AppleScript（Word） | LibreOffice |

> 如果以上都没有，需要安装免费的 [LibreOffice](https://www.libreoffice.org/download/)（安装一次即可）。

## 使用方法

1. 双击打开程序
2. 选择包含资料文件的文件夹
3. 设置导出页数（默认 17 页）
4. 点击「开始转换」
5. 等待完成，查看结果

## 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 打包

### macOS

```bash
bash build_app.sh
# 生成 dist/资料导出工具.app 和 dist/资料导出工具_arm64.dmg
```

首次打开未签名的 `.app`：右键点击 → 打开 → 打开。

### Windows

推送到 `main` 分支后，GitHub Actions 自动打包，在 Actions 页面下载 `资料导出工具_windows_x64.zip`。

或本地打包：
```bash
pip install pyinstaller
pyinstaller --windowed --name "资料导出工具" --noconfirm main.py
```

## 更名说明

本项目原名为 `ppt-batch-tool`，现更名为 `material-exporter`。如果本地仍保留旧克隆，请把远端同步到新仓库名：

```bash
git remote set-url origin https://github.com/xiwenran/material-exporter.git
```

旧仓库名、旧本地路径和旧 Skill 名只作为兼容备注保留。

## 输出结构

```
导出图片/
├── 资料名称A/
│   ├── 1.png
│   ├── 2.png
│   └── ...
├── 资料名称B/
│   ├── 1.png
│   └── ...
└── ...
```

## 文件名清理规则

程序会自动从源文件名中去除：
- 平台标记（公众号、小红书、抖音、微博等）
- 版权声明（侵权删、转载、版权等）
- @用户名
- 各种括号内容（【】、[]、（））

例如：`精美课件【公众号：XXX】侵删.pptx` → `精美课件/`

---

## 命令行工具（CLI）

除图形界面外，提供 `cli.py` 支持无界面批量处理，可由 Claude Code 等 AI 工具直接调用。

### 检测可用引擎

```bash
python3 cli.py detect
```

### 批量转换

```bash
# 文件夹模式（递归扫描所有支持的资料文件）
python3 cli.py convert \
  --input <源文件夹> \
  --output <图片输出目录> \
  --max-slides 17

# 单文件模式（目前支持 PPT / Word）
python3 cli.py convert \
  --input <源文件夹> \
  --output <图片输出目录> \
  --only-file <文件名.docx>
```

**macOS 授权说明**：首次运行会弹出 PowerPoint 或 Word 授权窗口，点「允许」后本次批量不再重复弹出。单文件模式不复制文件，直接在原始目录操作，不触发额外授权。

### 与融景联动（pipeline.py）

`pipeline.py` 把「资料导出图片」和「融景透视合成」串联成一键流水线：

```bash
# 整个资料文件夹（使用全部融景模板）
python3 pipeline.py run \
  --input <资料文件夹> \
  --output <输出目录>

# 单个资料文件（指定模板）
python3 pipeline.py run \
  --input <单个资料文件.pptx> \
  --output <输出目录> \
  --templates 3

# 自定义页数和模板
python3 pipeline.py run \
  --input <资料文件夹> \
  --output <输出目录> \
  --templates 1 2 3 \
  --max-slides 10
```

输出结构：
```
输出目录/
  资料图片/          ← 原始导出的 PNG（可单独使用）
    资料A/
      1.png  2.png ...
  合成图/           ← 融景合成完的成品
    资料A/
      3/            ← 模板编号
        1.jpg  2.jpg ...
```

### Claude Code Skill

已提供两个 Skill，在 Claude Code 中可直接用自然语言触发：

- `material-exporter`（原 `ppt-batch-tool`）：仅导出图片
  > 「把这个文件夹里所有 PPT / Word 转成图片，输出到 Downloads」

- `ppt-notes-pipeline`（`~/.claude/skills/ppt-notes-pipeline/SKILL.md`）：导出 + 融景合成一键完成
  > 「把这个 PPT 一键做成笔记图，用第3个模板」
