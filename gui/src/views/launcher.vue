<template>
  <div class="launcher-wrap">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="title">
        <span class="dot" :class="runningCount ? 'on' : ''"></span>
        启动器（{{ runningCount }}/9 运行中）
      </div>
      <label class="poll-switch" title="每 1.5 秒读取所有运行槽位的内存（关闭时仅手动刷新）">
        <input type="checkbox" v-model="polling" /> 内存轮询
      </label>
      <el-button size="small" @click="addSlot">+ 空槽位</el-button>
      <el-button size="small" @click="save">保存配置</el-button>
      <el-button size="small" type="danger" plain @click="stopAll">全部停止</el-button>
    </div>

    <!-- 9 槽位网格 -->
    <div class="slot-grid">
      <div v-for="(s, i) in slots" :key="i" class="slot-card" :class="{ running: s.pid && s.alive }">
        <div class="slot-head">
          <span class="slot-no">#{{ i + 1 }}</span>
          <el-tag :type="s.pid && s.alive ? 'success' : 'info'" size="small" effect="dark">
            {{ s.pid && s.alive ? '运行中' : '已停止' }}
          </el-tag>
          <span v-if="s.pid && s.alive" class="pid">PID {{ s.pid }}</span>
          <span v-if="s.title" class="wtitle">{{ s.title }}</span>
        </div>

        <div class="field">
          <span class="label">名称</span>
          <el-input v-model="s.label" size="small" placeholder="槽位名称" @change="dirty" />
        </div>

        <div class="field">
          <span class="label">启动文件</span>
          <div class="row">
            <el-input v-model="s.dir" size="small" placeholder="D2Loader.exe 或 .lnk" @change="dirty" />
            <el-button size="small" @click="pickExe(i)">…</el-button>
            <el-button size="small" @click="pickLnk(i)" title="选 .lnk 并自动解析目标+参数">lnk</el-button>
          </div>
        </div>

        <div class="field">
          <span class="label">参数</span>
          <el-input v-model="s.params" size="small" placeholder="-direct -locale kor ..." @change="dirty" />
        </div>

        <div class="field">
          <span class="label">窗口标题</span>
          <el-input v-model="s.title" size="small" placeholder="多开区分，如 Bus 1" @change="dirty" />
        </div>

        <div class="field">
          <span class="label">后台脚本</span>
          <div class="row">
            <el-input v-model="s.script" size="small" placeholder="可选 .ahk 点击脚本" @change="dirty" />
            <el-button size="small" @click="pickAhk(i)">…</el-button>
            <el-button v-if="s.script" size="small" @click="clearScript(i)">×</el-button>
          </div>
        </div>

        <div class="slot-actions">
          <el-button v-if="!(s.pid && s.alive)" type="primary" size="small" @click="start(i)">启动</el-button>
          <el-button v-else type="danger" size="small" @click="stop(i)">停止</el-button>
          <el-button v-if="s.pid && s.alive" size="small" type="primary" plain @click="openExtra(i)">附加</el-button>
          <label class="poll-sw" :title="'内存轮询（每 1.5s），槽位独立持久化'">
            <input type="checkbox" v-model="s.poll" @change="save()" /> 轮询
          </label>
          <el-button size="small" @click="clearSlot(i)">清空</el-button>
          <el-button size="small" type="warning" plain @click="removeSlot(i)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- 附加功能弹窗（侧边栏：内存 / 控件） -->
    <el-dialog :model-value="extraDlg !== null" title="附加功能" width="880px" append-to-body @close="extraDlg = null">
      <template v-if="extraDlg !== null && slots[extraDlg]">
        <div class="extra-body">
          <div class="extra-side">
            <div class="extra-nav" :class="{ active: extraTab === 'mem' }" @click="extraTab = 'mem'">内存</div>
            <div class="extra-nav" :class="{ active: extraTab === 'ctrl' }" @click="switchCtrl()">控件</div>
          </div>
          <div class="extra-main">
            <!-- ========== 内存页 ========== -->
            <template v-if="extraTab === 'mem'">
              <div class="mem-dlg">
                <div class="md-row">
                  <span class="md-k">槽位</span>
                  <span class="md-v">#{{ extraDlg + 1 }} {{ slots[extraDlg].label || slots[extraDlg].dir || "" }}</span>
                </div>
                <template v-if="slots[extraDlg].mem.error">
                  <div class="md-row">
                    <span class="md-k">内存</span>
                    <span class="md-v md-err">{{ slots[extraDlg].mem.error }}</span>
                  </div>
                </template>
                <template v-else>
                  <div class="md-row">
                    <span class="md-k">状态</span>
                    <span class="md-v">
                      <el-tag size="small" :type="memTagType(slots[extraDlg].mem.marker)" effect="plain">{{ memStatus(slots[extraDlg].mem.marker) }}</el-tag>
                      标记 {{ slots[extraDlg].mem.marker ?? "—" }}
                    </span>
                  </div>
                  <div class="md-row" v-if="slots[extraDlg].mem.gameType !== 0">
                    <span class="md-k">账号</span>
                    <span class="md-v">{{ slots[extraDlg].mem.account || "—" }}</span>
                  </div>
                  <div class="md-row">
                    <span class="md-k">人物</span>
                    <span class="md-v">{{ slots[extraDlg].mem.charName || "—" }}</span>
                  </div>
                  <div class="md-row">
                    <span class="md-k">索引</span>
                    <span class="md-v">{{ slots[extraDlg].mem.charIndex == null ? "—" : (slots[extraDlg].mem.charIndex === 4294967295 ? "未选" : slots[extraDlg].mem.charIndex) }}</span>
                  </div>
                  <div class="md-row">
                    <span class="md-k">背包</span>
                    <span class="md-v pre" :title="bagDetail(slots[extraDlg].mem.bag)">{{ bagText(slots[extraDlg].mem.bag) }}</span>
                  </div>
                  <div class="md-row">
                    <span class="md-k">仓库</span>
                    <span class="md-v pre">
                      <template v-if="slots[extraDlg].mem.stash && slots[extraDlg].mem.stash.stash_open">
                        第{{ slots[extraDlg].mem.stash.page }}页<template v-if="stashText(slots[extraDlg].mem.bag)"> · {{ stashText(slots[extraDlg].mem.bag) }}</template>
                      </template>
                      <template v-else>未打开</template>
                    </span>
                  </div>
                </template>
                <div class="md-tip">每 1.5 秒自动刷新（轮询进行中）</div>
              </div>
            </template>
            <!-- ========== 控件页 ========== -->
            <template v-else-if="extraTab === 'ctrl'">
              <div class="ctrl-dlg">
                <div class="md-row">
                  <span class="md-k">槽位</span>
                  <span class="md-v">#{{ extraDlg + 1 }} {{ slots[extraDlg].label || slots[extraDlg].dir || "" }}</span>
                </div>
                <template v-if="ctrlErr">
                  <div class="md-row">
                    <span class="md-k">读取</span>
                    <span class="md-v md-err">{{ ctrlErr }}</span>
                  </div>
                </template>
                <template v-else-if="ctrlData">
                  <div class="md-row">
                    <span class="md-k">状态</span>
                    <span class="md-v">
                      <el-tag size="small" :type="ctrlData.state === 'game' ? 'success' : ctrlData.state === 'menu' ? 'warning' : 'info'" effect="plain">
                        {{ ctrlStateName(ctrlData.state) }}
                      </el-tag>
                      页面：{{ ctrlData.page || "—" }}
                    </span>
                  </div>
                  <div class="md-row">
                    <span class="md-k">链首</span>
                    <span class="md-v">0x{{ (ctrlData.first || 0).toString(16).toUpperCase().padStart(8, "0") }} · 控件 {{ ctrlList.length }} 个</span>
                  </div>
                  <div class="ctrl-filter">
                    <span class="cf-title">类型</span>
                    <label v-for="o in ctrlTypeOptions" :key="o.v" class="cf-item">
                      <input type="checkbox" :value="o.v" v-model="ctrlTypes" /> {{ o.label }}
                    </label>
                    <label class="cf-item">
                      <input type="checkbox" v-model="ctrlHideEmpty" /> 剔除空文本
                    </label>
                    <label class="cf-item">
                      <input type="checkbox" v-model="ctrlHideDisabled" /> 过滤禁用
                    </label>
                  </div>
                  <div class="ctrl-list">
                    <div v-for="(c, k) in ctrlList" :key="k" class="ctrl-item" :class="{ disabled: ctrlDisabled(c), noclick: ctrlDisabled(c) }" @click="ctrlClick(c)">
                      <span class="ci-no">#{{ k }}</span>
                      <el-tag size="small" effect="plain" :type="c.type === 6 ? 'primary' : 'info'" class="ci-type" :class="{ strike: ctrlDisabled(c) }">{{ c.type_name }}</el-tag>
                      <span class="ci-pos">({{ c.pos[0] }},{{ c.pos[1] }}) {{ c.size[0] }}×{{ c.size[1] }}</span>
                      <span class="ci-txt" :class="{ 'ci-dis': c.type === 6 && ctrlDisabled(c) }">{{ (c.texts || []).join("\n") || "—" }}</span>
                      <span v-if="c.cb_off" class="ci-cb" :title="'回调 @0x34 相对偏移，同版本下稳定唯一'">{{ c.cb_off }}</span>
                    </div>
                  </div>
                </template>
                <div class="ctrl-actions">
                  <el-button size="small" :loading="ctrlLoading" @click="loadCtrl(extraDlg)">刷新</el-button>
                  <span class="md-tip">点击时读取快照，非自动刷新；点击控件行可后台点击游戏窗口</span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- Log 面板 -->
    <div class="log-panel">
      <div class="log-head">
        日志
        <el-button size="small" text @click="clearLog">清空</el-button>
      </div>
      <div class="log-body" ref="logBody">
        <div v-for="(l, i) in logs" :key="i" class="log-line" :class="l.level">
          <span class="log-time">{{ l.time }}</span>
          <span class="log-msg">{{ l.msg }}</span>
        </div>
        <div v-if="!logs.length" class="log-empty">暂无日志</div>
      </div>
    </div>
  </div>
