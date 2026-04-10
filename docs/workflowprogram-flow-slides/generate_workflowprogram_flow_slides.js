const path = require("path");
const PptxGenJS = require("pptxgenjs");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers/layout");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.company = "WorkflowProgram-CN";
pptx.subject = "WorkflowProgram overall flow and module map";
pptx.title = "WorkflowProgram 流程图文档";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const COLORS = {
  ink: "17324D",
  muted: "5B7083",
  soft: "EAF0F6",
  line: "B7C6D6",
  blue: "1F5A91",
  teal: "0E6E6E",
  amber: "A86218",
  red: "A13B3B",
  green: "1E6B45",
  bg: "F8FAFC",
  white: "FFFFFF",
  navy: "0F2740",
};

function addSlideFrame(slide, title, subtitle) {
  slide.background = { color: COLORS.bg };
  slide.addText(title, {
    x: 0.5,
    y: 0.28,
    w: 8.7,
    h: 0.45,
    fontFace: "Microsoft YaHei",
    fontSize: 25,
    bold: true,
    color: COLORS.navy,
    margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5,
      y: 0.77,
      w: 11.7,
      h: 0.25,
      fontFace: "Microsoft YaHei",
      fontSize: 10,
      color: COLORS.muted,
      margin: 0,
    });
  }
  slide.addShape(pptx.ShapeType.line, {
    x: 0.5,
    y: 1.05,
    w: 12.2,
    h: 0,
    line: { color: COLORS.line, pt: 1.2 },
  });
  slide.addText("WorkflowProgram-CN", {
    x: 10.9,
    y: 0.3,
    w: 1.8,
    h: 0.2,
    align: "right",
    fontFace: "Microsoft YaHei",
    fontSize: 10,
    color: COLORS.blue,
    bold: true,
    margin: 0,
  });
}

function addFooter(slide, page) {
  slide.addShape(pptx.ShapeType.line, {
    x: 0.5,
    y: 7.05,
    w: 12.2,
    h: 0,
    line: { color: COLORS.line, pt: 0.8 },
  });
  slide.addText(`第 ${page} 页`, {
    x: 11.8,
    y: 7.1,
    w: 0.8,
    h: 0.2,
    align: "right",
    fontFace: "Microsoft YaHei",
    fontSize: 9,
    color: COLORS.muted,
    margin: 0,
  });
}

function addRoundBox(slide, text, x, y, w, h, options = {}) {
  const fill = options.fill || COLORS.white;
  const line = options.line || COLORS.line;
  const color = options.color || COLORS.ink;
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: fill },
    line: { color: line, pt: options.linePt || 1.2 },
  });
  slide.addText(text, {
    x: x + 0.08,
    y: y + 0.05,
    w: w - 0.16,
    h: h - 0.1,
    align: options.align || "center",
    valign: options.valign || "mid",
    fontFace: "Microsoft YaHei",
    fontSize: options.fontSize || 12,
    bold: options.bold !== false,
    color,
    margin: options.margin === undefined ? 0.03 : options.margin,
  });
}

function addArrow(slide, x1, y1, x2, y2, color = COLORS.blue, label = "") {
  slide.addShape(pptx.ShapeType.line, {
    x: x1,
    y: y1,
    w: x2 - x1,
    h: y2 - y1,
    line: {
      color,
      pt: 1.5,
      endArrowType: "triangle",
    },
  });
  if (label) {
    slide.addText(label, {
      x: Math.min(x1, x2),
      y: Math.min(y1, y2) - 0.18,
      w: Math.abs(x2 - x1) + 0.2,
      h: 0.18,
      align: "center",
      fontFace: "Microsoft YaHei",
      fontSize: 9,
      color,
      margin: 0,
    });
  }
}

function addBulletList(slide, x, y, w, lines, options = {}) {
  const fontSize = options.fontSize || 12;
  const lineGap = options.lineGap || 0.3;
  lines.forEach((line, index) => {
    slide.addText(`• ${line}`, {
      x,
      y: y + index * lineGap,
      w,
      h: 0.22,
      fontFace: "Microsoft YaHei",
      fontSize,
      color: options.color || COLORS.ink,
      bold: false,
      margin: 0,
      valign: "mid",
    });
  });
}

