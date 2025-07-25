    // frontend/js/liff-init.js
    // 統一匯出後端 URL，供所有模組使用
    export const backendURL = 'https://liff-test-941374905030.asia-east1.run.app';

    const liffId = "2007733246-nAexA2b9"; // 你現有的 LIFF ID

    // 用於儲存根據頁面動態載入的功能模組中的載入函數
    let loadContentFunction; 

    // frontend/js/liff-init.js
// ... (其他部分保持不變)

async function initializeLiff() {
  try {
    await liff.init({ liffId });
    console.log("DEBUG: LIFF 初始化成功。");

    if (!liff.isLoggedIn()) {
      console.log("DEBUG: 未登入，導向登入頁面。");
      liff.login({ redirectUri: "https://24557150.github.io/liff-test/" });
      return;
    }

    const profile = await liff.getProfile();
    const userId = profile.userId;

    window.userId = userId;
    localStorage.setItem('user_id', userId);

    const userNameElement = document.getElementById('user-name');
    if (userNameElement) {
      userNameElement.innerText = profile.displayName;
    }
    const statusElement = document.getElementById('status') || document.getElementById('wannabe-status'); // 兼容兩個頁面
    if (statusElement) {
        statusElement.innerText = `✅ 已登入：${profile.displayName}`;
    }
    console.log("DEBUG: 用戶已登入，userId 設定為:", userId);

    // 根據當前頁面路徑動態導入對應的 JavaScript 檔案
    if (window.location.pathname.includes('wannabe.html')) {
        const { loadWannabeWardrobe } = await import('./wannabe-upload.js');
        loadContentFunction = loadWannabeWardrobe;
        console.log("DEBUG: 在 wannabe.html 中載入 loadWannabeWardrobe。");
    } else {
        const { loadWardrobe } = await import('./upload.js');
        loadContentFunction = loadWardrobe;
        console.log("DEBUG: 在 index.html 中載入 loadWardrobe。");
    }

    if (loadContentFunction) {
      loadContentFunction();
    } else {
      console.warn("WARN: loadContentFunction 仍未定義，無法載入圖片。");
    }

  } catch (err) {
    console.error("❌ LIFF 初始化失敗:", err);
    const statusElement = document.getElementById('status') || document.getElementById('wannabe-status');
    if (statusElement) {
        statusElement.innerText = "⚠️ LIFF 初始化失敗";
    }
  }
}

document.addEventListener("DOMContentLoaded", initializeLiff);