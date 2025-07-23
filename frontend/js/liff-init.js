// frontend/js/liff-init.js
export const backendURL = 'https://ai-outfit-1027775725754.asia-east1.run.app';

import { loadWardrobe } from './upload.js';

const liffId = "2007733246-nAexA2b9"; // 你現有的 LIFF ID

async function initializeLiff() {
  try {
    await liff.init({ liffId });

    if (!liff.isLoggedIn()) {
      // 使用固定 GitHub Pages 網址，避免 iOS 無法登入
      liff.login({ redirectUri: "https://24557150.github.io/liff-test/" });
      return;
    }

    const profile = await liff.getProfile();
    const userId = profile.userId;

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
