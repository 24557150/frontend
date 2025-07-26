// frontend/js/upload.js
// 從 liff-init.js 導入 backendURL
import { backendURL } from './liff-init.js';

// 處理圖片上傳的主函式
async function uploadImages(event) {
  console.log("DEBUG: uploadImages 被觸發 (來自 input change 事件)");

  const input = event.target;
  const category = document.getElementById('category').value;
  const userId = window.userId;

  console.log("DEBUG: 當前 userId:", userId);
  console.log("DEBUG: 當前 category:", category);

  if (!userId || !category) {
    console.warn("WARN: userId 或 category 缺失，無法上傳", { userId, category });
    document.getElementById('status').innerText = "⚠️ 請先登入或選擇類別";
    input.value = '';
    return;
  }

  const files = input.files;
  console.log("DEBUG: 選擇的檔案數量:", files.length);

  if (!files.length) {
    console.warn("WARN: 未選擇任何檔案");
    document.getElementById('status').innerText = "未選擇圖片";
    return;
  }

  document.getElementById('status').innerText = "🔄 正在上傳...";

  for (const file of files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('user_id', userId);

    console.log(`DEBUG: 開始上傳檔案 ${file.name} (${file.size} bytes)`);

    try {
      const res = await fetch(`${backendURL}/upload`, {
        method: 'POST',
        body: formData,
      });

      console.log("DEBUG: 後端回應狀態:", res.status);
      const data = await res.json();
      console.log("DEBUG: 後端回應資料:", data);

      if (data.status === 'ok') {
        console.log("INFO: 上傳成功，重新載入衣櫃");
        document.getElementById('status').innerText = "✅ 上傳成功！";
        loadWardrobe();
      } else {
        console.error("ERROR: 上傳失敗 (後端回傳錯誤):", data.message);
        document.getElementById('status').innerText = `❌ 上傳失敗: ${data.message}`;
      }
    } catch (err) {
      console.error("❌ 上傳過程錯誤 (Fetch 或 JSON 解析失敗):", err);
      document.getElementById('status').innerText = `❌ 上傳失敗: ${err.message}`;
    }
  }

  input.value = ''; // 清空選擇，以便下次能重複選同檔案
}

// 載入衣櫃內容
export async function loadWardrobe(category = "all") {
  const userId = window.userId;
  console.log("DEBUG: 執行 loadWardrobe，類別:", category, "userId:", userId);

  if (!userId) {
    console.warn("WARN: userId 缺失，無法載入衣櫃");
    return;
  }

  try {
    const url = `${backendURL}/wardrobe?user_id=${userId}&category=${category}`;
    console.log("DEBUG: 從後端獲取衣櫃資料:", url);
    const res = await fetch(url);
    const data = await res.json();
    console.log("DEBUG: 後端回應衣櫃資料:", data);
    displayImages(data.images);
  } catch (err) {
    console.error("❌ 載入衣櫃失敗", err);
  }
}

// 顯示圖片
function displayImages(images) {
  console.log("DEBUG: displayImages 開始，圖片數量:", images.length);

  const categorySections = {
    "top": document.getElementById("top-container"),
    "bottom": document.getElementById("bottom-container"),
    "skirt": document.getElementById("skirt-container"),
    "dress": document.getElementById("dress-container"),
    "shoes": document.getElementById("shoes-container")
  };

  // 清空各分類容器
  for (const key in categorySections) {
    if (categorySections[key]) {
      categorySections[key].innerHTML = "";
      console.log(`DEBUG: 已清空 ${key}-container`);
    }
  }

  images.forEach(img => {
    if (categorySections[img.category]) {
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

      console.log(`DEBUG: 已添加圖片 (${img.category}): ${img.path}`);
    } else {
      console.warn(`WARN: 找不到分類 ${img.category}，圖片路徑: ${img.path}`);
    }
  });
}

// 刪除已選圖片
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
    console.error("❌ 刪除過程錯誤", err);
    document.getElementById('status').innerText = `❌ 刪除失敗: ${err.message}`;
  }
}

// 新增：頁面初始化函式 (給 liff-init.js 調用)
export function initUploadFeatures() {
  console.log("DEBUG: 初始化 upload 頁面功能");
  const uploadButton = document.getElementById('upload-button');
  const imageInput = document.getElementById('image-input');

  console.log("DEBUG: 綁定前取得元素 uploadButton:", uploadButton);
  console.log("DEBUG: 綁定前取得元素 imageInput:", imageInput);

  if (uploadButton && imageInput) {
    uploadButton.addEventListener('click', () => {
      console.log("DEBUG: 上傳按鈕被點擊，觸發選擇框");
      imageInput.click();
    });
    imageInput.addEventListener('change', uploadImages);
    console.log("DEBUG: 已完成上傳按鈕與檔案輸入框綁定");
  } else {
    console.warn("WARN: 找不到 uploadButton 或 imageInput，無法綁定事件");
  }

  const deleteButton = document.getElementById('delete-button');
  if (deleteButton) {
    deleteButton.addEventListener('click', deleteSelected);
    console.log("DEBUG: 已綁定刪除按鈕");
  }
}