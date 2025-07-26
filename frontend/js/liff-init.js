// frontend/js/liff-init.js
// 統一匯出後端 URL，供所有模組使用
export const backendURL = 'https://liff-test-941374905030.asia-east1.run.app';

const liffId = "2007733246-nAexA2b9"; // 你現有的 LIFF ID

// 用於儲存根據頁面動態載入的功能模組中的載入函數
let loadContentFunction; 
let initPageFeaturesFunction; // 新增一個變數來儲存頁面初始化功能

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
    try {
        if (window.location.pathname.includes('wannabe.html')) {
            const { loadWannabeWardrobe, initWannabeFeatures } = await import('./wannabe-upload.js');
            loadContentFunction = loadWannabeWardrobe;
            initPageFeaturesFunction = initWannabeFeatures; // 儲存初始化功能
            console.log("DEBUG: 在 wannabe.html 中載入 loadWannabeWardrobe 和 initWannabeFeatures。");
        } else {
            const { loadWardrobe, initUploadFeatures } = await import('./upload.js'); // 導入新的 initUploadFeatures
            loadContentFunction = loadWardrobe;
            initPageFeaturesFunction = initUploadFeatures; // 儲存初始化功能
            console.log("DEBUG: 在 index.html 中載入 loadWardrobe 和 initUploadFeatures。");
        }
    } catch (importError) {
        console.error("ERROR: 動態導入模組失敗:", importError);
        if (statusElement) {
            statusElement.innerText = `❌ 載入頁面功能失敗: ${importError.message}`;
        }
        return; // 導入失敗則直接返回，不執行後續的 loadContentFunction()
    }

    console.log("DEBUG: loadContentFunction 和 initPageFeaturesFunction 已被賦值，等待 DOMContentLoaded 觸發。");


  } catch (err) {
    console.error("❌ LIFF 初始化失敗:", err);
    // 根據當前頁面判斷更新哪個狀態元素
    const statusElement = document.getElementById('status') || document.getElementById('wannabe-status');
    if (statusElement) {
        statusElement.innerText = "⚠️ LIFF 初始化失敗";
    }
  }
}

// 將 initializeLiff() 的調用放在 DOMContentLoaded 內部，確保所有元素都已載入
document.addEventListener("DOMContentLoaded", async () => {
    await initializeLiff(); // 首先初始化 LIFF

    // 在 LIFF 初始化成功且頁面初始化功能已準備好後，再調用它
    if (initPageFeaturesFunction) {
        initPageFeaturesFunction(); // 調用對應頁面的初始化功能 (例如綁定按鈕)
        console.log("DEBUG: DOMContentLoaded 觸發，並調用 initPageFeaturesFunction。");
    } else {
        console.warn("WARN: DOMContentLoaded 後 initPageFeaturesFunction 仍未定義，無法初始化頁面功能。");
    }

    // 最後調用載入內容的函式
    if (loadContentFunction) {
        loadContentFunction(); // 調用對應頁面的載入函數
        console.log("DEBUG: DOMContentLoaded 觸發，並調用 loadContentFunction。"); // 調整日誌位置
    } else {
        console.warn("WARN: DOMContentLoaded 後 loadContentFunction 仍未定義，無法載入圖片。");
    }
});