</template>

<script>
const CFG = "Setting\\launcher.json";
const MAX_LOG = 200;
const LOC_NAMES = { 0: "地面", 1: "背包", 2: "腰带", 3: "装备", 4: "仓库", 5: "盒子" };

// 控件类型选项（用于顶部复选框过滤；-1 = 未列出的其他类型）
const CTRL_TYPE_OPTIONS = [
  { v: 6, label: "按钮" },
  { v: 4, label: "文本框" },
  { v: 1, label: "编辑框" },
  { v: 2, label: "图片" },
  { v: 5, label: "滚动条" },
  { v: 7, label: "列表" },
  { v: 12, label: "账号列表" },
  { v: -1, label: "其他" },
];
const ALL_CTRL_TYPES = CTRL_TYPE_OPTIONS.map((o) => o.v);

const emptyMem = () => ({ marker: null, account: "", charIndex: null, charName: "", gameType: null, bag: [], stash: null, error: "" });
const emptySlot = () => ({ label: "", dir: "", params: "", title: "", script: "", pid: 0, mem: emptyMem(), poll: false });

export default {
  name: "launcher",
  data() {
    return {
      slots: [],
      logs: [],
      timer: null,
      saving: false,
      // 内存轮询开关：默认关闭，从 localStorage 恢复
      polling: (() => {
        try { return localStorage.getItem("d2it_polling") === "1"; } catch (e) { return false; }
      })(),
      extraDlg: null,   // 附加功能弹窗打开的槽位索引（null=关闭）
      extraTab: "mem",  // 附加功能侧边栏当前页：mem 内存 / ctrl 控件
      ctrlData: null,
      ctrlErr: "",
      ctrlLoading: false,
      // 控件类型过滤：从 localStorage 恢复，默认全选（全槽位通用）
      ctrlTypes: (() => {
        try {
          const v = JSON.parse(localStorage.getItem("d2it_ctrl_types"));
          if (Array.isArray(v) && v.length) return v;
        } catch (e) { /* 忽略损坏数据 */ }
        return [...ALL_CTRL_TYPES];
      })(),
      ctrlTypeOptions: CTRL_TYPE_OPTIONS,
      // 剔除空文本：从 localStorage 恢复，默认关闭
      ctrlHideEmpty: (() => {
        try { return localStorage.getItem("d2it_ctrl_hide_empty") === "1"; } catch (e) { return false; }
      })(),
      // 过滤禁用（dwDisabled bit0=0）：从 localStorage 恢复，默认关闭
      ctrlHideDisabled: (() => {
        try { return localStorage.getItem("d2it_ctrl_hide_disabled") === "1"; } catch (e) { return false; }
      })(),
    };
  },
  computed: {
    runningCount() {
      return this.slots.filter((s) => s.pid && s.alive).length;
    },
    // 控件列表：按顶部勾选的类型过滤（默认全选），可选剔除空文本/过滤禁用
    ctrlList() {
      if (!this.ctrlData || !this.ctrlData.controls) return [];
      return this.ctrlData.controls.filter((c) => {
        if (this.ctrlHideDisabled && this.ctrlDisabled(c)) return false;
        if (this.ctrlHideEmpty && (!c.texts || !c.texts.length)) return false;
        const hit = CTRL_TYPE_OPTIONS.find((o) => o.v === c.type);
        return this.ctrlTypes.includes(hit ? hit.v : -1);
      });
    },
  },
  watch: {
    ctrlTypes(v) {
      try { localStorage.setItem("d2it_ctrl_types", JSON.stringify(v)); } catch (e) { /* 忽略 */ }
    },
    ctrlHideEmpty(v) {
      try { localStorage.setItem("d2it_ctrl_hide_empty", v ? "1" : "0"); } catch (e) { /* 忽略 */ }
    },
    ctrlHideDisabled(v) {
      try { localStorage.setItem("d2it_ctrl_hide_disabled", v ? "1" : "0"); } catch (e) { /* 忽略 */ }
    },
  },
  mounted() {
    this.load();
    this.timer = setInterval(() => this.poll(), 1500);
  },
  beforeUnmount() {
    clearInterval(this.timer);
  },
  methods: {
    // ---------------- 内存状态辅助 ----------------
    memStatus(marker) {
      if (marker == null) return "未读取";
      if (marker >= 3000 && marker <= 3999) return "游戏内（单机）";
      if (marker >= 2000 && marker <= 2999) return "游戏内（战网）";
      if (marker === 10 || marker === 11) return "大厅";
      return "未知";
    },
    memTagType(marker) {
      if (marker == null) return "info";
      if ((marker >= 2000 && marker <= 2999) || (marker >= 3000 && marker <= 3999)) return "success";
      return "warning";
    },
    // 背包显示：按位置分组（loc: 0地面 1背包 2腰带 3装备）合并同物品 + 数量汇总
    groupBag(bag) {
      const groups = {};
      (bag || []).forEach((b) => {
        const k = b.loc == null ? 1 : b.loc;
        if (!groups[k]) groups[k] = new Map();
        const m = groups[k];
        const key = b.abbr || String(b.code);
        if (!m.has(key)) m.set(key, { ...b, count: 0 });
        m.get(key).count++;
      });
      return groups;
    },
    bagText(bag) {
      const g = this.groupBag(bag);
      const parts = Object.keys(g)
        .sort((a, b) => a - b)
        .map((k) => {
          const items = [...g[k].values()]
            .map((b) => `${b.name || b.abbr}×${b.count}`)
            .join(" ");
          return `${LOC_NAMES[k] || "?"}[${items}]`;
        });
      return parts.join("\n") || "—";
    },
    bagDetail(bag) {
      const g = this.groupBag(bag);
      const parts = Object.keys(g)
        .sort((a, b) => a - b)
        .map((k) => {
          const items = [...g[k].values()]
            .map((b) => `${b.name || b.abbr} ×${b.count}`)
            .join("，");
          return `${LOC_NAMES[k] || "?"}[${items}]`;
        });
      return parts.join("\n") || "空";
    },
    // 仓库当前页物品（loc==4），仅返回物品串（无则空串）
    stashText(bag) {
      const g = this.groupBag(bag);
      const items = [...(g[4] || new Map()).values()]
        .map((b) => `${b.name || b.abbr}×${b.count}`)
        .join("，");
      return items || "";
    },

    now() {
      const d = new Date();
      const p = (n) => String(n).padStart(2, "0");
      return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
    },
    // AHK 门面（Kits 约定：按文件名注入同名函数）
    ahkL() {
      return this.$ahk.fn.Launcher();
    },
    log(msg, level = "info") {
      this.logs.push({ time: this.now(), msg, level });
      if (this.logs.length > MAX_LOG) this.logs.splice(0, this.logs.length - MAX_LOG);
      this.$nextTick(() => {
        const b = this.$refs.logBody;
        if (b) b.scrollTop = b.scrollHeight;
      });
    },
    dirty() {
      this.save();
    },

    // ---------------- 配置持久化 ----------------
    load() {
      try {
        const raw = this.$ahk.fn.LoadJson("Setting", "launcher.json");
        const cfg = raw ? JSON.parse(raw) : {};
        this.slots = Array.isArray(cfg.slots) ? cfg.slots : [];
        this.slots = this.slots.map((s) => ({ ...emptySlot(), ...s, mem: { ...emptyMem(), ...(s.mem || {}) } }));
        this.log("配置已加载");
      } catch (e) {
        this.slots = [];
        this.log("配置加载失败: " + e.message, "warn");
      }
      if (!this.slots.length) this.slots.push(emptySlot()); // 至少保留 1 个空槽
    },
    save() {
      if (this.saving) return;
      this.saving = true;
      try {
        const cfg = { version: 1, updated: new Date().toISOString(), slots: this.slots };
        this.$ahk.fn.SaveFile(CFG, JSON.stringify(cfg));
      } catch (e) {
        this.log("保存失败: " + e.message, "error");
      }
      this.saving = false;
    },

    // ---------------- 槽位操作 ----------------
    addSlot() {
      if (this.slots.length >= 9) {
        this.log("最多 9 个槽位", "warn");
        return;
      }
      this.slots.push(emptySlot());
      this.save();
    },
    clearSlot(i) {
      if (this.slots[i].pid && this.slots[i].alive) this.stop(i);
      this.slots[i] = emptySlot();
      this.save();
    },
    removeSlot(i) {
      if (this.slots[i].pid && this.slots[i].alive) this.stop(i);
      this.slots.splice(i, 1);
      if (!this.slots.length) this.slots.push(emptySlot()); // 至少保留 1 个
      if (this.extraDlg === i) this.extraDlg = null;
      else if (this.extraDlg !== null && this.extraDlg > i) this.extraDlg--;
      this.save();
      this.log(`槽位 #${i + 1} 已删除`);
    },
    // ---------------- 附加功能（侧边栏：内存 / 控件） ----------------
    openExtra(i) {
      this.extraDlg = i;
      this.extraTab = "mem";
    },
    // 切换到控件页：首次进入时读取快照
    switchCtrl() {
      this.extraTab = "ctrl";
      const s = this.slots[this.extraDlg];
      if (s && s.pid) this.loadCtrl(this.extraDlg);
    },
    // ---------------- 控件信息（点击时读取快照） ----------------
    ctrlStateName(state) {
      return { menu: "菜单", game: "游戏内", null: "无", busy: "加载中" }[state] || state || "—";
    },
    // 禁用判断：dwDisabled@0x08 的 bit0（0=不可点击 1=可点击），链路上所有控件通用
    ctrlDisabled(c) {
      return c.disabled !== undefined && (c.disabled & 1) === 0;
    },
    async loadCtrl(i) {
      const s = this.slots[i];
      if (!s || !s.pid) return;
      this.ctrlLoading = true;
      this.ctrlErr = "";
      this.ctrlData = null;
      try {
        const r = this.ahkL().Mem(String(s.pid));
        if (!r || !r.ok) {
          this.ctrlErr = (r && r.error) || "内存读取无返回";
          return;
        }
        const data = JSON.parse(r.json);
        const m = data.results && data.results[String(s.pid)];
        this.ctrlData = (m && m["控件链"]) || null;
        if (!this.ctrlData) this.ctrlErr = "未读取到控件链（可能不在菜单/游戏界面）";
      } catch (e) {
        this.ctrlErr = "读取失败: " + e.message;
      } finally {
        this.ctrlLoading = false;
      }
    },
    // 点击控件行 → 向游戏窗口发送后台点击（PostMessage，附控件中心坐标）
    async ctrlClick(c) {
      const s = this.slots[this.extraDlg];
      if (!s || !s.pid) return;
      // 不可点击判断：dwDisabled@0x08 bit0==0（链路上所有控件通用）
      if (this.ctrlDisabled(c)) {
        const label = (c.texts || []).join("/") || c.type_name || "控件";
        this.log(`控件 [${label}] 为禁用状态(dwDisabled=0x${(c.disabled >>> 0).toString(16)})，忽略点击`, "warn");
        return;
      }
      // 用控件中心（pos + size/2），避免点在边缘触发区
      const x = c.pos[0] + Math.floor(c.size[0] / 2);
      const y = c.pos[1] + Math.floor(c.size[1] / 2);
      const label = (c.texts || []).join("/") || c.type_name || "控件";
      try {
        const r = this.ahkL().Click(String(s.pid), x, y);
        if (r && r.ok) {
          this.log(`点击控件 [${label}] @ 中心(${x},${y}) [pos(${c.pos[0]},${c.pos[1]}) ${c.size[0]}×${c.size[1]}] → 窗口 0x${(r.hwnd >>> 0).toString(16).toUpperCase()}`);
          // 点击后界面可能切换，延迟刷新控件快照
          setTimeout(() => this.loadCtrl(this.extraDlg), 350);
        } else this.log("控件点击失败: " + ((r && r.error) || "无返回"), "error");
      } catch (e) {
        this.log("控件点击异常: " + e.message, "error");
      }
    },
    clearScript(i) {
      this.slots[i].script = "";
      this.save();
    },
    pickExe(i) {
      const p = this.ahkL().SelectExe("选择启动文件 #" + (i + 1));
      if (p) {
        this.slots[i].dir = p;
        this.save();
        this.log(`槽位 #${i + 1} 启动文件: ${p}`);
      }
    },
    pickLnk(i) {
      const p = this.ahkL().SelectExe("选择快捷方式 #" + (i + 1));
      if (!p) return;
      const r = this.ahkL().PickLnk(p);
      if (r && r.ok) {
        this.slots[i].dir = r.target;
        this.slots[i].params = r.args || "";
        if (!this.slots[i].title && r.workDir) this.log(`工作目录: ${r.workDir}`);
        this.save();
        this.log(`槽位 #${i + 1} 已解析 lnk → ${r.target}`);
      } else {
        this.log("lnk 解析失败: " + (r && r.error), "error");
      }
    },
    pickAhk(i) {
      const p = this.ahkL().SelectAhk("选择后台脚本 #" + (i + 1));
      if (p) {
        this.slots[i].script = p;
        this.save();
      }
    },

    // ---------------- 启动 / 停止 ----------------
    start(i) {
      const s = this.slots[i];
      if (!s.dir) {
        this.log(`槽位 #${i + 1} 未配置启动文件`, "warn");
        return;
      }
      this.log(`槽位 #${i + 1} 启动: ${s.dir}`);
      const r = this.ahkL().Start(s.dir, s.params || "", s.title || "", s.script || "");
      if (r && r.ok) {
        s.pid = r.pid;
        s.alive = true;
        this.log(`槽位 #${i + 1} 已启动 PID=${r.pid}` + (r.warn ? "（" + r.warn + "）" : ""));
      } else {
        s.alive = false;
        this.log(`槽位 #${i + 1} 启动失败: ${r && r.error}`, "error");
      }
      this.save();
    },
    async stop(i) {
      const s = this.slots[i];
      if (!s.pid) return;
      this.log(`槽位 #${i + 1} 停止 PID=${s.pid}`);
      const r = this.ahkL().Stop(s.pid);
      s.pid = 0;
      s.alive = false;
      this.log(`槽位 #${i + 1} 已停止（${r && r.note}）`);
      this.save();
    },
    async stopAll() {
      for (let i = 0; i < this.slots.length; i++) if (this.slots[i].pid) await this.stop(i);
      this.log("全部停止");
    },

    // ---------------- 状态轮询 ----------------
    poll() {
      const running = [];
      this.slots.forEach((s, i) => {
        if (!s.pid) return;
        let alive = false;
        try {
          const r = this.ahkL().Alive(s.pid);
          alive = !!(r && r.alive);
          if (r && r.title && r.title !== s.title) s.title = r.title;
        } catch (e) {
          /* 轮询失败忽略 */
        }
        if (s.alive && !alive) this.log(`槽位 #${i + 1} 进程已退出 PID=${s.pid}`, "warn");
        s.alive = alive;
        if (alive) running.push(s.pid);
      });

      // 批量读内存：仅读取开启"轮询"的槽位（槽位独立）
      const memPids = running.filter((pid) => {
        const s = this.slots.find((x) => x.pid === pid);
        return s && s.poll;
      });
      if (memPids.length) {
        let r = null;
        try {
          r = this.ahkL().Mem(memPids.join(","));
        } catch (e) {
          this.log("内存读取调用异常: " + e.message, "warn");
        }
        if (r && r.ok) {
          try {
            const data = JSON.parse(r.json);
            if (data.results) {
              this.slots.forEach((s) => {
                const m = data.results[String(s.pid)];
                if (!m) return;
                if (m._error) {
                  s.mem.error = m._error;
                  return;
                }
                s.mem.error = "";
                s.mem.marker = m["界面标记"] ?? null;
                s.mem.account = m["登录的战网账号"] || "";
                s.mem.gameType = m["游戏类型"] ?? null;
                s.mem.charIndex = m["人物位置索引"] ?? null;
                s.mem.charName = m["人物名称"] || "";
                s.mem.bag = Array.isArray(m["背包物品"]) ? m["背包物品"] : [];
                s.mem.stash = m["仓库状态"] ?? null;
              });
            }
          } catch (e) {
            this.log("内存 JSON 解析失败: " + e.message, "warn");
          }
        } else if (r) {
          this.log("内存读取失败: " + (r.error || "未知错误"), "warn");
        } else {
          this.log("内存读取无返回", "warn");
        }
      }
    },
  },
};
</script>

