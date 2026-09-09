<template>
  <div @click="refresh">setting！</div>
</template>
<script>
export default {
  data() {
    return {};
  },
  methods: {
    refresh() {
      location.reload();
    },
  },
};
</script>
