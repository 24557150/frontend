// frontend/js/liff-init.js

// ✅ 使用你的 ngrok 公開網址作為後端 API 基礎路徑
const backendURL = 'https://7d3e145bb3d0.ngrok-free.app';

import { loadWardrobe } from './upload.js';

const liffId = "2007733246-nAexA2b9"; // 請確認這是你在 LINE Developer 註冊的 LIFF ID

async function initializeLiff() {
  try {
    await liff.init({ liffId });

    if (!liff.isLoggedIn()) {
      liff.login();
    } else {
      const profile = await liff.getProfile();
      const userId = profile.userId;

      // 儲存 userId 到本地儲存
      localStorage.setItem('user_id', userId);

      // 顯示登入資訊
      document.getElementById('user-name').innerText = profile.displayName;
      document.getElementById('status').innerText = `✅ 已登入：${profile.displayName}`;

      // 載入使用者衣櫃資料（會透過 upload.js 的 fetch 傳到 backendURL）
      loadWardrobe(userId);
    }
  } catch (err) {
    console.error("LIFF 初始化失敗:", err);
    document.getElementById('status').innerText = "⚠️ LIFF 初始化失敗";
  }
}

document.addEventListener("DOMContentLoaded", initializeLiff);

