<template>
  <div @click="val = Math.random()">dataLibrary！{{ val }}</div>
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