function addLaneLabel(slide, text, x, y, w, h, fill, color) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.05,
    fill: { color: fill },
    line: { color: fill, pt: 1 },
  });
  slide.addText(text, {
    x,
    y: y + 0.08,
    w,
    h: h - 0.16,
    fontFace: "Microsoft YaHei",
    fontSize: 14,
    bold: true,
    color,
    align: "center",
    margin: 0,
  });
}

function finalizeSlide(slide) {
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function buildCover() {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 1.35,
    fill: { color: COLORS.navy },
    line: { color: COLORS.navy, pt: 0 },
  });
  slide.addText("WorkflowProgram 流程图文档", {
    x: 0.65,
    y: 0.48,
    w: 7.8,
    h: 0.45,
    fontFace: "Microsoft YaHei",
    fontSize: 26,
    bold: true,
    color: COLORS.white,
    margin: 0,
  });
  slide.addText("从用户触发、skill 路由到脚本控制面与验证链的整体说明", {
    x: 0.65,
    y: 1.65,
    w: 8.5,
    h: 0.3,
    fontFace: "Microsoft YaHei",
    fontSize: 14,
    color: COLORS.muted,
    margin: 0,
  });
  addRoundBox(slide, "PLUGIN_ROOT\n插件模板、脚本、skills", 0.9, 4.8, 3.2, 1.05, {
    fill: "DCEBFA",
    line: "9DBDDD",
    color: COLORS.navy,
    fontSize: 15,
  });
  addRoundBox(slide, "TARGET_ROOT\n目标项目 .claude 资产", 5.05, 4.8, 3.2, 1.05, {
    fill: "DFF3EE",
    line: "9FD2C5",
    color: COLORS.green,
    fontSize: 15,
  });
  addRoundBox(slide, "RUN_ROOT\n运行证据与中间产物", 9.2, 4.8, 3.2, 1.05, {
    fill: "FCEAD8",
    line: "E5B98B",
    color: COLORS.amber,
    fontSize: 15,
  });
  addArrow(slide, 4.1, 5.33, 5.0, 5.33, COLORS.blue);
  addArrow(slide, 8.25, 5.33, 9.1, 5.33, COLORS.amber);
  slide.addText("核心结论：WorkflowProgram 不是一组 prompt，而是一条“AI 设计 + Python 控制面 + S5 判定”的产品化链路。", {
    x: 0.9,
    y: 3.3,
    w: 11.8,
    h: 0.45,
    fontFace: "Microsoft YaHei",
    fontSize: 17,
    color: COLORS.ink,
    bold: true,
    margin: 0,
  });
  addBulletList(slide, 0.95, 2.15, 11.5, [
    "显式入口 / 自然语言入口都会落到确定性的脚本链，而不是只靠模型自由发挥。",
    "控制面由 workflow-entry.py 与 workflow-runner.py 负责，最终 workflow 级结论由 S5 judge 给出。",
    "经验积累通过 lessons 与 constraints 回流，服务下一轮设计与验证。",
  ], { fontSize: 13, lineGap: 0.42 });
  addFooter(slide, 1);
  finalizeSlide(slide);
}

