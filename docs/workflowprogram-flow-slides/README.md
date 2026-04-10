# WorkflowProgram 流程图文档

这个目录存放用 `slides` skill 生成的 `WorkflowProgram` 流程图文档。

## 产物

- `generate_workflowprogram_flow_slides.js`
  - deck 源码
- `workflowprogram_flow_overview.pptx`
  - 生成后的演示文稿
- `pptxgenjs_helpers/`
  - 从 `slides` skill 复制过来的本地 helper

## 内容范围

这份 deck 主要回答 4 类问题：

1. 用户请求如何进入 `workflowprogram-orchestrate`、`workflowprogram-develop` 或历史 `/develop`
2. `workflow-entry.py`、`managed-assets.py`、`workflow-runner.py`、`workflowprogram-validate` 分别负责什么
3. AI 和 Python 脚本是如何切换控制权的
4. `RUN_ROOT`、`TARGET_ROOT`、`PLUGIN_ROOT` 与 S1-S6 阶段模型如何串起来

## 重新生成

在本目录执行：

```bash
npm install
npm run generate
```

## 渲染预览

如果本机装有 LibreOffice / `soffice`，可以继续执行：

```bash
python3 /mnt/c/Users/zhd/.codex/skills/slides/scripts/render_slides.py workflowprogram_flow_overview.pptx --output_dir rendered
python3 /mnt/c/Users/zhd/.codex/skills/slides/scripts/create_montage.py --input_dir rendered --output_file montage.png
python3 /mnt/c/Users/zhd/.codex/skills/slides/scripts/slides_test.py workflowprogram_flow_overview.pptx
```

当前这台机器还缺少 `pdf2image` / `soffice` 这类渲染依赖，因此生成 `.pptx` 没问题，但本地 PNG 渲染预览暂时无法执行。
