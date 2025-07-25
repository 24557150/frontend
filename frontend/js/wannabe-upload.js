// frontend/js/wannabe-upload.js
// 從 liff-init.js 導入 backendURL
import { backendURL } from './liff-init.js';

/**
 * 上傳「我想成為」圖片到後端。
 */
async function uploadWannabeImages() {
  console.log("DEBUG: 準備上傳「我想成為」圖片 - uploadWannabeImages 函式開始執行");

  const input = document.getElementById('wannabe-image-input');
  const userId = window.userId; // 從 liff-init.js 獲取 user ID

  console.log("DEBUG: 獲取到的 userId (uploadWannabeImages):", userId);

  if (!userId) {
    console.warn("WARN: userId 缺失，無法上傳「我想成為」圖片。");
    document.getElementById('wannabe-status').innerText = "⚠️ 請先登入";
    return;
  }

  const files = input.files;
  console.log("DEBUG: 選擇的檔案數量:", files.length);

  if (!files.length) {
    console.warn("WARN: 未選擇任何檔案，無法上傳。");
    document.getElementById('wannabe-status').innerText = "未選擇圖片";
    return;
  }

  document.getElementById('wannabe-status').innerText = "🔄 正在上傳...";

  for (const file of files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('user_id', userId); // 這裡不需要 category，因為是單一的「我想成為」分類

    console.log(`DEBUG: 正在上傳檔案: ${file.name}, 大小: ${file.size} bytes 到 /upload_wannabe`);

    try {
      const res = await fetch(`${backendURL}/upload_wannabe`, { // 注意這裡呼叫新的後端接口
        method: 'POST',
        body: formData,
      });

      console.log("DEBUG: 收到後端響應狀態:", res.status);
      const data = await res.json();
      console.log("DEBUG: 後端響應數據:", data);

      if (data.status === 'ok') {
        console.log("INFO: 「我想成為」圖片上傳成功，正在重新載入。");
        document.getElementById('wannabe-status').innerText = "✅ 上傳成功！";
        loadWannabeWardrobe(); // 成功後重新載入「我想成為」圖片
      } else {
        console.error("ERROR: 後端返回錯誤狀態:", data.message);
        document.getElementById('wannabe-status').innerText = `❌ 上傳失敗: ${data.message}`;
      }
    } catch (err) {
      console.error('❌ 上傳錯誤 (Fetch 或 JSON 解析失敗):', err);
      document.getElementById('wannabe-status').innerText = `❌ 上傳失敗: ${err.message}`;
    }
  }
}

/**
 * 從後端載入「我想成為」圖片並顯示。
 */
// 這裡已經有 export 關鍵字，無需在檔案末尾重複導出
export async function loadWannabeWardrobe() {
  const userId = window.userId;
  console.log("DEBUG: loadWannabeWardrobe 函式開始執行，userId:", userId);
  if (!userId) {
    console.warn("WARN: 載入「我想成為」圖片時 userId 缺失。");
    return;
  }

  try {
    const url = `${backendURL}/wannabe_wardrobe?user_id=${userId}`; // 注意這裡呼叫新的後端接口
    console.log("DEBUG: 正在從後端獲取「我想成為」圖片數據:", url);
    const res = await fetch(url);
    const data = await res.json();
    console.log("DEBUG: 後端「我想成為」圖片數據載入成功:", data);
    displayWannabeImages(data.images);
  } catch (err) {
    console.error("❌ 載入「我想成為」圖片失敗", err);
  }
}

/**
 * 在頁面上顯示「我想成為」圖片。
 * @param {Array<Object>} images - 包含圖片路徑的物件陣列。
 */
function displayWannabeImages(images) {
  console.log("DEBUG: displayWannabeImages 函式開始執行，接收到圖片數量:", images.length);
  const wannabeContainer = document.getElementById("wannabe-container");
  if (!wannabeContainer) {
      console.error("ERROR: 找不到 wannabe-container 元素。");
      return;
  }
  wannabeContainer.innerHTML = ""; // 清空現有圖片

  if (images.length === 0) {
      wannabeContainer.innerHTML = "<p>尚未上傳「我想成為」的圖片。</p>";
      return;
  }

  images.forEach(img => {
    const wrapper = document.createElement("div");
    wrapper.className = "image-item";
    wrapper.style.display = "inline-block";
    wrapper.style.margin = "10px";
    wrapper.style.textAlign = "center";

    const imgElement = document.createElement("img");
    imgElement.src = img.path;
    imgElement.style.width = "150px";
    imgElement.style.borderRadius = "8px";

    const caption = document.createElement("div");
    caption.style.fontSize = "0.9em";
    caption.textContent = img.tags ? img.tags : ""; // 「我想成為」圖片可能沒有標籤
    caption.style.margin = "6px 0 4px 0";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.path = img.path;
    checkbox.style.marginTop = "5px";

    wrapper.appendChild(imgElement);
    wrapper.appendChild(caption);
    wrapper.appendChild(checkbox);
    wannabeContainer.appendChild(wrapper);
    console.log(`DEBUG: 添加「我想成為」圖片: ${img.path}`);
  });
}

/**
 * 刪除選取的「我想成為」圖片。
 */
async function deleteSelectedWannabe() {
  const userId = window.userId;
  if (!userId) return;
  const checkboxes = document.querySelectorAll("#wannabe-image-list input[type=checkbox]:checked");
  if (!checkboxes.length) return;

  const paths = Array.from(checkboxes).map(cb => cb.dataset.path);

  try {
    const res = await fetch(`${backendURL}/delete_wannabe`, { // 注意這裡呼叫新的後端接口
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, paths }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('wannabe-status').innerText = "✅ 刪除成功！";
      loadWannabeWardrobe(); // 刪除成功後重新載入
    } else {
      document.getElementById('wannabe-status').innerText = `❌ 刪除失敗: ${data.message}`;
    }
  } catch (err) {
    console.error("❌ 刪除「我想成為」圖片錯誤", err);
    document.getElementById('wannabe-status').innerText = `❌ 刪除失敗: ${err.message}`;
  }
}

// 事件監聽器
document.addEventListener('DOMContentLoaded', () => {
  console.log("DEBUG: wannabe-upload.js DOMContentLoaded 事件觸發，開始綁定按鈕。");
  document.getElementById('wannabe-upload-button').addEventListener('click', uploadWannabeImages);
  document.getElementById('wannabe-delete-button').addEventListener('click', deleteSelectedWannabe);
  console.log("DEBUG: wannabe-upload.js 按鈕綁定完成。");
});