function buildOverallFlow() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "1. 总体主链", "用户请求如何流经 skill、入口脚本、runner 与验证链");
  addRoundBox(slide, "用户请求", 0.55, 1.5, 1.4, 0.68, { fill: "E8EEF5", line: "AEBFD1" });
  addRoundBox(slide, "自然语言请求", 2.25, 1.15, 1.9, 0.58, { fill: "E6F4FF", line: "A7C8E7", fontSize: 11 });
  addRoundBox(slide, "显式 /develop 或\nworkflowprogram-develop", 2.25, 1.95, 1.9, 0.78, {
    fill: "F1F7FF",
    line: "A7C8E7",
    fontSize: 11,
  });
  addRoundBox(slide, "workflowprogram-orchestrate", 4.55, 1.1, 2.15, 0.65, { fill: "DCEBFA", line: "9DBDDD" });
  addRoundBox(slide, "workflowprogram-develop /\naudit / iterate / validate", 4.55, 1.95, 2.15, 0.82, {
    fill: "DFF3EE",
    line: "9FD2C5",
    color: COLORS.green,
    fontSize: 11,
  });
  addRoundBox(slide, "workflow-entry.py run", 7.18, 1.62, 1.95, 0.72, { fill: "F6E8FF", line: "C5A6E8", color: "6D3A92" });
  addRoundBox(slide, "managed-assets.py", 9.45, 1.22, 1.6, 0.62, { fill: "FFF3E4", line: "E7BF89", color: COLORS.amber });
  addRoundBox(slide, "workflow-runner.py", 9.45, 2.05, 1.6, 0.62, { fill: "FFF3E4", line: "E7BF89", color: COLORS.amber });
  addRoundBox(slide, "workflowprogram-validate\n+ workflow-s5-judge.py", 11.25, 1.58, 1.55, 0.88, {
    fill: "FDEAE9",
    line: "D8A5A1",
    color: COLORS.red,
    fontSize: 10,
  });
  addArrow(slide, 1.95, 1.84, 2.25, 1.44, COLORS.blue);
  addArrow(slide, 1.95, 1.84, 2.25, 2.34, COLORS.blue);
  addArrow(slide, 4.15, 1.44, 4.55, 1.42, COLORS.blue);
  addArrow(slide, 4.15, 2.34, 4.55, 2.34, COLORS.green);
  addArrow(slide, 6.7, 1.43, 6.7, 2.2, COLORS.blue);
  addArrow(slide, 6.7, 2.34, 7.18, 1.98, COLORS.green);
  addArrow(slide, 9.13, 1.98, 9.45, 1.54, COLORS.amber);
  addArrow(slide, 9.13, 1.98, 9.45, 2.36, COLORS.amber);
  addArrow(slide, 11.05, 2.36, 11.25, 2.02, COLORS.red);

  addRoundBox(slide, "TARGET_ROOT/.claude", 1.1, 4.3, 2.4, 0.72, { fill: "DFF3EE", line: "9FD2C5", color: COLORS.green });
  addRoundBox(slide, "RUN_ROOT/state.json\nRUN_ROOT/events.jsonl\nrunner-summary.json", 4.2, 4.1, 2.75, 1.05, {
    fill: "FFF3E4",
    line: "E7BF89",
    color: COLORS.amber,
    fontSize: 11,
  });
  addRoundBox(slide, "validation-runtime-report.md\ns5-validation-summary.json", 7.55, 4.18, 2.8, 0.9, {
    fill: "FDEAE9",
    line: "D8A5A1",
    color: COLORS.red,
    fontSize: 11,
  });
  addRoundBox(slide, "lessons.md / constraints.md", 10.95, 4.3, 1.9, 0.72, { fill: "E8EEF5", line: "AEBFD1" });
  addArrow(slide, 10.25, 4.62, 10.95, 4.62, COLORS.red);
  addArrow(slide, 3.55, 4.66, 4.2, 4.66, COLORS.green);
  addArrow(slide, 6.95, 4.62, 7.55, 4.62, COLORS.amber);

  addBulletList(slide, 0.75, 5.75, 12.0, [
    "自然语言请求优先进入 orchestrate，再被 route-intent.py 路由到叶子 skill。",
    "显式 /develop 或 workflowprogram-develop 不会回跳到 orchestrate，它们直接进入 develop 主链。",
    "workflow-entry.py 是 skill 与控制面脚本之间的桥，workflow-runner.py 只负责确定性的 stage 转移与状态落盘。",
  ], { fontSize: 12, lineGap: 0.34 });
  addFooter(slide, 2);
  finalizeSlide(slide);
}

