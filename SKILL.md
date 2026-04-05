---
name: QZD
description: 控制视频创作软件。支持：搜索抖音爆款视频（根据关键词搜索热门视频、查找爆款内容）、提取抖音视频文案、改写文案、生成语音、生成数字人视频、生成字幕、添加字幕、添加背景音乐、生成封面、生成标题标签、一键发布、全自动执行、数字人管理（刷新/添加/删除）、音色管理（刷新/添加/删除）、设置本地视频/封面路径。当用户说"帮我找爆款视频"、"搜索热门视频"、"查找XX类的视频"时，使用 search_douyin 操作。通过自然语言指令操控软件完成视频内容创作全流程。
---

# 视频创作软件控制

通过 HTTP API 控制运行中的视频创作桌面软件，实现自动化操作。

## ⚠️ 核心执行规则（必须严格遵守）

### 规则 1：执行阶段禁止提问
一旦进入执行阶段（用户已确认开始，或用户直接下达了明确的操作指令），你必须：
- 直接执行所有步骤，中间不得向用户提问、请求确认或等待回复
- 不得出现"是否继续？"、"你确定吗？"、"要不要xxx？"等任何形式的提问
- 如果某个参数缺失，使用软件当前已有的配置（通过 ui_state 可查询），不要停下来问用户
- 如果某个步骤失败，直接报告错误并继续执行后续步骤，不要问用户怎么处理

### 规则 2：禁止评价和建议
你是一个忠实的执行者，不是评审员。你必须：
- 只输出脚本返回的实际结果，不对结果做任何主观评价
- 不得说"效果不太好"、"建议重新生成"、"可以优化"等评价性语言
- 不得建议用户重试、修改或优化任何步骤的输出
- 不得对文案质量、语音效果、视频效果、封面效果等做任何点评
- 执行完成后，简洁报告每个步骤的结果（成功/失败），不要添加任何额外建议

### 规则 3：配置确认流程（仅限准备阶段）
当用户要求执行涉及语音生成或视频生成的流程时（包括 generate_voice、generate_video、execute_all、或完整流程），在开始执行前：
1. 先调用 `ui_state` 查询当前软件配置
2. 将关键配置信息汇总展示给用户，包括：
   - 当前选择的音色
   - 当前选择的数字人形象
   - 改写模式
   - 字幕设置（字体、字号、颜色等）
   - BGM 设置
   - 封面设置
   - 发布平台设置
3. 告诉用户"当前配置如上，如需调整请告诉我，确认无误请说开始"
4. 等用户确认后，进入执行阶段，后续所有步骤一口气跑完，不再提问

**例外情况：** 如果用户明确说了"直接开始"、"不用确认"、"用默认配置"等类似表述，跳过配置确认，直接进入执行阶段。

### 规则 4：简洁输出
- 执行过程中只输出关键进度信息，不要啰嗦
- 每个步骤完成后用一行简要说明结果
- 最终汇总用简短的清单格式，例如：
  ```
  ✅ 文案改写完成
  ✅ 语音生成完成
  ✅ 视频生成完成
  ✅ 字幕生成并添加完成
  ✅ BGM 添加完成
  ✅ 封面生成完成
  ✅ 标题标签生成完成
  ```

## 核心能力速查

| 用户意图 | 对应操作 |
|---------|---------|
| 找爆款视频、搜索热门视频、查找XX类视频 | search_douyin |
| 提取视频文案 | extract_text |
| 改写文案 | rewrite_text |
| 生成语音/视频/字幕/封面 | generate_voice / generate_video / create_subtitle / generate_cover |
| 发布视频 | publish |
| 全自动执行 | execute_all |

## 前提条件

- 视频创作软件必须已启动（登录界面或主界面均可）
- 软件会在本地 18900 端口提供 API 服务
- 如果软件处于登录界面，需要先执行 login 操作

## Usage

使用总入口脚本执行操作：

```bash
uv run /path/to/scripts/operate.py --action <action_name> [参数...]
```

## 支持的操作

### 0. 登录 (login)

输入账号密码登录软件。软件界面会自动填入账号密码并完成登录流程。

