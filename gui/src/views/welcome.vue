<template>
  <div>
    <h1>暗黑2工具箱</h1>
    <el-alert class="alert" type="warning" show-icon :closable="false">
      <p>!!!注意 部分功能基于内存读取,会被战网检测.</p>
    </el-alert>
    <el-alert class="alert" type="info" :closable="false">
      <p>
        内存读取基于1.13c,适配其他版本请前往项目目录下的setting\memory文件夹自行添加配置.
        <br />
        <br />
        读取范围:
        <br />
        背包 仓库 盒子 物品码表 展开的菜单标识 所处界面 战网角色列表
      </p>
    </el-alert>
    <el-alert class="alert" type="info" :closable="false">
      <p>
        功能
        <br />
        <br />
        游戏多开 同账号登录断开自动重进 仓库模板 人物保活 仓库翻页快捷键 传送阵快捷键 合成查询
        <br />
        <br />
        离线仓检
      </p>
    </el-alert>
  </div>
</template>
<script>
export default {
  data() {
    return {
      val: Math.random(),
    };
  },
  methods: {},
};
</script>

<style scoped>
.alert {
  margin-bottom: 10px;
}
</style>