function buildTriggerRouting() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "2. 模块一：触发与路由", "重点回答：develop 不会跳到 orchestrate，只有自然语言请求会先经过 orchestrate");
  addRoundBox(slide, "显式入口", 0.7, 1.45, 2.2, 0.55, { fill: "EAF0F6", line: COLORS.line, fontSize: 14 });
  addRoundBox(slide, "/develop", 0.9, 2.2, 1.1, 0.6, { fill: COLORS.white, line: "A7C8E7", color: COLORS.blue });
  addRoundBox(slide, "workflowprogram-develop", 2.05, 2.2, 1.95, 0.6, { fill: COLORS.white, line: "A7C8E7", color: COLORS.blue, fontSize: 10 });
  addRoundBox(slide, "直接进入 develop 主链", 1.25, 3.2, 2.1, 0.65, { fill: "DFF3EE", line: "9FD2C5", color: COLORS.green });
  addArrow(slide, 1.45, 2.8, 2.15, 3.2, COLORS.blue);
  addArrow(slide, 3.0, 2.8, 2.55, 3.2, COLORS.blue);

  addRoundBox(slide, "自然语言入口", 5.15, 1.45, 2.3, 0.55, { fill: "EAF0F6", line: COLORS.line, fontSize: 14 });
  addRoundBox(slide, "workflowprogram-orchestrate", 5.3, 2.15, 2.2, 0.62, { fill: "DCEBFA", line: "9DBDDD", fontSize: 11 });
  addRoundBox(slide, "route-intent.py", 5.7, 3.08, 1.35, 0.56, { fill: COLORS.white, line: "A7C8E7", color: COLORS.blue });
  addRoundBox(slide, "workflowprogram-develop /\naudit / iterate / validate", 5.05, 4.0, 2.7, 0.82, {
    fill: "DFF3EE",
    line: "9FD2C5",
    color: COLORS.green,
    fontSize: 11,
  });
  addArrow(slide, 6.4, 2.77, 6.4, 3.08, COLORS.blue);
  addArrow(slide, 6.4, 3.64, 6.4, 4.0, COLORS.blue);

  addRoundBox(slide, "严格模式", 8.55, 1.6, 1.45, 0.45, { fill: "FFF3E4", line: "E7BF89", color: COLORS.amber, fontSize: 12 });
  addRoundBox(slide, "若关键词并列或零分\nroute-intent.py 返回歧义", 8.35, 2.25, 1.9, 0.72, {
    fill: COLORS.white,
    line: "E7BF89",
    color: COLORS.amber,
    fontSize: 10,
  });
  addRoundBox(slide, "strict 模式下阻断\n非 strict 模式下回退到 develop", 8.2, 3.35, 2.2, 0.86, {
    fill: "FFF3E4",
    line: "E7BF89",
    color: COLORS.amber,
    fontSize: 10,
  });
  addArrow(slide, 9.3, 2.97, 9.3, 3.35, COLORS.amber);

  addRoundBox(slide, "结论", 0.8, 5.55, 1.0, 0.4, { fill: "EAF0F6", line: COLORS.line, fontSize: 12 });
  addBulletList(slide, 1.0, 6.05, 11.2, [
    "不存在“develop 先调用 orchestrate 再回来”的运行链路。",
    "orchestrate 只承担自然语言总入口；叶子 skill 负责实际业务主链。",
    "即便显式进入 develop，workflow-entry.py 仍会再调用 route-intent.py，用于记录路由证据和检查冲突，而不是切换 skill。",
  ], { fontSize: 12, lineGap: 0.32 });
  addFooter(slide, 3);
  finalizeSlide(slide);
}