```bash
uv run /path/to/scripts/operate.py --action login --account "账号" --password "密码"
```

参数说明：
- `--account`（必填）：登录账号
- `--password`（必填）：登录密码

输出：登录成功后软件会自动进入主界面。

### 1. 提取文案 (extract_text)

从抖音视频链接或本地视频中提取文案内容。

```bash
uv run /path/to/scripts/operate.py --action extract_text --url "抖音分享链接或本地视频路径" [--url-type "抖音分享链接"|"本地视频路径"]
```

参数说明：
- `--url`（必填）：抖音分享链接 或 本地视频文件路径
- `--url-type`（可选）：链接类型，默认 "抖音分享链接"。如果是本地文件则传 "本地视频路径"

示例：
```bash
# 抖音链接
uv run /path/to/scripts/operate.py --action extract_text --url "https://v.douyin.com/xxxxx"

# 本地视频
uv run /path/to/scripts/operate.py --action extract_text --url "C:/videos/test.mp4" --url-type "本地视频路径"
```

输出：提取成功后会打印提取到的文案内容，同时软件界面上的文案输入框会自动更新显示。

### 2. 改写文案 (rewrite_text)

对文案进行 AI 改写。

```bash
uv run /path/to/scripts/operate.py --action rewrite_text --text "要改写的文案内容" [--mode "自动仿写"|"自定义指令仿写"|"完全一致"] [--prompt "自定义改写指令"]
```

参数说明：
- `--text`（必填）：要改写的原始文案
- `--mode`（可选）：改写模式，默认 "自动仿写"
  - "自动仿写"：AI 自动改写
  - "自定义指令仿写"：根据用户提供的 prompt 改写（需同时提供 --prompt）
  - "完全一致"：不做修改，原样返回
- `--prompt`（可选）：自定义改写指令，仅在 mode 为 "自定义指令仿写" 时生效

示例：
```bash
# 自动改写
uv run /path/to/scripts/operate.py --action rewrite_text --text "今天天气真好，适合出去玩"

# 自定义指令改写
uv run /path/to/scripts/operate.py --action rewrite_text --text "今天天气真好" --mode "自定义指令仿写" --prompt "改成更加活泼的语气"
```

输出：改写成功后会打印改写后的文案，同时软件界面上的改写文案框会自动更新。

### 3. 查询任务状态 (status)

查询某个任务的执行状态。

```bash
uv run /path/to/scripts/operate.py --action status --task-id "任务ID"
```

### 4. 健康检查 (ping)

检查软件 API 服务是否正常运行。

```bash
uv run /path/to/scripts/operate.py --action ping
```

### 5. 生成语音 (generate_voice)

根据当前改写后的文案生成语音。需要先完成文案提取和改写。

```bash
uv run /path/to/scripts/operate.py --action generate_voice
```

输出：生成成功后软件界面会自动加载音频，返回音频文件路径。

### 6. 生成数字人视频 (generate_video)

使用生成的音频和选定的数字人模型生成视频。需要先完成语音生成。

```bash
uv run /path/to/scripts/operate.py --action generate_video
```

输出：生成成功后软件界面会自动加载视频，返回视频文件路径。

### 7. 生成字幕 (create_subtitle)

根据音频生成字幕文件。需要先完成语音生成。

```bash
uv run /path/to/scripts/operate.py --action create_subtitle
```

输出：生成成功后软件界面会显示字幕内容。

### 8. 添加字幕到视频 (add_subtitle)

将生成的字幕添加到视频中。需要先完成字幕生成和视频生成。

```bash
uv run /path/to/scripts/operate.py --action add_subtitle
```

输出：成功后返回添加字幕后的视频路径。

### 9. 添加背景音乐 (add_bgm)

为视频添加背景音乐。需要先完成视频生成。

```bash
uv run /path/to/scripts/operate.py --action add_bgm
```

输出：成功后返回添加BGM后的视频路径。

### 10. 生成封面 (generate_cover)

为视频生成封面图片。

```bash
uv run /path/to/scripts/operate.py --action generate_cover
```

输出：成功后返回封面图片路径。

### 11. 生成标题标签 (generate_title_tags)

