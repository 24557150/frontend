// frontend/js/liff-init.js
import { loadWardrobe } from './upload.js';

const liffId = "2007733246-nAexA2b9";

async function initializeLiff() {
  try {
    await liff.init({ liffId });

    if (!liff.isLoggedIn()) {
      liff.login();
    } else {
      const profile = await liff.getProfile();
      const userId = profile.userId;
      localStorage.setItem('user_id', userId);
      document.getElementById('user-name').innerText = profile.displayName;
      document.getElementById('status').innerText = `✅ 已登入：${profile.displayName}`;
      loadWardrobe(userId);
    }
  } catch (err) {
    console.error("LIFF 初始化失敗:", err);
    document.getElementById('status').innerText = "⚠️ LIFF 初始化失敗";
  }
}

document.addEventListener("DOMContentLoaded", initializeLiff);
