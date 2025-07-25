// frontend/js/liff-init.js
// 統一匯出後端 URL，供所有模組使用
export const backendURL = 'https://liff-test-941374905030.asia-east1.run.app';

const liffId = "2007733246-nAexA2b9"; // 你現有的 LIFF ID

// 用於儲存根據頁面動態載入的功能模組中的載入函數
let loadContentFunction; 

async function initializeLiff() {
  try {
    await liff.init({ liffId });
    console.log("DEBUG: LIFF 初始化成功。");

    if (!liff.isLoggedIn()) {
      console.log("DEBUG: 未登入，導向登入頁面。");
      // 使用固定 GitHub Pages 網址，避免 iOS 無法登入
      liff.login({ redirectUri: "https://24557150.github.io/liff-test/" });
      return;
    }

    const profile = await liff.getProfile();
    const userId = profile.userId;

    window.userId = userId; // 將 userId 賦值給 window.userId，讓其他模組可以存取
    localStorage.setItem('user_id', userId);

    const userNameElement = document.getElementById('user-name');
    if (userNameElement) {
      userNameElement.innerText = profile.displayName;
    }
    // 根據當前頁面判斷更新哪個狀態元素
    const statusElement = document.getElementById('status') || document.getElementById('wannabe-status');
    if (statusElement) {
        statusElement.innerText = `✅ 已登入：${profile.displayName}`;
    }
    console.log("DEBUG: 用戶已登入，userId 設定為:", userId);

    // 根據當前頁面路徑動態導入對應的 JavaScript 檔案
    if (window.location.pathname.includes('wannabe.html')) {
        // 動態導入 wannabe-upload.js
        const { loadWannabeWardrobe } = await import('./wannabe-upload.js');
        loadContentFunction = loadWannabeWardrobe;
        console.log("DEBUG: 在 wannabe.html 中載入 loadWannabeWardrobe。");
    } else {
        // 預設為 index.html，動態導入 upload.js
        const { loadWardrobe } = await import('./upload.js');
        loadContentFunction = loadWardrobe;
        console.log("DEBUG: 在 index.html 中載入 loadWardrobe。");
    }

    // 確保 loadContentFunction 已經被賦值後再調用
    if (loadContentFunction) {
      loadContentFunction(); // 調用對應頁面的載入函數
    } else {
      console.warn("WARN: loadContentFunction 仍未定義，無法載入圖片。"); 
    }

  } catch (err) {
    console.error("❌ LIFF 初始化失敗:", err);
    // 根據當前頁面判斷更新哪個狀態元素
    const statusElement = document.getElementById('status') || document.getElementById('wannabe-status');
    if (statusElement) {
        statusElement.innerText = "⚠️ LIFF 初始化失敗";
    }
  }
}

document.addEventListener("DOMContentLoaded", initializeLiff);
