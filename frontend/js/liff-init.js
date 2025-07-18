// frontend/js/liff-init.js
export const backendURL = 'https://7d3e145bb3d0.ngrok-free.app';

import { loadWardrobe } from './upload.js';

const liffId = "2007733246-nAexA2b9";

async function initializeLiff() {
  try {
    await liff.init({ liffId });

    if (!liff.isLoggedIn()) {
      // iOS LINE App 避免登入卡住，加 redirectUri
      liff.login({ redirectUri: window.location.href });
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
