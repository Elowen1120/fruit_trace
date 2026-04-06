import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import "./assets/theme.css";

const PAGE_TITLE = "果蔬食品全流程溯源模式设计";

const app = createApp(App);
app.use(router);
router.afterEach(() => {
  document.title = PAGE_TITLE;
});
app.mount("#app");
