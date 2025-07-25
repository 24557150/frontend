// frontend/js/liff-init.js
// 導入 backendURL，確保所有使用它的模組都有一致的定義
export const backendURL = 'https://liff-test-941374905030.asia-east1.run.app';

// 根據當前頁面判斷要載入哪個功能模組
// 這是一個更彈性的方式來處理不同頁面載入不同模組的需求
let loadFunction;
if (window.location.pathname.includes('wannabe.html')) {
  // 如果是 wannabe.html 頁面，則從 wannabe-upload.js 導入
  import('./wannabe-upload.js')
    .then(module => {
      loadFunction = module.loadWannabeWardrobe;
      console.log("DEBUG: 在 wannabe.html 中載入 loadWannabeWardrobe。");
    })
    .catch(err => console.error("ERROR: 載入 wannabe-upload.js 失敗:", err));
} else {
  // 否則（假設是 index.html 或其他預設頁面），從 upload.js 導入
  import('./upload.js')
    .then(module => {
      loadFunction = module.loadWardrobe;
      console.log("DEBUG: 在 index.html 中載入 loadWardrobe。");
    })
    .catch(err => console.error("ERROR: 載入 upload.js 失敗:", err));
}


const liffId = "2007733246-nAexA2b9"; // 你現有的 LIFF ID

async function initializeLiff() {
  try {
    await liff.init({ liffId });
    console.log("DEBUG: LIFF 初始化成功。");

    if (!liff.isLoggedIn()) {
      console.log("DEBUG: 未登入，導向登入頁面。");
      liff.login({ redirectUri: window.location.href }); // 使用當前頁面作為重定向URI
      return;
    }

    const profile = await liff.getProfile();
    const userId = profile.userId;

    window.userId = userId; // 將 userId 賦值給 window.userId，讓其他模組可以存取
    localStorage.setItem('user_id', userId);

    // 更新用戶名顯示，這在兩個頁面都通用
    const userNameElement = document.getElementById('user-name');
    if (userNameElement) {
      userNameElement.innerText = profile.displayName;
    }
    const statusElement = document.getElementById('status') || document.getElementById('wannabe-status');
    if (statusElement) {
      statusElement.innerText = `✅ 已登入：${profile.displayName}`;
    }
    console.log("DEBUG: 用戶已登入，userId 設定為:", userId);

    // 確保 loadFunction 已經被賦值
    if (loadFunction) {
      loadFunction(); // 調用對應頁面的載入函數
    } else {
      // 延遲執行，直到 loadFunction 被設置
      setTimeout(() => {
          if (loadFunction) loadFunction();
          else console.warn("WARN: loadFunction 仍未定義，無法載入圖片。");
      }, 500); // 短暫延遲
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