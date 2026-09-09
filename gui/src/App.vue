<template>
  <div class="app-shell">
    <Launcher />
  </div>
</template>

<script>
import Launcher from "@/views/launcher.vue";

export default {
  components: { Launcher },
  mounted() {
    localStorage.getItem("theme") === "dark" && document.documentElement.classList.add("dark");
  },
};
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  overflow: hidden; /* 外层禁止滚动：滚动只发生在内部区域 */
}
body {
  background-color: #252525;
  user-select: none;
  font-family: "微软雅黑";
}

#app {
  zoom: 1;
}

.app-shell {
  height: 100vh;
  overflow: hidden;
  box-sizing: border-box;
}
</style>
