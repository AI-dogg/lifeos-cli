# LifeOS 成长护照 CLI

LifeOS CLI 是一个面向个人用户的成长护照记录工具。

它用于记录和查看你的计划、行动、目标、复盘、成果和重要经历。你可以自己用命令记录，也可以把配套 Skill 安装给 AI 助手，让 AI 帮你把成长信息沉淀进成长护照。

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
cp -R lifeos-cli/skills/lifeos-cli "$SKILLS_DIR/"
```

### 3. 注册并验证

第一次使用：

```bash
lifeos register --name "你的名字" --password "你的密码"
lifeos diagnose
```

## 常用方式

```bash
lifeos snapshot
lifeos plan save --date 2026-06-18 --action "09:00|写今日计划"
lifeos plan confirm --date 2026-06-18
lifeos action list --date 2026-06-18
lifeos fact add --dimension long_term_goal --statement "未来三年持续建设个人成长系统"
```

查看帮助：

```bash
lifeos help
```

## 可选：更换服务地址

```bash
lifeos configure \
  --base-url "https://your-lifeos-api.example.com" \
  --name "你的名字"
```

## Development

```bash
python3 -m pip install -e .
lifeos schema
python3 -m unittest discover -s tests -v
```

## License

MIT
