/**
 * GoalSlice 就这 — B2 可点击流程原型
 * 最小状态机，非生产代码
 */

const state = {
  screen: "home",
  clarifyStep: 0,
  clarifyAnswers: {},
  currentDay: 3,
  completedDays: [1, 2],
  goal: "",
  downgradeApplied: false,
  selectedOption: null,
  selectedDowngrade: null,
};

const CLARIFY_QUESTIONS = [
  {
    id: "goalType",
    question: "这个目标更接近哪一类？",
    options: ["转行 / 求职", "技能提升", "面试准备", "作品集建设", "个人品牌", "其他"],
  },
  {
    id: "weeklyOutcome",
    question: "如果只看这一周，你希望自己发生什么变化？",
    options: [
      "完成一个具体产物",
      "明确下一步方向",
      "开始行动，不再只想",
      "为面试 / 求职做一个准备动作",
      "解决一个卡点",
    ],
  },
  {
    id: "availableTime",
    question: "你每天大概能投入多久？",
    options: ["5 分钟", "15 分钟", "30 分钟", "60 分钟以上", "不固定，看当天状态"],
  },
  {
    id: "currentLevel",
    question: "你现在更接近哪种状态？",
    options: [
      "完全小白，不知道从哪开始",
      "有一点了解，但不系统",
      "已经做过一些尝试",
      "有一定基础，但缺少成果",
      "已经比较明确，只是缺少执行节奏",
    ],
  },
  {
    id: "failureReason",
    question: "过去类似目标最容易卡在哪里？",
    options: [
      "不知道第一步做什么",
      "计划太复杂，坚持不下去",
      "太忙，没有固定时间",
      "学了一堆，但没有产出",
      "容易想太多，迟迟不开始",
    ],
  },
];

const DEMO_SCENARIO = {
  goal: "我想提升自己的会议总结能力",
  questTitle: "从「会议听完就忘」到「能写出可执行的会议总结」",
  successCondition: "完成一份真实会议的总结稿（含背景、决议、待办）",
  headerShort: "练就会议总结力",
  feedbackAction: "四格模板练习",
  feedbackMeaning:
    "你第一次把「我想提升会议总结能力」从模糊感受，变成了可重复使用的结构。以后每场会都有抓手，而不是听完就散。",
  reviewBoss: "你不再只是「想写好纪要」，而是有了一份能直接用的总结方法",
  reviewItems: [
    "列出 3 场难总结的会议场景",
    "找出旧纪要里缺失的关键信息",
    "完成一次四格模板填空练习",
    "拆解一份优秀纪要范例",
    "写出一场会的 5 句核心结论",
  ],
  nextWeekTitle: "进入「文档写作副本」",
  nextWeekDesc: "把会议总结能力延伸到日常文档输出，练一份结构清晰的工作说明",
  observation: "你在填空和拆解类任务上完成度高，写完整段落时容易拖延。",
};

const WEEK_PLAN = [
  { day: 1, title: "列出最近 3 场会，标出最难总结的一场", time: "15 分钟" },
  { day: 2, title: "读一份旧纪要，圈出缺失的 3 个关键信息", time: "15 分钟" },
  { day: 3, title: "用「背景-讨论-决议-待办」四格模板，填空总结一场会", time: "15 分钟" },
  { day: 4, title: "找一份好纪要范例，标出 2 个可学习的写法", time: "20 分钟" },
  { day: 5, title: "用 5 句话写出一场会的核心结论", time: "15 分钟" },
  { day: 6, title: "整理成你的专属会议总结模板", time: "25 分钟" },
  { day: 7, title: "Boss 战：独立完成一场真实会议的总结稿", time: "30 分钟", boss: true },
];

const DAILY_TASK = {
  normal: {
    title: "用四格模板填空总结一场会",
    desc: "选一场你最近参加的会，按「背景 → 讨论 → 决议 → 待办」四格，每格写 1–2 句话。不用完美，先填满。",
    meaning:
      "会议总结难，往往难在不知道从何写起。四格模板把模糊感受变成固定结构，你先求「写完」，再求「写好」。",
    hasInput: true,
    inputPlaceholder: "贴上你的四格填空，或写下最难写的那一格…",
  },
  downgraded: {
    title: "5 分钟版：写下一场会的名字 + 1 个结论",
    desc: "回忆最近一场会，写下会议名称和你还记得的 1 个结论或待办。不用四格，两句话就够。",
    meaning: "今天先完成「开始记录」比完成「完美纪要」更重要。你已经迈出了最难的第一步。",
    hasInput: false,
  },
};

function $(sel) {
  return document.querySelector(sel);
}

function $$(sel) {
  return document.querySelectorAll(sel);
}

function showScreen(id) {
  state.screen = id;
  $$(".screen").forEach((el) => el.classList.remove("active"));
  const target = document.getElementById(`screen-${id}`);
  if (target) target.classList.add("active");
  updateHeader();
  window.scrollTo(0, 0);
}

