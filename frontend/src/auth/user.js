import { ref } from "vue";
import { http } from "../api.js";

/** 当前登录的普通用户（与管理员 session 独立） */
export const currentUser = ref(null);

export async function refreshUserAuth() {
  try {
    const { data } = await http.get("/api/auth/me", { silent: true });
    currentUser.value = data?.user ?? null;
  } catch {
    currentUser.value = null;
  }
}

export async function logoutUser() {
  try {
    await http.post("/api/auth/logout", {}, { silent: true });
  } finally {
    currentUser.value = null;
  }
}
