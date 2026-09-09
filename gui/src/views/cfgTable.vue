<template>
  <div>
    <el-card style="margin: auto; border-radius: 15px" shadow="always">
      <el-scrollbar height="570px">
        <div
          style="display: flex; flex-wrap: wrap; align-content: center; justify-content: flex-start; padding-left: 10px">
          <el-card class="cfg-card-50" shadow="always" @click="newGameConfig"> + 新建客户端配置 </el-card>
        </div>
        <el-divider style="margin: 10px 0" />
        <div
          style="display: flex; flex-wrap: wrap; align-content: flex-start; justify-content: flex-start; padding-left: 10px">
          <el-card class="cfg-card-50" shadow="always" v-for="(item, index) in gameConfig">
            <el-descriptions style="max-width: 100%" :column="1">
              <el-descriptions-item>{{ item.label }}</el-descriptions-item>
            </el-descriptions>
            <div style="display: flex; flex-wrap: wrap; margin-bottom: 10px">
              <el-tag v-if="item.bNet" type="success">{{ item.bNet.length > 7 ? item.bNet.slice(0, 7) + "…" :
                item.bNet }}</el-tag>
              <el-tag v-else type="success">单机</el-tag>
              <el-tag v-if="true" type="warning">{{ item.gameVer }}</el-tag>
            </div>
            <el-button class="cardBtn" @click="showEditDialog(index)">编辑</el-button>
            <el-button class="cardBtn" @click="showDeleteDialog(index)">删除</el-button>
          </el-card>
        </div>
      </el-scrollbar>
    </el-card>
  </div>
  <el-dialog v-model="deleteDialog.Visible" title="确认删除" width="300" :show-close="false"
    style="border: 1px solid #ab4d00" center>
    <div style="text-align: center">{{ deleteDialog.TXT }}</div>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="deleteGameConfig"> 确认 </el-button>
      </div>
    </template>
  </el-dialog>
  <el-dialog v-model="editDialog.Visible" :title="`${editDialog.type === 1 ? '新建' : '编辑'}客户端配置`" fullscreen>
    <el-form :model="editDialog.form" style="display: flex" class="specialLabel">
      <el-scrollbar height="578px" style="width: 499px; margin-right: 20px;padding-right: 20px;">
        <el-form-item label="名称" placeholder="必填" style="border-left: 2px solid #ab4d00">
          <el-input v-model="editDialog.form.label" placeholder="必填 至少2个字符" autocomplete="off" minlength="2"
            maxlength="10" show-word-limit />
        </el-form-item>
        <el-form-item label="战网" style="border-left: 2px solid #ab4d00">
          <el-select v-model="editDialog.form.bNet" placeholder="选择战网">
            <el-option v-for="item in bNetList" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本" style="border-left: 2px solid #ab4d00">
          <el-select v-model="editDialog.form.gameVer" placeholder="游戏版本">
            <el-option v-for="item in gameVerList" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="打开方式" style="border-left: 2px solid #ab4d00">
          <el-input v-model="editDialog.form.dir" autocomplete="off" placeholder="必填">
            <template #append> <el-button @click="FileSelect">选择</el-button></template>
          </el-input>
          <el-alert type="info" :closable="false">
            <span style="font-size: 0.8rem">
              允许任意打开方式 但启动参数仅对选择了D2Loader.exe的方式生效. 快捷方式以内置参数为准.<br />修改此项后,请先用[尝试启动]确保能够正常启动
            </span>
          </el-alert>
        </el-form-item>
        <el-form-item label="格子设置" style="border-left: 2px solid #ab4d00">
          <el-select v-model="editDialog.form.inventorySet" placeholder="格子预设" @change="handleInventorySetChange">
            <el-option v-for="item in persetForInventory" :key="item" :label="item" :value="item" />
          </el-select>
          <el-alert type="info" :closable="false" v-if="inventorySetState">
            <div class="specialAlert">
              <div>角色背包:&nbsp;{{ editDialog.form.bagSize[0] }}行{{ editDialog.form.bagSize[1] }}列</div>
              <div>角色仓库:&nbsp;{{ editDialog.form.storageSize[0] }}行{{ editDialog.form.storageSize[1] }}列{{
                editDialog.form.storageSize[2] }}页</div>
            </div>
            <div class="specialAlert">
              <div>赫拉迪姆:&nbsp;{{ editDialog.form.boxSize[0] }}行{{ editDialog.form.boxSize[1] }}列</div>
              <div>非资仓库:&nbsp;{{ editDialog.form.fzStorageSize[0] }}行{{ editDialog.form.fzStorageSize[1] }}列{{
                editDialog.form.fzStorageSize[2] }}页</div>
            </div>
          </el-alert>
          <el-alert type="info" :closable="false" v-else>
            <el-form-item label="角色背包" style="margin-right: 20px">
              <div class="specialSpan" style="display: flex; justify-content: flex-start">
                <el-input-number v-model="editDialog.form.bagSize[0]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>行</span>
                <el-input-number v-model="editDialog.form.bagSize[1]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>列</span>
              </div>
            </el-form-item>
            <el-form-item label="赫拉迪姆" style="margin-right: 20px; margin-top: 10px">
              <div class="specialSpan" style="display: flex; justify-content: flex-start">
                <el-input-number v-model="editDialog.form.boxSize[0]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>行</span>
                <el-input-number v-model="editDialog.form.boxSize[1]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>列</span>
              </div>
            </el-form-item>
            <el-form-item label="角色仓库" style="margin-right: 20px; margin-top: 10px">
              <div class="specialSpan" style="display: flex; justify-content: flex-start">
                <el-input-number v-model="editDialog.form.storageSize[0]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>行</span>
                <el-input-number v-model="editDialog.form.storageSize[1]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>列</span>
                <el-input-number v-model="editDialog.form.storageSize[2]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>页</span>
              </div>
            </el-form-item>
            <el-form-item label="非资仓库" style="margin-right: 20px; margin-top: 10px">
              <div class="specialSpan" style="display: flex; justify-content: flex-start">
                <el-input-number v-model="editDialog.form.fzStorageSize[0]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>行</span>
                <el-input-number v-model="editDialog.form.fzStorageSize[1]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>列</span>
                <el-input-number v-model="editDialog.form.fzStorageSize[2]" :min="1" :max="50" :precision="0"
                  :controls="false" />
                <span>页</span>
              </div>
            </el-form-item>
          </el-alert>
        </el-form-item>
      </el-scrollbar>
      <el-scrollbar height="578px" style="width: 499px; margin-right: 20px">
        <span style="margin-right: 20px">账号&角色</span>
        <el-tag type="primary">添加账号</el-tag>
        <el-collapse accordion>
          <el-collapse-item :name="index + ''"
            v-for="(item, index) in ['aba001', 'aba002', 'aba003', 'aba004', 'aba005', 'aba006', 'ue4re0', 'ue4re1', 'ue4re2']">
            <template #title>
              <div class="dialog-footer-between">
                <div><span style="margin-right: 20px">{{ item }}</span></div>
                <div><el-tag type="warning">保存后删除</el-tag></div>
              </div>
            </template>
            <el-tag style="margin-right: 10px" closable
              v-for="item2 in ['aba001', 'aba002', 'aba003', 'aba004', 'aba005', 'aba006', 'ue4re0', 'ue4re1', 'ue4re2']"
              :key="item2">
              {{ item2 }}
            </el-tag>
            <div class="dialog-footer-between" style="margin-top: 10px">
              <div><el-tag type="success">添加角色 8/8</el-tag></div>
              <div style="margin-right: 20px">
                <el-tag type="success">编辑账号</el-tag>
                <el-tag type="danger">删除账号</el-tag>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-scrollbar>
    </el-form>
    <template #footer>
      <div class=" dialog-footer-between">
        <div style="width: 220px">
          <el-input v-model="editDialog.loadParams" autocomplete="off" placeholder="尝试启动参数 ">
            <template #append> <el-button @click="tryLoadGame">试运行</el-button></template>
          </el-input>
        </div>
        <div>
          <el-button @click="editDialog.Visible = false">取消</el-button>
          <el-button type="primary" :disabled="true" v-if="!editDialog.form.tryCheck"> 先通过试运行 </el-button>
          <el-button type="primary" @click="handleSubmit" v-else
            :disabled="!(editDialog.form.label.length >= 2 && editDialog.form.tryCheck === true)">
            {{ editDialog.type === 1 ? "添加" : "保存" }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ElMessage } from "element-plus";
