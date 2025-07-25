// frontend/js/liff-init.js
export const backendURL = 'https://liff-test-941374905030.asia-east1.run.app';

import { loadWardrobe } from './upload.js';

const liffId = "2007733246-nAexA2b9"; // 你現有的 LIFF ID

async function initializeLiff() {
  try {
    await liff.init({ liffId });
    console.log("DEBUG: LIFF 初始化成功。"); // 新增除錯訊息

    if (!liff.isLoggedIn()) {
      console.log("DEBUG: 未登入，導向登入頁面。"); // 新增除錯訊息
      // 使用固定 GitHub Pages 網址，避免 iOS 無法登入
      liff.login({ redirectUri: "https://24557150.github.io/liff-test/" });
      return;
    }

    const profile = await liff.getProfile();
    const userId = profile.userId;

    // --- 新增這一行！ ---
    window.userId = userId; // 將 userId 賦值給 window.userId，讓其他模組可以存取
    // -------------------

    localStorage.setItem('user_id', userId);

    document.getElementById('user-name').innerText = profile.displayName;
    document.getElementById('status').innerText = `✅ 已登入：${profile.displayName}`;
    console.log("DEBUG: 用戶已登入，userId 設定為:", userId); // 新增除錯訊息

    // 這裡調用 loadWardrobe 應該是為了初始化顯示衣櫃內容，
    // 因為 upload.js 的 loadWardrobe 已經是傳入 userId 的，所以這個參數是有效的
    loadWardrobe(); // 調用 loadWardrobe 以顯示用戶衣櫃
  } catch (err) {
    console.error("❌ LIFF 初始化失敗:", err); // 讓錯誤訊息更明顯
    document.getElementById('status').innerText = "⚠️ LIFF 初始化失敗";
  }
}

document.addEventListener("DOMContentLoaded", initializeLiff);