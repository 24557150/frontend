// frontend/js/upload.js
import { backendURL } from './liff-init.js';

// 支援多張圖片上傳，避免每張上傳後立即刷新
async function uploadImages(event) {
  console.log("DEBUG: uploadImages 被觸發 (支援多檔案)");

  const input = event.target;
  const category = document.getElementById('category').value;
  const userId = window.userId;

  if (!userId || !category) {
    console.warn("WARN: userId 或 category 缺失");
    document.getElementById('status').innerText = "⚠️ 請先登入或選擇類別";
    input.value = '';
    return;
  }

  const files = input.files;
  if (!files.length) {
    console.warn("WARN: 沒有選擇檔案");
    document.getElementById('status').innerText = "未選擇圖片";
    return;
  }

  document.getElementById('status').innerText = `🔄 正在上傳 ${files.length} 張圖片...`;

  let successCount = 0, failCount = 0;

  for (const file of files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('user_id', userId);

    console.log(`DEBUG: 準備上傳 ${file.name} (${file.size} bytes)`);

    try {
      const res = await fetch(`${backendURL}/upload`, { method: 'POST', body: formData });
      const data = await res.json();

      if (data.status === 'ok') {
        successCount++;
        console.log(`INFO: ${file.name} 上傳成功`);
      } else {
        failCount++;
        console.error(`ERROR: ${file.name} 上傳失敗:`, data.message);
      }
    } catch (err) {
      failCount++;
      console.error(`❌ ${file.name} 上傳錯誤:`, err);
    }
  }

  document.getElementById('status').innerText =
    `✅ 成功上傳 ${successCount} 張，❌ 失敗 ${failCount} 張`;

  loadWardrobe();  // 全部上傳完才刷新衣櫃
  input.value = '';  // 重置檔案選擇框
}

// 載入衣櫃圖片
export async function loadWardrobe(category = "all") {
  const userId = window.userId;
  if (!userId) {
    console.warn("WARN: userId 缺失，無法載入");
    return;
  }

  try {
    const url = `${backendURL}/wardrobe?user_id=${userId}&category=${category}`;
    console.log("DEBUG: 從後端獲取衣櫃:", url);
    const res = await fetch(url);
    const data = await res.json();
    displayImages(data.images);
  } catch (err) {
    console.error("❌ 載入衣櫃失敗", err);
  }
}

// 顯示圖片
function displayImages(images) {
  const categorySections = {
    "top": document.getElementById("top-container"),
    "bottom": document.getElementById("bottom-container"),
    "skirt": document.getElementById("skirt-container"),
    "dress": document.getElementById("dress-container"),
    "shoes": document.getElementById("shoes-container")
  };

  for (const key in categorySections) {
    if (categorySections[key]) categorySections[key].innerHTML = "";
  }

  images.forEach(img => {
    if (!categorySections[img.category]) return;

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
    caption.textContent = img.tags ? img.tags : "(描述生成中...)";
    caption.style.margin = "6px 0 4px 0";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.path = img.path;
    checkbox.style.marginTop = "5px";

    wrapper.appendChild(imgElement);
    wrapper.appendChild(caption);
    wrapper.appendChild(checkbox);
    categorySections[img.category].appendChild(wrapper);
  });
}

// 刪除選取的圖片
async function deleteSelected() {
  const userId = window.userId;
  if (!userId) return;

  const checkboxes = document.querySelectorAll("#image-list input[type=checkbox]:checked");
  if (!checkboxes.length) return;

  const paths = Array.from(checkboxes).map(cb => cb.dataset.path);
  try {
    const res = await fetch(`${backendURL}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, paths }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('status').innerText = "✅ 刪除成功！";
      loadWardrobe();
    } else {
      document.getElementById('status').innerText = `❌ 刪除失敗: ${data.message}`;
    }
  } catch (err) {
    console.error("❌ 刪除錯誤", err);
    document.getElementById('status').innerText = `❌ 刪除失敗: ${err.message}`;
  }
}

// 初始化 (由 liff-init.js 呼叫)
export function initUploadFeatures() {
  const uploadButton = document.getElementById('upload-button');
  const imageInput = document.getElementById('image-input');
  if (uploadButton && imageInput) {
    uploadButton.addEventListener('click', () => imageInput.click());
    imageInput.addEventListener('change', uploadImages);
  }
  const deleteButton = document.getElementById('delete-button');
  if (deleteButton) deleteButton.addEventListener('click', deleteSelected);
}
