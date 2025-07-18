// frontend/js/upload.js

export const backendURL = 'https://7d3e145bb3d0.ngrok-free.app';

document.addEventListener('DOMContentLoaded', () => {
  localStorage.setItem('user_id', 'demo_user'); // 測試帳號

  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);
  document.getElementById('all-button').addEventListener('click', () => filterCategory('all'));
  document.getElementById('top-button').addEventListener('click', () => filterCategory('top'));
  document.getElementById('bottom-button').addEventListener('click', () => filterCategory('bottom'));
  document.getElementById('shoes-button').addEventListener('click', () => filterCategory('shoes'));

  const userId = localStorage.getItem('user_id');
  if (userId) loadWardrobe(userId);
});

// 上傳圖片到後端
async function uploadImages() {
  const input = document.getElementById('image-input');
  const category = document.getElementById('category').value;
  const userId = localStorage.getItem('user_id');

  if (!input.files.length || !category || !userId) {
    alert('請選擇圖片與分類，並確認已登入');
    return;
  }

  for (const file of input.files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('user_id', userId);

    try {
      const res = await fetch(`${backendURL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        console.log(`✅ 上傳成功: ${file.name}`);
      } else {
        console.error(`❌ 上傳失敗: ${file.name}`);
      }
    } catch (err) {
      console.error('❌ 上傳錯誤:', err);
    }
  }

  await loadWardrobe(userId);
  input.value = '';
}

// 載入使用者衣櫃
export async function loadWardrobe(userId) {
  try {
    const res = await fetch(`${backendURL}/wardrobe?user_id=${userId}`);
    const data = await res.json();
    console.log("✅ 從後端取得圖片資料：", data);
    displayImages(data.images);
  } catch (err) {
    console.error("❌ 載入衣櫃失敗", err);
  }
}

// 顯示圖片與 checkbox
function displayImages(images) {
  const imageList = document.getElementById("image-list");
  imageList.innerHTML = "";

  images.forEach(img => {
    const fullPath = `${backendURL}${img.path}`;
    const category = img.category || 'unknown';

    // 外層容器
    const wrapper = document.createElement("div");
    wrapper.className = `image-item ${category}`;
    wrapper.style.display = "inline-block";
    wrapper.style.margin = "10px";
    wrapper.style.textAlign = "center";

    // 圖片
    const imgElement = document.createElement("img");
    imgElement.src = fullPath;
    imgElement.style.width = "150px";
    imgElement.style.borderRadius = "8px";

    // 勾選框
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.path = img.path;
    checkbox.style.marginTop = "5px";

    wrapper.appendChild(imgElement);
    wrapper.appendChild(checkbox);
    imageList.appendChild(wrapper);
  });
}

// 篩選分類
function filterCategory(category) {
  const allImages = document.querySelectorAll('.image-item');
  allImages.forEach(img => {
    img.style.display = (category === 'all' || img.classList.contains(category)) ? 'inline-block' : 'none';
  });
}

// 刪除勾選的圖片
async function deleteSelected() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
  const paths = Array.from(checkboxes).map(cb => cb.dataset.path);
  const userId = localStorage.getItem('user_id');

  if (!paths.length) return alert('請選擇要刪除的圖片');

  try {
    const res = await fetch(`${backendURL}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, paths }),
    });

    if (res.ok) {
      console.log("✅ 已刪除圖片");
      await loadWardrobe(userId);
    } else {
      console.error("❌ 刪除失敗");
    }
  } catch (err) {
    console.error("❌ 刪除錯誤:", err);
  }
}