使用 AI 根据文案内容生成标题和标签。

```bash
uv run /path/to/scripts/operate.py --action generate_title_tags
```

输出：成功后软件界面会自动填入生成的标题和标签。

### 12. 一键发布 (publish)

将视频发布到配置的平台（抖音、小红书、视频号等）。

```bash
uv run /path/to/scripts/operate.py --action publish
```

输出：发布成功后返回发布结果。

### 13. 全自动执行 (execute_all)

按顺序自动执行所有步骤：改写文案 → 生成语音 → 生成视频 → 生成字幕 → 添加字幕 → 添加BGM → 生成封面 → 生成标题标签。需要先完成文案提取。

```bash
uv run /path/to/scripts/operate.py --action execute_all
```

输出：全部步骤完成后返回最终结果。

### 14. 查询 UI 状态 (ui_state)

查询所有可控 UI 组件的当前状态，包括下拉框选项列表、复选框状态、输入框内容等。

```bash
uv run /path/to/scripts/operate.py --action ui_state
```

输出：返回 JSON 格式的所有 UI 组件状态，包含每个组件的类型、当前值、可选项等。

### 15. 设置 UI 组件 (ui_set)

设置指定 UI 组件的值，效果和用户手动操作完全一致。

```bash
uv run /path/to/scripts/operate.py --action ui_set --component "组件名" --value "值"
```

参数说明：
- `--component`（必填）：组件名称
- `--value`（必填）：要设置的值

支持的组件名称：

| 组件名 | 类型 | 说明 | 值示例 |
|--------|------|------|--------|
| share_link | text | 视频链接输入框 | "https://v.douyin.com/xxxxx" |
| url_type | combobox | 链接类型 | "抖音分享链接"/"本地视频路径" |
| rewrite_mode | radio | 改写模式 | "自动仿写"/"自定义指令"/"完全一致" |
| custom_prompt | text | 自定义改写提示词 | "改成活泼语气" |
| voice | combobox | 音色选择 | 音色名称（先用 ui_state 查询可选项） |
| avatar | combobox | 数字人模型 | 模型名称（先用 ui_state 查询可选项） |
| subtitle_font | combobox | 字幕字体 | 字体名称 |
| subtitle_font_size | spinbox | 字幕字号 | "100" |
| subtitle_font_color | color | 字幕字体颜色 | "#ffffff" |
| subtitle_outline_color | color | 字幕描边颜色 | "#000000" |
| subtitle_bottom_margin | spinbox | 字幕底部距离 | "500" |
| subtitle_highlight_color | color | 字幕高亮颜色 | "#ffd600" |
| subtitle_line_font_num | spinbox | 每行字数 | "5" |
| subtitle_chip_silence | checkbox | 剪辑气口 | "true"/"false" |
| subtitle_highlight | checkbox | 关键词高亮 | "true"/"false" |
| subtitle_add_shop | checkbox | 添加画中画 | "true"/"false" |
| subtitle_shop_path | text | 画中画素材路径 | "C:/素材/商品" |
| subtitle_effect | combobox | 字幕特效 | "无特效"/"随机组合"/"逐字弹出"等 |
| bgm_volume | slider | BGM音量(0-100) | "30" |
| bgm_no_use | checkbox | 不使用BGM | "true"/"false" |
| bgm_custom | checkbox | 自定义BGM | "true"/"false" |
| bgm_path | text | BGM文件路径 | "C:/music/bgm.mp3" |
| bgm_category | combobox | BGM分类 | 分类名称（先用 ui_state 查询可选项） |
| bgm_file | combobox | BGM音乐文件 | 音乐名称（先用 ui_state 查询可选项） |
| cover_no_use | checkbox | 不需要封面 | "true"/"false" |
| cover_use_ai | switch | AI生成封面 | "true"/"false" |
| cover_text | text | 封面文案 | "今日好物推荐" |
| cover_highlight_words | text | 封面高亮词 | "好物,推荐" |
| cover_font | combobox | 封面字体 | 字体名称 |
| cover_font_size | spinbox | 封面字号 | "200" |
| cover_font_color | color | 封面字体颜色 | "#ffffff" |
| cover_highlight_color | color | 封面高亮颜色 | "#ffd600" |
| cover_position | combobox | 封面文字位置 | "底部"/"中心"/"顶部" |
| cover_frame_time | spinbox | 封面截取时间点(秒) | "3" |
| publish_douyin | checkbox | 发布到抖音 | "true"/"false" |
| publish_shp | checkbox | 发布到视频号 | "true"/"false" |
| publish_xhs | checkbox | 发布到小红书 | "true"/"false" |
| descriptions_text | text | 标题标签文本 | "标题内容\n#标签1 #标签2" |