export default {
  data() {
    return {
      activeNames: "0",
      editDialog: {
        Visible: false,
        type: 1,
        index: NaN,
        tryCheck: false,
        loadParams: "-w",
        form: {
          label: "",
          dir: "",
          bNet: "",
          gameVer: "",
          inventorySet: "",
          tryCheck: false,
          bagSize: [],
          storageSize: [],
          fzStorageSize: [],
          boxSize: [],
        },
      },
      deleteDialog: { Visible: false, index: NaN, TXT: "" },
      gameConfig: JSON.parse(this.$ahk.fn.loadJson("Setting", "globalData.json")).gameConfig || [],
      bNetList: [],
      gameVerList: [],
      persetForInventory: [],
    };
  },
  mounted() {
  },
  computed: {
    inventorySetState() {
      return this.editDialog.form.inventorySet !== "自定义";
    }
  },
  methods: {
    initSelect() {
      this.bNetList = this.$ahk.fn.LoadFileNameByType("Setting\\bNet", "json").split(",")
      this.gameVerList = this.$ahk.fn.LoadFileNameByType("Setting\\memory", "json").split(",")
      this.persetForInventory = (this.$ahk.fn.LoadFileNameByType("Setting\\bNet", "json") + ",自定义").split(",")
    },
    showDeleteDialog(index) {
      this.deleteDialog.Visible = true;
      this.deleteDialog.index = index;
      this.deleteDialog.TXT = this.gameConfig[index].label;
    },
    newGameConfig() {
      this.initSelect()
      this.editDialog.Visible = true;
      this.editDialog.type = 1;
      this.editDialog.form = {
        label: "",
        dir: "",
        bNet: "原版",
        gameVer: "",
        inventorySet: "原版",
        tryCheck: false,
        bagSize: [],
        storageSize: [],
        fzStorageSize: [],
        boxSize: [],
      };
      this.handleInventorySetChange("原版");
    },
    deleteGameConfig() {
      this.deleteDialog.Visible = false;
      this.gameConfig.splice(this.deleteDialog.index, 1);
      this.saveGameConfig();
    },
    showEditDialog(index) {
      this.initSelect()
      this.editDialog.index = index;
      this.editDialog.type = 2;
      this.editDialog.form = JSON.parse(JSON.stringify(this.gameConfig[index]));
      this.editDialog.Visible = true;
    },
    FileSelect() {
      let result = this.$ahk.fn.FileSelector();
      if (!result) {
        return;
      }
      this.editDialog.form.dir = result;
      this.editDialog.form.tryCheck = false;
    },
    handleSubmit() {
      if (this.editDialog.type === 1) {
        this.gameConfig.push(this.editDialog.form);
      } else {
        this.gameConfig[this.editDialog.index] = this.editDialog.form;
      }
      this.saveGameConfig();
      this.editDialog.Visible = false;
    },
    tryLoadGame() {
      if (!this.editDialog.form.dir) {
        ElMessage.error("游戏目录为空");
        return;
      }
      this.editDialog.form.tryCheck = false;
      this.$ahk.fn.RunGame(this.editDialog.form.dir, this.editDialog.loadParams);
      let result = this.$ahk.fn.WaitingConfirm();
      this.editDialog.form.tryCheck = result == 1;
    },
    handleInventorySetChange(e) {
      if (this.inventorySetState) {
        this.editDialog.form.inventorySet = e
        let result = JSON.parse(this.$ahk.fn.LoadJson("Setting\\bNet", e + ".json")).inventorySet
        this.editDialog.form.bagSize = result.bagSize;
        this.editDialog.form.storageSize = result.storageSize;
        this.editDialog.form.fzStorageSize = result.fzStorageSize;
        this.editDialog.form.boxSize = result.boxSize;
      }
    },

    saveGameConfig() {
      let globalData = JSON.parse(this.$ahk.fn.loadJson("Setting", "globalData.json"))
      globalData.gameConfig = this.gameConfig;
      this.$ahk.fn.SaveFile("Setting\\globalData.json", JSON.stringify(globalData));
    }
  },
}
</script>

<style>
.cfg-card {
  border-radius: 15px;
  margin-top: 10px;
  margin-right: auto;
  width: 100%;
}

.cfg-card-50 {
  cursor: pointer;
  border-radius: 15px;
  margin-top: 10px;
  margin-right: 10px;
  width: 350px;
}

.cfg-card-Rbtn {
  display: flex;
  justify-content: start;
  flex-direction: column;
  align-items: flex-end;
}

.cardBtn:first-child {
  margin-top: 0px;
}

.cardBtn {
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.dialog-footer-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer button {
  margin-left: 10px;
}

.el-tag {
  margin-right: 10px;
  margin-bottom: 5px;
}

.specialSpan>span {
  margin-right: 15px;
  margin-left: 5px;
}

.specialSpan>span:first-child {
  margin-left: 5px;
}

.specialSpan>.el-input-number {
  width: 50px;
}

.specialLabel .el-form-item__label {
  width: 80px;
  justify-content: center;
}

.el-form-item {
  margin-bottom: 6px;
}

.specialAlert {
  width: 385px;
  display: flex;
  justify-content: space-between;
}

.specialAlert div {
  width: 50%;
  font-size: 0.8rem;
}
</style>