function buildAiPythonHandoff() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "3. 模块二：AI 与 Python 如何切换", "切换媒介不是函数互调，而是 shell 命令 + 产物文件 + JSON 摘要");
  addLaneLabel(slide, "AI / Skill 层", 0.65, 1.35, 1.55, 0.55, "DCEBFA", COLORS.navy);
  addLaneLabel(slide, "Python / 控制面层", 0.65, 4.15, 1.55, 0.55, "FFF3E4", COLORS.amber);
  slide.addShape(pptx.ShapeType.line, {
    x: 2.35,
    y: 3.25,
    w: 10.0,
    h: 0,
    line: { color: COLORS.line, pt: 1.2, dash: "dash" },
  });

  const aiBoxes = [
    { text: "读取 command / skill 文本", x: 2.55, y: 1.45, w: 1.65 },
    { text: "澄清需求\n设计 workflow-spec", x: 4.45, y: 1.45, w: 1.8 },
    { text: "生成 candidate\n.claude 资产", x: 6.55, y: 1.45, w: 1.7 },
    { text: "执行 shell 命令\nworkflow-entry.py run", x: 8.55, y: 1.45, w: 2.1 },
    { text: "读取结果\n继续 validate / 汇报", x: 11.0, y: 1.45, w: 1.8 },
  ];
  aiBoxes.forEach((box, index) => {
    addRoundBox(slide, box.text, box.x, box.y, box.w, 0.78, { fill: COLORS.white, line: "A7C8E7", color: COLORS.blue, fontSize: 11 });
    if (index < aiBoxes.length - 1) {
      addArrow(slide, box.x + box.w, 1.84, aiBoxes[index + 1].x, 1.84, COLORS.blue);
    }
  });

  const pyBoxes = [
    { text: "route-intent.py", x: 2.75, y: 4.25, w: 1.35 },
    { text: "validate-workflow-spec.py", x: 4.3, y: 4.25, w: 1.8 },
    { text: "generate-workflow-view.py", x: 6.35, y: 4.25, w: 1.85 },
    { text: "managed-assets.py", x: 8.45, y: 4.25, w: 1.55 },
    { text: "workflow-runner.py", x: 10.2, y: 4.25, w: 1.65 },
    { text: "validate-run-state.py", x: 12.02, y: 4.25, w: 1.1 },
  ];
  pyBoxes.forEach((box, index) => {
    addRoundBox(slide, box.text, box.x, box.y, box.w, 0.72, { fill: COLORS.white, line: "E7BF89", color: COLORS.amber, fontSize: 10 });
    if (index < pyBoxes.length - 1) {
      addArrow(slide, box.x + box.w, 4.61, pyBoxes[index + 1].x, 4.61, COLORS.amber);
    }
  });

  addArrow(slide, 9.6, 2.23, 9.15, 4.25, COLORS.red);
  addArrow(slide, 11.0, 4.97, 11.7, 2.23, COLORS.green);

  addRoundBox(slide, "文件 / JSON 交接物", 2.6, 5.55, 2.0, 0.42, { fill: "EAF0F6", line: COLORS.line, fontSize: 12 });
  addBulletList(slide, 2.7, 6.0, 9.8, [
    "AI -> Python：通过 shell 命令传参，例如 --spec、--run-root、--entry-skill、--request。",
    "Python -> AI：通过 entry-orchestration-summary.json、state.json、events.jsonl、runner-summary.json、validation 报告交回。",
    "这意味着设计是 AI 主导的，控制面语义与约束执行是 Python 主导的。",
  ], { fontSize: 12, lineGap: 0.32 });
  addFooter(slide, 4);
  finalizeSlide(slide);
}

function buildDevelopStages() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "4. 模块三：develop 主链与阶段模型", "S1-S6 中，哪些环节更偏 AI，哪些环节更偏脚本");
  const stages = [
    { slot: "S1", title: "需求澄清", color: "DCEBFA", line: "9DBDDD", note: "AI 主导\n草案 -> validate-workflow-draft" },
    { slot: "S2", title: "上下文研究", color: "DFF3EE", line: "9FD2C5", note: "AI / 子代理主导\n收集 repo 与领域上下文" },
    { slot: "S3", title: "YAML 设计", color: "F6E8FF", line: "C5A6E8", note: "AI 产出\nvalidate-workflow-spec 把关" },
    { slot: "S4", title: "受控写入", color: "FFF3E4", line: "E7BF89", note: "workflow-entry + managed-assets\n冲突则停在这里" },
    { slot: "S5", title: "验证判定", color: "FDEAE9", line: "D8A5A1", note: "workflowprogram-validate\n+ workflow-s5-judge" },
    { slot: "S6", title: "经验回流", color: "EAF0F6", line: "AEBFD1", note: "lessons / constraints\n形成下一轮输入" },
  ];
  let x = 0.75;
  stages.forEach((stage, index) => {
    addRoundBox(slide, `${stage.slot}\n${stage.title}`, x, 1.55, 1.75, 0.88, {
      fill: stage.color,
      line: stage.line,
      fontSize: 16,
    });
    addRoundBox(slide, stage.note, x, 2.72, 1.75, 1.08, {
      fill: COLORS.white,
      line: stage.line,
      color: COLORS.ink,
      fontSize: 10,
      bold: false,
    });
    if (index < stages.length - 1) {
      addArrow(slide, x + 1.75, 1.99, x + 1.98, 1.99, COLORS.blue);
    }
    x += 2.05;
  });
  addRoundBox(slide, "实际固定脚本主链", 0.85, 4.4, 1.6, 0.42, { fill: "EAF0F6", line: COLORS.line, fontSize: 12 });
  addBulletList(slide, 1.0, 4.9, 11.4, [
    "AI 负责设计与候选产物；一旦进入 S4，workflow-entry.py 就把主链固定为脚本执行。",
    "workflow-runner.py 负责 stage 转移、required_evidence 检查、approval_status 与 failure_kind 等控制面状态。",
    "S5 不是 runner 的职责；S5 主判定在 workflowprogram-validate / workflow-s5-judge.py。",
    "S6 的目标不是重跑流程，而是把本次运行提炼成 lessons、constraints candidates 和用户进度摘要。",
  ], { fontSize: 12, lineGap: 0.31 });
  addFooter(slide, 5);
  finalizeSlide(slide);
}

