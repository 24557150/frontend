// frontend/js/upload.js
// 從 liff-init.js 導入 backendURL
import { backendURL } from './liff-init.js'; 

async function uploadImages() {
  console.log("DEBUG: uploadImages 函式開始執行。"); // 新增日誌
  
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
  console.log("DEBUG: 獲取到的檔案物件 (input.files):", files); // 新增日誌
  console.log("DEBUG: 選擇的檔案數量 (files.length):", files.length); // 新增日誌

  if (!files.length) {
    console.warn("WARN: 未選擇任何檔案，無法上傳。");
    document.getElementById('status').innerText = "未選擇圖片";
    return; 
  }

  document.getElementById('status').innerText = "🔄 正在上傳...";

  for (const file of files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('user_id', userId);

    console.log(`DEBUG: 正在上傳檔案: ${file.name}, 大小: ${file.size} bytes`);
    
    try {
      const res = await fetch(`${backendURL}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      console.log("DEBUG: 收到後端響應狀態:", res.status);
      const data = await res.json();
      console.log("DEBUG: 後端響應數據:", data);

      if (data.status === 'ok') {
        console.log("INFO: 上傳成功，正在重新載入衣櫃。");
        document.getElementById('status').innerText = "✅ 上傳成功！";
        loadWardrobe(); 
      } else {
        console.error("ERROR: 後端返回錯誤狀態:", data.message);
        document.getElementById('status').innerText = `❌ 上傳失敗: ${data.message}`;
      }
    } catch (err) {
      console.error('❌ 上傳錯誤 (Fetch 或 JSON 解析失敗):', err);
      document.getElementById('status').innerText = `❌ 上傳失敗: ${err.message}`;
    }
  }
}

// 這裡已經有 export 關鍵字，無需在檔案末尾重複導出
export async function loadWardrobe(category = "all") { 
  const userId = window.userId;
  console.log("DEBUG: loadWardrobe 函式開始執行，載入類別:", category, "userId:", userId); 
  if (!userId) {
    console.warn("WARN: 載入衣櫃時 userId 缺失。");
    return;
  }

  try {
    const url = `${backendURL}/wardrobe?user_id=${userId}&category=${category}`;
    console.log("DEBUG: 正在從後端獲取衣櫃數據:", url); 
    const res = await fetch(url);
    const data = await res.json();
    console.log("DEBUG: 後端衣櫃數據載入成功:", data); 
    displayImages(data.images);
  } catch (err) {
    console.error("❌ 載入衣櫃失敗", err);
  }
}

function displayImages(images) {
  console.log("DEBUG: displayImages 函式開始執行，接收到圖片數量:", images.length);
  console.log("DEBUG: displayImages 接收到的圖片數據:", images);

  const categorySections = {
    "top": document.getElementById("top-container"),
    "bottom": document.getElementById("bottom-container"),
    "skirt": document.getElementById("skirt-container"),
    "dress": document.getElementById("dress-container"),
    "shoes": document.getElementById("shoes-container")
  };

  for (const key in categorySections) {
      if (categorySections[key]) {
          categorySections[key].innerHTML = "";
          console.log(`DEBUG: 清空容器: ${key}-container`); 
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
      console.log(`DEBUG: 添加圖片到 ${img.category} 分類: ${img.path}`); 
    } else {
      console.warn(`WARN: 圖片類別 '${img.category}' 無法識別或對應的容器不存在。圖片路徑: ${img.path}`); 
    }
  });
}

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

// 按鈕綁定
document.addEventListener('DOMContentLoaded', () => {
  console.log("DEBUG: DOMContentLoaded 事件觸發，開始綁定按鈕。");
  const uploadButton = document.getElementById('upload-button');
  console.log("DEBUG: 獲取到的 uploadButton 元素:", uploadButton); // 新增這行日誌
  if (uploadButton) {
    uploadButton.addEventListener('click', uploadImages); 
    console.log("DEBUG: '上傳' 按鈕綁定完成。"); 
  } else {
    console.warn("WARN: 找不到 'upload-button' 元素。"); 
  }

  const deleteButton = document.getElementById('delete-button');
  if (deleteButton) {
    deleteButton.addEventListener('click', deleteSelected);
    console.log("DEBUG: '刪除選取圖片' 按鈕綁定完成。"); 
  } else {
    console.warn("WARN: 找不到 'delete-button' 元素。"); 
  }
  
  document.getElementById('all-button').addEventListener('click', () => loadWardrobe("all"));
  document.getElementById('top-button').addEventListener('click', () => loadWardrobe("top"));
  document.getElementById('bottom-button').addEventListener('click', () => loadWardrobe("bottom"));
  document.getElementById('skirt-button').addEventListener('click', () => loadWardrobe("skirt"));
  document.getElementById('dress-button').addEventListener('click', () => loadWardrobe("dress"));
  document.getElementById('shoes-button').addEventListener('click', () => loadWardrobe("shoes"));
  console.log("DEBUG: 分類按鈕綁定完成。");
});
