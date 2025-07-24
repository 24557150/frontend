export const backendURL = 'https://liff-test-941374905030.asia-east1.run.app';

async function uploadImages() {
  console.log("準備上傳圖片 - uploadImages 函式開始執行"); // 執行到這裡，表示按鈕事件被觸發
  
  const input = document.getElementById('image-input');
  const category = document.getElementById('category').value;
  const userId = window.userId; // 這裡獲取 userId

  console.log("DEBUG: 獲取到的 userId:", userId);
  console.log("DEBUG: 獲取到的 category:", category);

  if (!userId || !category) {
    console.warn("WARN: userId 或 category 缺失，無法上傳。", { userId, category });
    // 如果這裡 return，Network 標籤會是空的
    return; 
  }

  const files = input.files;
  console.log("DEBUG: 選擇的檔案數量:", files.length);

  if (!files.length) {
    console.warn("WARN: 未選擇任何檔案，無法上傳。");
    // 如果這裡 return，Network 標籤會是空的
    return; 
  }

  console.log("DEBUG: 檔案和資訊都已準備好，開始處理上傳...");

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
        loadWardrobe();
      } else {
        console.error("ERROR: 後端返回錯誤狀態:", data.message);
      }
    } catch (err) {
      console.error('❌ 上傳錯誤 (Fetch 或 JSON 解析失敗):', err); // 捕捉網路錯誤或 JSON 解析錯誤
    }
  }
}

async function loadWardrobe(category = "all") {
  const userId = window.userId;
  if (!userId) {
    console.warn("WARN: 載入衣櫃時 userId 缺失。");
    return;
  }

  try {
    const url = `${backendURL}/wardrobe?user_id=${userId}&category=${category}`;
    console.log("DEBUG: 正在載入衣櫃:", url);
    const res = await fetch(url);
    const data = await res.json();
    console.log("DEBUG: 衣櫃數據載入成功:", data);
    displayImages(data.images);
  } catch (err) {
    console.error("❌ 載入衣櫃失敗", err);
  }
}

function displayImages(images) {
  const imageList = document.getElementById("image-list");
  // 清空現有內容，並保留標題結構
  const categorySections = {
    "top": document.getElementById("top-container"),
    "bottom": document.getElementById("bottom-container"),
    "skirt": document.getElementById("skirt-container"),
    "dress": document.getElementById("dress-container"),
    "shoes": document.getElementById("shoes-container")
  };

  // 清空所有圖片容器
  for (const key in categorySections) {
      if (categorySections[key]) {
          categorySections[key].innerHTML = "";
      }
  }

  const categories = ["top", "bottom", "skirt", "dress", "shoes"];
  // 由於 HTML 已經有固定的標題和容器，我們直接往裡面添加圖片
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
      loadWardrobe();
    }
  } catch (err) {
    console.error("❌ 刪除錯誤", err);
  }
}

// 按鈕綁定
document.addEventListener('DOMContentLoaded', () => {
  console.log("DEBUG: DOMContentLoaded 事件觸發，開始綁定按鈕。");
  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);
  document.getElementById('all-button').addEventListener('click', () => loadWardrobe("all"));
  document.getElementById('top-button').addEventListener('click', () => loadWardrobe("top"));
  document.getElementById('bottom-button').addEventListener('click', () => loadWardrobe("bottom"));
  document.getElementById('skirt-button').addEventListener('click', () => loadWardrobe("skirt"));
  document.getElementById('dress-button').addEventListener('click', () => loadWardrobe("dress"));
  document.getElementById('shoes-button').addEventListener('click', () => loadWardrobe("shoes"));
  console.log("DEBUG: 按鈕綁定完成。");
});

// 只保留這一行作為 module export（讓 liff-init.js 能 import）
export { loadWardrobe };