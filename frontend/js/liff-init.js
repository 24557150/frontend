// frontend/js/liff-init.js
export const backendURL = 'https://a7946680e883.ngrok-free.app';

import { loadWardrobe } from './upload.js';

const liffId = "2007733246-nAexA2b9";

async function initializeLiff() {
  try {
    await liff.init({ liffId });

    if (!liff.isLoggedIn()) {
      // 修正 iOS：登入後回到目前頁面
      liff.login({ redirectUri: window.location.href });
      return;
    }

    const profile = await liff.getProfile();
    const userId = profile.userId;

    // 儲存真正的 LINE userId（不再使用 demo_user）
    localStorage.setItem('user_id', userId);

    document.getElementById('user-name').innerText = profile.displayName;
    document.getElementById('status').innerText = `✅ 已登入：${profile.displayName}`;

    loadWardrobe(userId);
  } catch (err) {
    console.error("LIFF 初始化失敗:", err);
    document.getElementById('status').innerText = "⚠️ LIFF 初始化失敗";
  }
}

document.addEventListener("DOMContentLoaded", initializeLiff);