function buildEntryRunner() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "5. 模块四：workflow-entry.py 与 workflow-runner.py", "入口编排层负责串脚本，runner 负责控制面状态");
  addRoundBox(slide, "workflow-entry.py run", 0.8, 1.45, 2.5, 0.7, { fill: "F6E8FF", line: "C5A6E8", color: "6D3A92", fontSize: 18 });
  addBulletList(slide, 0.95, 2.35, 3.0, [
    "解析显式 entry_skill 与 intent",
    "校验 workflow-spec.yaml",
    "生成 workflow-view.md",
    "develop 时执行 managed apply",
    "无冲突后调用 workflow-runner.py run",
    "最后校验 state.json",
  ], { fontSize: 11, lineGap: 0.29 });

  addRoundBox(slide, "workflow-runner.py run", 4.35, 1.45, 2.55, 0.7, { fill: "FFF3E4", line: "E7BF89", color: COLORS.amber, fontSize: 18 });
  addBulletList(slide, 4.5, 2.35, 3.1, [
    "按 intent_flows 计算实际 stage 链",
    "执行 S0-S6 控制面转移",
    "写 state.json / events.jsonl",
    "写 runner-summary.json",
    "检查 required_evidence",
    "校验 failure_kind 与环境 skip 语义",
  ], { fontSize: 11, lineGap: 0.29 });

  addRoundBox(slide, "关键边界", 8.05, 1.45, 1.5, 0.45, { fill: "EAF0F6", line: COLORS.line, fontSize: 13 });
  addBulletList(slide, 8.1, 2.1, 4.1, [
    "develop 流程若 managed-assets.py 发现冲突，entry 会停在 runner 之前。",
    "runner 只负责控制面，不负责 workflow 级最终 verdict。",
    "显式 develop 不会切回 orchestrate；route-intent 只用于证据与冲突检查。",
    "runner 结束后仍要经过 validate-run-state.py 与 S5 judge。",
  ], { fontSize: 11, lineGap: 0.3 });

  addRoundBox(slide, "主要产物", 0.95, 5.25, 1.3, 0.42, { fill: "EAF0F6", line: COLORS.line, fontSize: 12 });
  // layout helper 对 table 的内部对象会按 EMU 坐标读取，可能误报 out-of-bounds；
  // 这里的表格盒子本身在 slide 宽度之内，保留 warning 仅作为调试信息。
  slide.addTable(
    [
      [{ text: "文件" }, { text: "产生者" }, { text: "作用" }],
      [{ text: "entry-orchestration-summary.json" }, { text: "workflow-entry.py" }, { text: "记录这次为什么走到某个入口与脚本链" }],
      [{ text: "state.json / events.jsonl" }, { text: "workflow-runner.py" }, { text: "控制面状态与事件流" }],
      [{ text: "runner-summary.json" }, { text: "workflow-runner.py" }, { text: "摘要化的 transition / artifact 统计" }],
    ],
    {
      x: 0.95,
      y: 5.75,
      w: 11.8,
      border: { pt: 1, color: COLORS.line },
      fill: COLORS.white,
      fontFace: "Microsoft YaHei",
      fontSize: 11,
      color: COLORS.ink,
      rowH: 0.34,
      bold: true,
      margin: 0.05,
    }
  );
  addFooter(slide, 6);
  finalizeSlide(slide);
}