示例：
```bash
# 选择音色
uv run /path/to/scripts/operate.py --action ui_set --component voice --value "音色A"

# 设置字幕字号
uv run /path/to/scripts/operate.py --action ui_set --component subtitle_font_size --value "120"

# 关闭BGM
uv run /path/to/scripts/operate.py --action ui_set --component bgm_no_use --value "true"

# 选择发布平台
uv run /path/to/scripts/operate.py --action ui_set --component publish_douyin --value "true"
uv run /path/to/scripts/operate.py --action ui_set --component publish_xhs --value "false"
```

### 16. 刷新数字人列表 (refresh_avatars)

从云端获取最新的数字人列表，更新软件界面的数字人下拉框。

```bash
uv run /path/to/scripts/operate.py --action refresh_avatars
```

输出：返回当前可用的数字人名称列表。

### 17. 添加数字人 (add_avatar)

上传本地视频文件训练新的数字人模型。

```bash
uv run /path/to/scripts/operate.py --action add_avatar --video-path "C:/videos/avatar.mp4" --avatar-name "我的数字人"
```

参数说明：
- `--video-path`（必填）：本地视频文件路径
- `--avatar-name`（必填）：数字人名称

输出：训练完成后返回成功消息，数字人列表会自动刷新。

### 18. 删除数字人 (delete_avatar)

删除当前在下拉框中选中的数字人。操作不可恢复。

```bash
uv run /path/to/scripts/operate.py --action delete_avatar
```

提示：先用 `ui_set --component avatar --value "名称"` 选中要删除的数字人。

### 19. 刷新音色列表 (refresh_voices)

从云端获取最新的音色列表，更新软件界面的音色下拉框。

```bash
uv run /path/to/scripts/operate.py --action refresh_voices
```

输出：返回当前可用的音色名称列表。

### 20. 添加音色 (add_voice)

上传本地音频文件克隆新的音色。

```bash
uv run /path/to/scripts/operate.py --action add_voice --audio-path "C:/audio/voice.wav" --voice-name "我的音色"
```

参数说明：
- `--audio-path`（必填）：本地音频文件路径（支持 wav/mp3/m4a/webm）
- `--voice-name`（必填）：音色名称

输出：克隆完成后返回成功消息，音色列表会自动刷新。

### 21. 删除音色 (delete_voice)

删除当前在下拉框中选中的音色。操作不可恢复。

```bash
uv run /path/to/scripts/operate.py --action delete_voice
```

提示：先用 `ui_set --component voice --value "名称"` 选中要删除的音色。

### 22. 设置本地视频 (set_video)

直接设置本地视频文件路径，跳过文件选择对话框。

```bash
uv run /path/to/scripts/operate.py --action set_video --video-path "C:/videos/my_video.mp4"
```

参数说明：
- `--video-path`（必填）：本地视频文件路径

输出：设置成功后软件界面会自动加载并显示该视频。

### 23. 设置本地封面 (set_cover)

直接设置本地封面图片路径，跳过文件选择对话框。

```bash
uv run /path/to/scripts/operate.py --action set_cover --cover-path "C:/images/cover.jpg"
```

参数说明：
- `--cover-path`（必填）：本地封面图片路径（支持 png/jpg/jpeg）

输出：设置成功后软件界面会自动显示该封面图片。

### 24. 搜索抖音爆款视频 (search_douyin)

根据关键词搜索抖音视频，获取爆款视频列表（含播放量、点赞数、链接等信息）。用户可以从结果中选择一个视频链接，配合 extract_text 提取文案进入创作流程。

