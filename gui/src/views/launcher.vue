<template>
  <div class="launcher-wrap">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="title">
        <span class="dot" :class="runningCount ? 'on' : ''"></span>
        启动器（{{ runningCount }}/9 运行中）
      </div>
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
          <el-button v-if="s.pid && s.alive" size="small" type="info" plain @click="openMem(i)">内存</el-button>
          <el-button size="small" @click="clearSlot(i)">清空</el-button>
          <el-button size="small" type="warning" plain @click="removeSlot(i)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- 指针监听弹窗 -->
    <el-dialog :model-value="memDlg !== null" title="指针监听" width="640px" append-to-body @close="memDlg = null">
      <template v-if="memDlg !== null && slots[memDlg]">
        <div class="mem-dlg">
          <div class="md-row">
            <span class="md-k">槽位</span>
            <span class="md-v">#{{ memDlg + 1 }} {{ slots[memDlg].label || slots[memDlg].dir || "" }}</span>
          </div>
          <template v-if="slots[memDlg].mem.error">
            <div class="md-row">
              <span class="md-k">内存</span>
              <span class="md-v md-err">{{ slots[memDlg].mem.error }}</span>
            </div>
          </template>
          <template v-else>
            <div class="md-row">
              <span class="md-k">状态</span>
              <span class="md-v">
                <el-tag size="small" :type="memTagType(slots[memDlg].mem.marker)" effect="plain">{{ memStatus(slots[memDlg].mem.marker) }}</el-tag>
                标记 {{ slots[memDlg].mem.marker ?? "—" }}
              </span>
            </div>
            <div class="md-row">
              <span class="md-k">账号</span>
              <span class="md-v">{{ slots[memDlg].mem.account || "—" }}</span>
            </div>
            <div class="md-row">
              <span class="md-k">人物</span>
              <span class="md-v">{{ slots[memDlg].mem.charName || "—" }}</span>
            </div>
            <div class="md-row">
              <span class="md-k">索引</span>
              <span class="md-v">{{ slots[memDlg].mem.charIndex == null ? "—" : (slots[memDlg].mem.charIndex === 4294967295 ? "未选" : slots[memDlg].mem.charIndex) }}</span>
            </div>
            <div class="md-row">
              <span class="md-k">背包</span>
              <span class="md-v pre" :title="bagDetail(slots[memDlg].mem.bag)">{{ bagText(slots[memDlg].mem.bag) }}</span>
            </div>
            <div class="md-row">
              <span class="md-k">仓库</span>
              <span class="md-v pre">
                <template v-if="slots[memDlg].mem.stash && slots[memDlg].mem.stash.stash_open">
                  第{{ slots[memDlg].mem.stash.page }}页<template v-if="stashText(slots[memDlg].mem.bag)"> · {{ stashText(slots[memDlg].mem.bag) }}</template>
                </template>
                <template v-else>未打开</template>
              </span>
            </div>
          </template>
          <div class="md-tip">每 1.5 秒自动刷新（轮询进行中）</div>
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

const emptyMem = () => ({ marker: null, account: "", charIndex: null, charName: "", bag: [], stash: null, error: "" });
const emptySlot = () => ({ label: "", dir: "", params: "", title: "", script: "", pid: 0, mem: emptyMem() });

export default {
  name: "launcher",
  data() {
    return {
      slots: [],
      logs: [],
      timer: null,
      saving: false,
      memDlg: null,
    };
  },
  computed: {
    runningCount() {
      return this.slots.filter((s) => s.pid && s.alive).length;
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
      if (marker >= 3000 && marker <= 3999) return "游戏内";
      if (marker === 10 || marker === 11) return "大厅";
      return "未知";
    },
    memTagType(marker) {
      if (marker == null) return "info";
      if (marker >= 3000 && marker <= 3999) return "success";
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
      if (this.memDlg === i) this.memDlg = null;
      else if (this.memDlg !== null && this.memDlg > i) this.memDlg--;
      this.save();
      this.log(`槽位 #${i + 1} 已删除`);
    },
    openMem(i) {
      this.memDlg = i;
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

      // 批量读内存：一次调用读全部运行实例
      if (running.length) {
        let r = null;
        try {
          r = this.ahkL().Mem(running.join(","));
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
  gap: 6px;
  margin-top: 4px;
}
/* 指针监听弹窗 */
.mem-dlg {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 62vh;
  overflow-y: auto;
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