function buildValidationChain() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "6. 模块五：验证链与 S5 主判定", "区分控制面证据、动态 harness、以及 workflow 级 verdict");
  addRoundBox(slide, "RUN_ROOT 证据", 0.8, 1.55, 1.7, 0.62, { fill: "FFF3E4", line: "E7BF89", color: COLORS.amber, fontSize: 15 });
  addRoundBox(slide, "workflowprogram-validate", 3.0, 1.55, 2.15, 0.62, { fill: "FDEAE9", line: "D8A5A1", color: COLORS.red, fontSize: 14 });
  addRoundBox(slide, "workflow-s5-judge.py", 5.75, 1.55, 1.9, 0.62, { fill: "FDEAE9", line: "D8A5A1", color: COLORS.red, fontSize: 14 });
  addRoundBox(slide, "validation-runtime-report.md\ns5-validation-summary.json", 8.2, 1.4, 2.45, 0.92, {
    fill: COLORS.white,
    line: "D8A5A1",
    color: COLORS.red,
    fontSize: 11,
  });
  addRoundBox(slide, "lessons / constraints 候选", 11.05, 1.55, 1.9, 0.62, { fill: "EAF0F6", line: COLORS.line, color: COLORS.navy, fontSize: 12 });
  addArrow(slide, 2.5, 1.86, 3.0, 1.86, COLORS.amber);
  addArrow(slide, 5.15, 1.86, 5.75, 1.86, COLORS.red);
  addArrow(slide, 7.65, 1.86, 8.2, 1.86, COLORS.red);
  addArrow(slide, 10.65, 1.86, 11.05, 1.86, COLORS.blue);

  addRoundBox(slide, "runtime_smoke.py", 2.55, 3.35, 1.7, 0.6, { fill: "DCEBFA", line: "9DBDDD", color: COLORS.blue, fontSize: 14 });
  addRoundBox(slide, "runtime_host.py", 4.6, 3.35, 1.45, 0.6, { fill: "DCEBFA", line: "9DBDDD", color: COLORS.blue, fontSize: 14 });
  addRoundBox(slide, "claude_cli /\ncommand_adapter /\nfixture_host", 6.45, 3.18, 1.9, 0.94, {
    fill: COLORS.white,
    line: "9DBDDD",
    color: COLORS.blue,
    fontSize: 10,
  });
  addRoundBox(slide, "transcript.md\nbefore/after snapshot\nprovider 结果", 8.8, 3.18, 2.15, 0.94, {
    fill: COLORS.white,
    line: "9DBDDD",
    color: COLORS.blue,
    fontSize: 10,
  });
  addArrow(slide, 4.25, 3.66, 4.6, 3.66, COLORS.blue);
  addArrow(slide, 6.05, 3.66, 6.45, 3.66, COLORS.blue);
  addArrow(slide, 8.35, 3.66, 8.8, 3.66, COLORS.blue);
  addArrow(slide, 9.85, 3.18, 6.8, 2.17, COLORS.blue);

  addBulletList(slide, 0.95, 5.15, 11.6, [
    "workflowprogram-validate 是 S5 主入口，workflow-s5-judge.py 才是实际 contract-aware 判定器。",
    "runtime_smoke.py 不是主判定来源；它负责真实运行、抓 transcript / snapshot / provider 输出，并把这些证据补给 judge。",
    "state.json / events.jsonl 属于控制面证据，S5 会消费它们，但不拥有它们。",
  ], { fontSize: 12, lineGap: 0.34 });
  addFooter(slide, 7);
  finalizeSlide(slide);
}

function buildModuleMap() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "7. 模块六：关键 skill / 脚本地图", "一页看清每个模块的职责、输入与输出");
  // 同上：这一页是大表格汇总，helper 对 table 内部坐标的边界检查会产生误报。
  slide.addTable(
    [
      [{ text: "模块" }, { text: "核心文件" }, { text: "主要职责" }, { text: "典型输出" }],
      [{ text: "总入口" }, { text: "workflowprogram-orchestrate" }, { text: "承接自然语言请求并路由到叶子 skill" }, { text: "路由结论、目标 skill" }],
      [{ text: "叶子设计入口" }, { text: "workflowprogram-develop / /develop" }, { text: "澄清需求、生成 spec 与 candidate 资产" }, { text: "workflow-spec.yaml, candidate/.claude" }],
      [{ text: "意图路由" }, { text: "route-intent.py" }, { text: "把请求映射到 develop / audit / iterate / validate" }, { text: "intent, entry_skill, confidence" }],
      [{ text: "确定性入口" }, { text: "workflow-entry.py" }, { text: "把 prompt 层顺序固定成脚本链" }, { text: "entry-orchestration-summary.json" }],
      [{ text: "受控写入" }, { text: "managed-assets.py" }, { text: "plan / apply-staged，处理覆盖与冲突" }, { text: "managed-change-plan/result" }],
      [{ text: "控制面" }, { text: "workflow-runner.py" }, { text: "stage 转移、状态落盘、required_evidence 检查" }, { text: "state.json, events.jsonl, runner-summary.json" }],
      [{ text: "状态校验" }, { text: "validate-run-state.py" }, { text: "校验 runner 落盘状态是否合法" }, { text: "run-state verdict" }],
      [{ text: "S5 主判定" }, { text: "workflowprogram-validate + workflow-s5-judge.py" }, { text: "根据 runtime_contract / test_contract 给 workflow verdict" }, { text: "runtime report, s5 summary" }],
      [{ text: "动态 harness" }, { text: "runtime_smoke.py + runtime_host.py" }, { text: "真跑一轮并补 transcript / snapshot / provider 证据" }, { text: "transcript, snapshots, smoke summary" }],
      [{ text: "经验回流" }, { text: "lessons.md / constraints.md" }, { text: "沉淀可复用经验，影响下一轮" }, { text: "lessons, rules" }],
    ],
    {
      x: 0.55,
      y: 1.35,
      w: 12.2,
      border: { pt: 1, color: COLORS.line },
      fill: COLORS.white,
      fontFace: "Microsoft YaHei",
      fontSize: 10,
      color: COLORS.ink,
      rowH: 0.38,
      margin: 0.04,
      bold: true,
    }
  );
  addFooter(slide, 8);
  finalizeSlide(slide);
}