function updateHeader() {
  const progress = state.completedDays.length;
  const pct = Math.round((progress / 7) * 100);
  const fill = $(".progress-bar-fill");
  const text = $(".progress-text");
  if (fill) fill.style.width = `${pct}%`;
  if (text) text.textContent = `${progress}/7`;

  const showFull = ["daily", "feedback", "hub", "preview", "review"].includes(state.screen);
  $(".header")?.classList.toggle("header--simple", state.screen === "home" || state.screen === "clarify");
  $(".header-center").style.display = showFull ? "block" : "none";
  $(".header-right").style.display = showFull ? "flex" : "none";
}

function renderClarify() {
  const q = CLARIFY_QUESTIONS[state.clarifyStep];
  $("#clarify-question").textContent = q.question;
  $("#step-label").textContent = `题 ${state.clarifyStep + 1}/${CLARIFY_QUESTIONS.length}`;

  const dots = $("#step-dots");
  dots.innerHTML = CLARIFY_QUESTIONS.map((_, i) => {
    let cls = "step-dot";
    if (i === state.clarifyStep) cls += " active";
    else if (i < state.clarifyStep) cls += " done";
    return `<span class="${cls}"></span>`;
  }).join("");

  const list = $("#option-list");
  list.innerHTML = q.options
    .map(
      (opt) =>
        `<div class="option-card${state.selectedOption === opt ? " selected" : ""}" data-value="${opt}">${opt}</div>`
    )
    .join("");

  list.querySelectorAll(".option-card").forEach((card) => {
    card.addEventListener("click", () => {
      state.selectedOption = card.dataset.value;
      renderClarify();
    });
  });

  const nextBtn = $("#btn-clarify-next");
  nextBtn.textContent = state.clarifyStep === CLARIFY_QUESTIONS.length - 1 ? "完成" : "下一题";
  nextBtn.disabled = !state.selectedOption;
}

function renderTimeline() {
  const list = $("#week-timeline");
  list.innerHTML = WEEK_PLAN.map((item) => {
    const done = state.completedDays.includes(item.day);
    const cls = ["timeline-item", done ? "done" : "", item.boss ? "boss" : ""].filter(Boolean).join(" ");
    return `
      <li class="${cls}">
        <div class="timeline-dot">${item.boss ? "★" : item.day}</div>
        <div class="timeline-content">
          <div class="timeline-title">${item.boss ? "Boss 战 · " : ""}${item.title}</div>
          <div class="timeline-desc">预计 ${item.time}</div>
        </div>
      </li>`;
  }).join("");
}

function applyDemoCopy() {
  const headerCenter = $(".header-center");
  if (headerCenter) headerCenter.textContent = DEMO_SCENARIO.headerShort;

  const previewTitle = $("#preview-title");
  if (previewTitle) previewTitle.textContent = DEMO_SCENARIO.questTitle;

  const previewCondition = $("#preview-condition");
  if (previewCondition) previewCondition.textContent = DEMO_SCENARIO.successCondition;

  const hubTitle = $("#hub-title");
  if (hubTitle) hubTitle.textContent = DEMO_SCENARIO.questTitle;

  const hubCondition = $("#hub-condition");
  if (hubCondition) hubCondition.textContent = `通关条件：${DEMO_SCENARIO.successCondition}`;

  const feedbackSub = $("#feedback-sub");
  if (feedbackSub) feedbackSub.textContent = `你今天完成的是「${DEMO_SCENARIO.feedbackAction}」`;

  const feedbackMeaning = $("#feedback-meaning");
  if (feedbackMeaning) feedbackMeaning.textContent = DEMO_SCENARIO.feedbackMeaning;

  const reviewBoss = $("#review-boss-title");
  if (reviewBoss) reviewBoss.textContent = DEMO_SCENARIO.reviewBoss;

  const reviewList = $("#review-list");
  if (reviewList) {
    reviewList.innerHTML = DEMO_SCENARIO.reviewItems.map((item) => `<li>${item}</li>`).join("");
  }

  const nextWeekTitle = $("#next-week-title");
  if (nextWeekTitle) nextWeekTitle.textContent = DEMO_SCENARIO.nextWeekTitle;

  const nextWeekDesc = $("#next-week-desc");
  if (nextWeekDesc) nextWeekDesc.textContent = DEMO_SCENARIO.nextWeekDesc;

  const observation = $("#review-observation");
  if (observation) observation.textContent = DEMO_SCENARIO.observation;

  const dailyInput = $("#daily-input");
  if (dailyInput && DAILY_TASK.normal.inputPlaceholder) {
    dailyInput.placeholder = DAILY_TASK.normal.inputPlaceholder;
  }
}

function renderDaily() {
  const task = state.downgradeApplied ? DAILY_TASK.downgraded : DAILY_TASK.normal;
  $("#daily-day-tag").textContent = `Day ${state.currentDay}`;
  $("#daily-title").textContent = task.title;
  $("#daily-desc").textContent = task.desc;
  $("#daily-meaning").textContent = task.meaning;
  const inputArea = $("#daily-input-area");
  const dailyInput = $("#daily-input");
  inputArea.style.display = task.hasInput ? "block" : "none";
  if (dailyInput && task.inputPlaceholder) {
    dailyInput.placeholder = task.inputPlaceholder;
  }
}

