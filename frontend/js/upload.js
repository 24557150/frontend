// frontend/js/upload.js
// 從 liff-init.js 導入 backendURL
import { backendURL } from './liff-init.js'; 

// 移除 testUploadClick 函式和其 export

async function uploadImages() {
  console.log("DEBUG: uploadImages 函式被點擊，準備上傳圖片。"); // 新增日誌
  
  const input = document.getElementById('image-input');
  const category = document.getElementById('category').value;
  const userId = window.userId; 

  console.log("DEBUG: 獲取到的 userId (uploadImages):", userId);
  console.log("DEBUG: 獲取到的 category (uploadImages):", category);

  if (!userId || !category) {
    console.warn("WARN: userId 或 category 缺失，無法上傳。", { userId, category });
    document.getElementById('status').innerText = "⚠️ 請先登入或選擇類別";
    return; 
  }

  const files = input.files;
  console.log("DEBUG: 選擇的檔案數量:", files.length);

  if (!files.length) {
    console.warn("WARN: 未選擇任何檔案，無法上傳。");
    document.getElementById('status').innerText = "未選擇圖片";
    return; 
  }