<style scoped>
.launcher-wrap {
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px;
  box-sizing: border-box;
  overflow: hidden; /* 外层禁止滚动 */
  color: #ddd;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.toolbar .title {
  font-size: 17px;
  font-weight: 600;
  flex: 1;
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #555;
  margin-right: 8px;
}
.dot.on {
  background: #52c41a;
  box-shadow: 0 0 6px #52c41a;
}
.slot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 320px); /* 固定列宽，槽位数变化不改变卡片大小 */
  gap: 10px;
  flex: 1; /* 中间区域占满剩余空间 */
  min-height: 0; /* flex 子项允许收缩，滚动仅发生在本区域 */
  overflow-y: auto;
  padding-right: 4px;
  align-content: start; /* 不满一行时卡片不拉伸 */
}
.slot-card {
  background: #2c2c2c;
  border: 1px solid #3d3d3d;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.slot-card.running {
  border-color: #52c41a;
}
.slot-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.slot-no {
  font-weight: 700;
  color: #8bc8ea;
}
.pid {
  font-size: 11px;
  color: #888;
}
.wtitle {
  font-size: 11px;
  color: #52c41a;
  flex: 1;
  text-align: right;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.field {
  display: flex;
  align-items: center;
  gap: 6px;
}
.field .label {
  width: 56px;
  font-size: 12px;
  color: #999;
  flex-shrink: 0;
}
.field .row {
  flex: 1;
  display: flex;
  gap: 4px;
}
.field :deep(.el-input) {
  flex: 1;
}
.mem-box {
  border: 1px solid #3d3d3d;
  border-radius: 8px;
  background: #2b2b2b;
  padding: 8px 10px;
  margin-top: 8px;
  font-size: 12px;
}
.mem-row {
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.8;
}
.mem-k {
  color: #9a9a9a;
  width: 42px;
  flex-shrink: 0;
}
.mem-v {
  color: #e8e8e8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mem-err {
  color: #f56c6c;
}
.mem-bag {
  white-space: pre-line; /* 背包/腰带/仓库等不同位置换行显示 */
  overflow: visible;
  text-overflow: clip;
  word-break: break-all;
}
.slot-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
/* 内存轮询开关（槽位独立） */
.poll-sw {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: #ccc;
  cursor: pointer;
  user-select: none;
  padding: 0 2px;
}
.poll-sw input {
  margin: 0;
  accent-color: #8bc8ea;
  cursor: pointer;
}
/* 附加功能弹窗：侧边栏 + 内容区（固定尺寸，内容区内滚动） */
.extra-body {
  display: flex;
  gap: 14px;
  height: 460px;   /* 固定高度，弹窗整体尺寸稳定 */
}
.extra-side {
  flex-shrink: 0;
  width: 118px;
  border-right: 1px solid #333;
  padding-right: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}
.extra-nav {
  padding: 9px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #ccc;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s, color 0.12s;
}
.extra-nav:hover {
  background: #2a2a2a;
}
.extra-nav.active {
  background: #2e3a4a;
  color: #8bc8ea;
  font-weight: 600;
}
.extra-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;   /* 内容超高时内容区滚动 */
}
.extra-main .mem-dlg,
.extra-main .ctrl-dlg {
  max-height: none;
}
/* 指针监听弹窗 */
.mem-dlg {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.md-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 13px;
}
.md-k {
  flex-shrink: 0;
  width: 52px;
  color: #8a8a8a;
  line-height: 1.6;
}
.md-v {
  flex: 1;
  line-height: 1.6;
  color: #ddd;
  word-break: break-all;
}
.md-v.pre {
  white-space: pre-line;
}
.md-err {
  color: #e88080;
}
.md-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #777;
}
/* 控件信息弹窗 */
.ctrl-dlg {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ctrl-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  padding: 6px 8px;
  border: 1px solid #333;
  border-radius: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #ccc;
  user-select: none;
}
.cf-title {
  color: #888;
  margin-right: 2px;
}
.cf-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  cursor: pointer;
}
.cf-item input {
  margin: 0;
  accent-color: #8bc8ea;
  cursor: pointer;
}
.ctrl-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 360px;   /* 固定高度内滚动（弹窗整体 460px 已固定） */
  overflow-y: auto;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 8px;
  background: #242424;
}
.ctrl-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  line-height: 1.6;
  padding: 3px 6px;
  margin: 1px -6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s;
}
.ctrl-item:hover {
  background: #2e3a4a;
}
/* 禁用按钮：整行置灰 + 禁止点击光标 */
.ctrl-item.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.ctrl-item.disabled:hover {
  background: transparent;
}
/* 不可点击（dwDisabled bit0=0）：默认光标 + 不触发高亮 */
.ctrl-item.noclick {
  cursor: default;
}
.ctrl-item.noclick:hover {
  background: transparent;
}
.ci-no {
  color: #8bc8ea;
  width: 28px;
  flex-shrink: 0;
}
/* 类型标签统一宽度居中 */
.ci-type {
  width: 60px;
  justify-content: center;
  flex-shrink: 0;
  box-sizing: border-box;
}
/* 不可点击（dwDisabled bit0=0）：类型标签文本划删除线 */
.ci-type.strike {
  text-decoration: line-through;
  opacity: 0.75;
}
.ci-pos {
  color: #aaa;
  width: 130px;
  flex-shrink: 0;
}
.ci-cb {
  color: #e8d48f;
  font-family: Consolas, monospace;
  font-size: 11px;
  width: 86px;
  flex-shrink: 0;
  cursor: help;
}
.ci-txt {
  color: #ddd;
  flex: 1;
  word-break: break-all;
  white-space: pre-line; /* 控件文本内换行（段间换行）保留显示 */
}
.ci-txt.ci-dis {
  color: #999;
}
.ctrl-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.log-panel {
  flex-shrink: 0;
  height: 220px; /* 固定高度日志区，内部滚动 */
  background: #1e1e1e;
  border: 1px solid #3d3d3d;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
}
.log-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  font-size: 13px;
  color: #aaa;
  border-bottom: 1px solid #333;
}
.log-body {
  flex: 1;
  overflow-y: auto;
  padding: 6px 12px;
  font-family: Consolas, "Courier New", monospace;
  font-size: 12px;
  line-height: 1.7;
}
.log-line .log-time {
  color: #666;
  margin-right: 8px;
}
.log-line.info .log-msg {
  color: #ccc;
}
.log-line.warn .log-msg {
  color: #faad14;
}
.log-line.error .log-msg {
  color: #ea6668;
}
.log-empty {
  color: #555;
  text-align: center;
  padding: 20px;
}
</style>

