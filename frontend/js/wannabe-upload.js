// frontend/js/wannabe-upload.js
import { backendURL } from './liff-init.js';

// 上傳並即時顯示「我想成為」圖片（去背結果）
async function uploadWannabeImages() {
  console.log("DEBUG: uploadWannabeImages 被觸發 (支援多檔案 & 即時顯示)");

  const input = document.getElementById('wannabe-image-input');
  const userId = window.userId;

  if (!userId) {
    document.getElementById('wannabe-status').innerText = "⚠️ 請先登入";
    return;
  }

  const files = input.files;
  if (!files.length) {
    document.getElementById('wannabe-status').innerText = "未選擇圖片";
    return;
  }

  document.getElementById('wannabe-status').innerText = `🔄 上傳中 (${files.length} 張)...`;

  let successCount = 0, failCount = 0;

  for (const file of files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('user_id', userId);

    console.log(`DEBUG: 上傳 ${file.name} (${file.size} bytes) 到 /upload_wannabe`);

    try {
      const res = await fetch(`${backendURL}/upload_wannabe`, { method: 'POST', body: formData });
      const data = await res.json();

      if (data.status === 'ok') {
        successCount++;
        console.log(`INFO: ${file.name} 上傳成功，立即顯示去背結果`);

        // 即時把回傳的 URL 加入畫面
        appendWannabeImage(data.path);
      } else {
        failCount++;
        console.error(`ERROR: ${file.name} 上傳失敗:`, data.message);
      }
    } catch (err) {
      failCount++;
      console.error(`❌ ${file.name} 上傳錯誤:`, err);
    }
  }

  document.getElementById('wannabe-status').innerText =
    `✅ 成功 ${successCount} 張，❌ 失敗 ${failCount} 張`;

  // 全部完成後再刷新一次，確保資料與 Firestore 同步
  loadWannabeWardrobe();
  input.value = '';
}

// 即時插入單張圖片到頁面
function appendWannabeImage(url) {
  const container = document.getElementById("wannabe-container");
  if (!container) return;

  const wrapper = document.createElement("div");
  wrapper.className = "image-item";
  wrapper.style.display = "inline-block";
  wrapper.style.margin = "10px";
  wrapper.style.textAlign = "center";

  const imgElement = document.createElement("img");
  imgElement.src = url;
  imgElement.style.width = "150px";
  imgElement.style.borderRadius = "8px";

  const caption = document.createElement("div");
  caption.style.fontSize = "0.9em";
  caption.textContent = ""; // 「我想成為」暫無標籤
  caption.style.margin = "6px 0 4px 0";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.dataset.path = url;
  checkbox.style.marginTop = "5px";

  wrapper.appendChild(imgElement);
  wrapper.appendChild(caption);
  wrapper.appendChild(checkbox);
  container.prepend(wrapper);  // 新圖放最上面
}

// 從後端載入「我想成為」圖片
export async function loadWannabeWardrobe() {
  const userId = window.userId;
  if (!userId) return;

  try {
    const url = `${backendURL}/wannabe_wardrobe?user_id=${userId}`;
    const res = await fetch(url);
    const data = await res.json();
    displayWannabeImages(data.images);
  } catch (err) {
    console.error("❌ 載入 wannabe 圖片失敗", err);
  }
}

// 顯示所有「我想成為」圖片
function displayWannabeImages(images) {
  const container = document.getElementById("wannabe-container");
  if (!container) return;

  container.innerHTML = "";
  if (!images.length) {
    container.innerHTML = "<p>尚未上傳「我想成為」圖片。</p>";
    return;
  }

  images.forEach(img => appendWannabeImage(img.path));
}

// 刪除選取的「我想成為」圖片
async function deleteSelectedWannabe() {
  const userId = window.userId;
  if (!userId) return;

  const checkboxes = document.querySelectorAll("#wannabe-image-list input[type=checkbox]:checked");
  if (!checkboxes.length) return;

  const paths = Array.from(checkboxes).map(cb => cb.dataset.path);

  try {
    const res = await fetch(`${backendURL}/delete_wannabe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, paths }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('wannabe-status').innerText = "✅ 刪除成功！";
      loadWannabeWardrobe();
    } else {
      document.getElementById('wannabe-status').innerText = `❌ 刪除失敗: ${data.message}`;
    }
  } catch (err) {
    console.error("❌ 刪除錯誤", err);
    document.getElementById('wannabe-status').innerText = `❌ 刪除失敗: ${err.message}`;
  }
}

// 初始化 (由 liff-init.js 呼叫)
export function initWannabeFeatures() {
  const uploadBtn = document.getElementById('wannabe-upload-button');
  const input = document.getElementById('wannabe-image-input');
  if (uploadBtn && input) {
    uploadBtn.addEventListener('click', () => input.click());
    input.addEventListener('change', uploadWannabeImages);
  }

  const deleteBtn = document.getElementById('wannabe-delete-button');
  if (deleteBtn) deleteBtn.addEventListener('click', deleteSelectedWannabe);
}