当用户说以下类似的话时，应该使用此操作：
- "帮我找一下情感类的爆款视频"
- "搜索口播类的热门视频"
- "查找励志类的视频"
- "帮我搜一下美食相关的抖音视频"
- "找一些爆款视频参考"
- "有什么热门的XX视频"

关键词提取规则：从用户的描述中提取核心搜索词，如"情感类的爆款视频"→ keyword="情感"，"口播类热门视频"→ keyword="口播"。

```bash
uv run /path/to/scripts/operate.py --action search_douyin --keyword "情感" [--max-count 9]
```

参数说明：
- `--keyword`（必填）：搜索关键词，如 "情感"、"口播"、"励志" 等
- `--max-count`（可选）：最多获取视频数量，默认 9

示例：
```bash
# 搜索情感类爆款视频
uv run /path/to/scripts/operate.py --action search_douyin --keyword "情感"

# 搜索20个口播类视频
uv run /path/to/scripts/operate.py --action search_douyin --keyword "口播" --max-count 20
```

输出：返回 JSON 格式的视频列表，每个视频包含：
- `aweme_id`：视频ID
- `desc`：视频描述/标题
- `share_url`：视频分享链接（可直接用于 extract_text）
- `likes`：点赞数
- `comments`：评论数
- `shares`：分享数
- `plays`：播放量
- `author`：作者昵称
- `author_id`：作者ID

注意：首次使用需要在弹出的浏览器中手动扫码登录抖音，登录状态会持久化保存。

## 典型工作流

### 搜索爆款 → 选择 → 创作流程（推荐）

当用户想找爆款视频来参考创作时，使用此流程：

1. search_douyin — 根据用户描述的关键词搜索抖音爆款视频
2. 将搜索结果（视频标题、作者、播放量、点赞数、链接）展示给用户
3. 用户选择一个感兴趣的视频后，用该视频的 share_url 执行 extract_text 提取文案
4. 后续进入改写 → 生成语音 → 生成视频 → 发布的完整流程

### 简单流程：提取并改写文案

1. 先执行 extract_text 提取文案
2. 等待任务完成，获取提取到的文案
3. 用提取到的文案执行 rewrite_text 改写
4. 等待改写完成，返回结果给用户

### 完整流程：从提取到发布（含配置确认）

**准备阶段（允许交互）：**
1. 用户提供视频链接或关键词
2. 如果是关键词，先 search_douyin 搜索，展示结果让用户选择
3. extract_text — 提取文案
4. 调用 ui_state 查询当前配置，向用户展示关键配置（音色、数字人、字幕、BGM、封面、发布平台）
5. 等待用户确认配置（如果用户要调整，用 ui_set 修改后再次展示）

**执行阶段（禁止交互，一口气跑完）：**
6. rewrite_text — 改写文案
7. generate_voice — 生成语音
8. generate_video — 生成数字人视频
9. create_subtitle — 生成字幕
10. add_subtitle — 添加字幕到视频
11. add_bgm — 添加背景音乐
12. generate_cover — 生成封面
13. generate_title_tags — 生成标题标签
14. publish — 发布（如果用户要求发布）
15. 输出简洁的执行结果汇总

或者在准备阶段完成后，直接使用 execute_all 一键完成步骤 6-13。

### 资源管理流程

- refresh_avatars — 刷新数字人列表，查看可用的数字人
- add_avatar — 上传视频训练新的数字人
- delete_avatar — 删除当前选中的数字人
- refresh_voices — 刷新音色列表，查看可用的音色
- add_voice — 上传音频克隆新的音色
- delete_voice — 删除当前选中的音色

## 错误处理

- 如果软件未启动，脚本会提示"无法连接到软件，请确保软件已启动"
- 如果任务执行失败，会返回具体的错误信息
- 任务超时（默认 5 分钟）会自动报告超时
- 遇到错误时直接报告，不要询问用户如何处理，不要建议重试

## 输出格式

所有操作的输出格式统一：
- 成功：`SUCCESS: <结果描述>`，后跟具体内容
- 失败：`ERROR: <错误描述>`
- 进度：`PROGRESS: <进度信息>`