function renderFeedback() {
  const progress = state.completedDays.length;
  $("#feedback-day").textContent = `Day ${state.currentDay}`;
  $("#feedback-progress-fill").style.width = `${(progress / 7) * 100}%`;
  $("#feedback-progress-text").textContent = `${progress} / 7`;
  $("#tomorrow-title").textContent = WEEK_PLAN[state.currentDay]?.title || "周复盘";
}

function openModal() {
  $("#modal-downgrade").classList.add("active");
  state.selectedDowngrade = null;
  $$(".downgrade-option").forEach((el) => el.classList.remove("selected"));
}

function closeModal() {
  $("#modal-downgrade").classList.remove("active");
}

function init() {
  // P01: 示例 chips
  $$(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      $("#goal-input").value = chip.dataset.goal;
      state.goal = chip.dataset.goal;
      $("#btn-start").disabled = false;
    });
  });

  $("#goal-input")?.addEventListener("input", (e) => {
    state.goal = e.target.value.trim();
    $("#btn-start").disabled = !state.goal;
  });

  $("#btn-start")?.addEventListener("click", () => {
    state.clarifyStep = 0;
    state.selectedOption = null;
    showScreen("clarify");
    renderClarify();
  });

  $("#link-continue")?.addEventListener("click", (e) => {
    e.preventDefault();
    showScreen("hub");
  });

  // P02: 澄清
  $("#btn-clarify-skip")?.addEventListener("click", () => {
    if (state.clarifyStep < CLARIFY_QUESTIONS.length - 1) {
      state.clarifyStep++;
      state.selectedOption = null;
      renderClarify();
    }
  });

  $("#btn-clarify-next")?.addEventListener("click", () => {
    if (state.selectedOption) {
      state.clarifyAnswers[CLARIFY_QUESTIONS[state.clarifyStep].id] = state.selectedOption;
    }
    if (state.clarifyStep < CLARIFY_QUESTIONS.length - 1) {
      state.clarifyStep++;
      state.selectedOption = state.clarifyAnswers[CLARIFY_QUESTIONS[state.clarifyStep].id] || null;
      renderClarify();
    } else {
      showScreen("preview");
      renderTimeline();
    }
  });

  // P03
  $("#btn-accept-plan")?.addEventListener("click", () => {
    state.currentDay = 1;
    state.completedDays = [];
    state.downgradeApplied = false;
    showScreen("daily");
    renderDaily();
  });

  $("#btn-regenerate")?.addEventListener("click", () => {
    alert("原型演示：将重新调用 AI 生成计划（Mock）");
  });

  // P04
  $("#btn-complete")?.addEventListener("click", () => {
    if (!state.completedDays.includes(state.currentDay)) {
      state.completedDays.push(state.currentDay);
      state.completedDays.sort((a, b) => a - b);
    }
    showScreen("feedback");
    renderFeedback();
  });

  $("#btn-downgrade")?.addEventListener("click", openModal);

  // P06 Modal
  $$(".downgrade-option").forEach((opt) => {
    opt.addEventListener("click", () => {
      state.selectedDowngrade = opt.dataset.id;
      $$(".downgrade-option").forEach((el) => el.classList.remove("selected"));
      opt.classList.add("selected");
      $("#btn-apply-downgrade").disabled = false;
    });
  });

  $("#btn-apply-downgrade")?.addEventListener("click", () => {
    state.downgradeApplied = true;
    closeModal();
    renderDaily();
  });

  $("#btn-cancel-downgrade")?.addEventListener("click", closeModal);

  $("#modal-downgrade")?.addEventListener("click", (e) => {
    if (e.target === $("#modal-downgrade")) closeModal();
  });

  // P05
  $("#btn-feedback-done")?.addEventListener("click", () => {
    if (state.currentDay < 7) {
      state.currentDay++;
      state.downgradeApplied = false;
      showScreen("hub");
    } else {
      showScreen("review");
    }
  });

  // P08
  $("#btn-go-daily")?.addEventListener("click", () => {
    showScreen("daily");
    renderDaily();
  });

  $("#link-view-plan")?.addEventListener("click", (e) => {
    e.preventDefault();
    showScreen("preview");
    renderTimeline();
  });

  // P07
  $("#btn-next-week")?.addEventListener("click", () => {
    state.clarifyStep = 0;
    state.selectedOption = null;
    state.currentDay = 1;
    state.completedDays = [];
    showScreen("clarify");
    renderClarify();
  });

  $("#btn-pause")?.addEventListener("click", () => showScreen("home"));

  $(".logo")?.addEventListener("click", () => showScreen("home"));

  // Demo: 从首页快捷进入中枢（演示回访）
  if (new URLSearchParams(location.search).get("hub") === "1") {
    state.currentDay = 3;
    state.completedDays = [1, 2];
    showScreen("hub");
  } else {
    showScreen("home");
  }

  updateHeader();
  applyDemoCopy();
  renderTimeline();
}

document.addEventListener("DOMContentLoaded", init);