function buildFaq() {
  const slide = pptx.addSlide();
  addSlideFrame(slide, "8. 常见问题结论页", "把前面几页的关键信息压缩成可直接复述的答案");
  const qa = [
    {
      q: "Q1. develop 是怎么跳到 orchestrate 的？",
      a: "不会跳。自然语言请求优先进入 orchestrate；显式 /develop 或 workflowprogram-develop 直接进入 develop 主链。",
      fill: "DCEBFA",
      line: "9DBDDD",
    },
    {
      q: "Q2. AI 和 Python 是怎么来回切换的？",
      a: "通过 shell 命令与产物文件交接。AI 设计与决策，Python 固化约束、执行控制面、落状态与给判定。",
      fill: "FFF3E4",
      line: "E7BF89",
    },
    {
      q: "Q3. workflow-runner.py 是谁触发的？",
      a: "由 workflow-entry.py 在 run_runner() 中起子进程调用；develop 流程里还要先过 managed-assets 的冲突门禁。",
      fill: "FDEAE9",
      line: "D8A5A1",
    },
    {
      q: "Q4. 最终 workflow 是否按设计执行，由谁说了算？",
      a: "不是 runner，而是 workflowprogram-validate + workflow-s5-judge.py；runtime_smoke.py 只负责补动态证据。",
      fill: "EAF0F6",
      line: "AEBFD1",
    },
  ];
  let y = 1.55;
  qa.forEach((item) => {
    addRoundBox(slide, item.q, 0.8, y, 4.2, 0.58, {
      fill: item.fill,
      line: item.line,
      color: COLORS.navy,
      fontSize: 14,
      align: "left",
    });
    addRoundBox(slide, item.a, 5.3, y, 7.1, 0.58, {
      fill: COLORS.white,
      line: item.line,
      color: COLORS.ink,
      fontSize: 12,
      bold: false,
      align: "left",
      margin: 0.06,
    });
    y += 1.1;
  });
  addRoundBox(slide, "建议阅读顺序", 0.85, 5.85, 1.35, 0.4, { fill: "EAF0F6", line: COLORS.line, fontSize: 12 });
  addBulletList(slide, 1.0, 6.25, 11.2, [
    "先看“总体主链”和“触发与路由”，弄清 skill 之间谁先谁后。",
    "再看“AI 与 Python 切换”和“workflow-entry / runner”，理解真正的控制权交接点。",
    "最后看“验证链”和“文件地图”，对照代码读实现最省时间。",
  ], { fontSize: 12, lineGap: 0.3 });
  addFooter(slide, 9);
  finalizeSlide(slide);
}

async function main() {
  buildCover();
  buildOverallFlow();
  buildTriggerRouting();
  buildAiPythonHandoff();
  buildDevelopStages();
  buildEntryRunner();
  buildValidationChain();
  buildModuleMap();
  buildFaq();

  const outPath = path.join(__dirname, "workflowprogram_flow_overview.pptx");
  await pptx.writeFile({ fileName: outPath });
  console.log(`Wrote ${outPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
