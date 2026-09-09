import { createRouter, createWebHashHistory } from "vue-router";
import empty from '@/views/empty.vue'


const routes = [
  {
    path: "/",
    name: "home",
    component: empty
  }
];

const router = createRouter({
  history: createWebHashHistory(process.env.BASE_URL),
  routes,
});

export default router;
