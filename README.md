# LifeOS 成长护照 CLI

LifeOS CLI 是一个面向个人用户的成长护照记录工具。

它用于记录和查看你的计划、行动、目标、复盘、成果和重要经历。你可以自己用命令记录，也可以把配套 Skill 安装给 AI 助手，让 AI 帮你把成长信息沉淀进成长护照。

CLI 默认连接当前 LifeOS 服务器：

```text
https://106.55.134.110/lifeos
```

## 安装 CLI + Skill

### 1. 安装 CLI

```bash
python3 -m pip install --user --upgrade \
  "git+https://github.com/AI-dogg/lifeos-cli.git"
```

也可以用 `pipx`：

```bash
brew install pipx
pipx install "git+https://github.com/AI-dogg/lifeos-cli.git"
```

如果安装后找不到 `lifeos` 命令，把用户命令目录加入 PATH：

```bash
export PATH="$HOME/Library/Python/3.*/bin:$HOME/.local/bin:$PATH"
```

### 2. 安装 AI 助手 Skill

Skill 会告诉 AI 助手：什么时候应该记录成长信息，什么时候只是讨论不该写入，以及在对话积累到一定量、上下文压缩前、交接前，如何总结一次并沉淀进成长护照。

把 Skill 复制到你的 AI 工具的 skills 目录：

```bash
git clone https://github.com/AI-dogg/lifeos-cli.git
export SKILLS_DIR="/path/to/your/skills"
mkdir -p "$SKILLS_DIR"
cp -R lifeos-cli/skills/lifeos_cli "$SKILLS_DIR/"
```

Cursor 用户也可以把项目规则复制到目标项目：

```text
.cursor/rules/lifeos-cli.mdc
```

### 3. 注册并验证

第一次使用：

```bash
lifeos register --name "你的名字" --password "你的密码"
lifeos profile get
lifeos diagnose
```

如果换设备或登录信息丢失：

```bash
lifeos login --name "你的名字" --password "你的密码"
```

### 4. 初始化成长护照

使用画像、七力评分、每日画像更新前，需要先初始化成长护照：

```bash
lifeos profile init --input-json '{
  "mainStoryline": "把 LifeOS 做成长期成长护照",
  "mostWantChange": "让行动复盘和个人沉淀更稳定",
  "pastBestPeriod": "持续推进产品落地的时候",
  "biggestBlocker": "容易被短期事务打断",
  "timeSpentDistribution": "产品建设、技术实现、复盘和学习",
  "longTermEnergySources": "创造产品、看到系统成型",
  "oneYearIdealState": "LifeOS 能稳定帮助用户沉淀成长轨迹",
  "noConstraintLife": "持续创造有价值的产品并保持健康节奏",
  "easyToFallIntoPatterns": "事情多时切换过频",
  "oneHabitToBuild": "每天完成一次行动复盘"
}'
```

如果字段不完整，CLI 会返回 `validation_error` 并列出缺少的字段。AI 助手应该一次追问 1-3 个自然问题，补齐后再调用 `profile init`。

## 常用方式

```bash
lifeos snapshot
lifeos plan save --date 2026-06-18 --action "09:00|写今日计划"
lifeos plan confirm --date 2026-06-18
lifeos action list --date 2026-06-18
lifeos action done --action-id ACTION_ID --text "已完成并验证结果"
lifeos fact add --dimension long_term_goal --statement "未来三年持续建设个人成长系统"
lifeos profile capture --dimension life_stage --statement "我正在从执行者转向产品负责人"
lifeos asset add --kind method_asset --title "每日复盘流程" --summary "用于沉淀计划、行动和成长证据"
```

查看帮助：

```bash
lifeos help
```

## 怎么选择

- 未来要做的事：用 `plan`
- 已经确认的行动：用 `action`
- 长期事实和里程碑：用 `fact`
- 人生阶段和目标：用 `profile capture`
- 首次建立成长护照：用 `profile init`
- 可复用成果和方法：用 `asset`
- 查看已有信息：用 `snapshot`

提醒：

- 只是讨论、草稿、假设计划时不要记录。
- 明确要记录、保存、沉淀时再写入成长护照。
- `action done` 表示真的完成了一个行动，不要随便使用。
- `profile capture` 只沉淀事实，不初始化成长护照。
- 看到 `ok: true` 就表示记录成功。

## 可选：更换服务地址

```bash
lifeos configure \
  --base-url "https://your-lifeos-api.example.com" \
  --name "你的名字"
```

CLI 会从命令参数、环境变量和 `~/.lifeos/cli.env` 读取配置。

常用环境变量：

```bash
LIFEOS_CLI_BASE_URL=https://106.55.134.110/lifeos
LIFEOS_CLI_INSECURE_TLS=true
LIFEOS_USER_ID=...
LIFEOS_USER_TOKEN=...
LIFEOS_USER_NAME=...
```

使用自定义配置路径：

```bash
export LIFEOS_CLI_CONFIG="$HOME/.config/lifeos/cli.env"
```

## Development

```bash
python3 -m pip install -e .
lifeos schema
python3 -m unittest discover -s tests -v
```

## License

MIT
