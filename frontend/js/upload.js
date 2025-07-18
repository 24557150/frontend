// frontend/js/upload.js

export const backendURL = 'https://7d3e145bb3d0.ngrok-free.app';

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);
  document.getElementById('all-button').addEventListener('click', () => filterCategory('all'));
  document.getElementById('top-button').addEventListener('click', () => filterCategory('top'));
  document.getElementById('bottom-button').addEventListener('click', () => filterCategory('bottom'));
  document.getElementById('shoes-button').addEventListener('click', () => filterCategory('shoes'));
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

  await loadWardrobe(userId); // 重新載入衣櫃
  input.value = ''; // 清空選取的檔案
}

// 載入使用者衣櫃
export async function loadWardrobe(userId) {
  try {
    const res = await fetch(`${backendURL}/wardrobe?user_id=${userId}`);
    const data = await res.json();

    console.log("✅ 從後端取得圖片資料：", data); // 除錯：顯示回傳資料
    displayImages(data.images);
  } catch (err) {
    console.error("❌ 載入衣櫃失敗", err);
  }
}

// 顯示圖片
function displayImages(images) {
  const container = document.getElementById('image-list');
  container.innerHTML = '';

  console.log("📷 準備顯示圖片", images); // 除錯：顯示即將渲染的圖片資料

  images.forEach(img => {
    const div = document.createElement('div');
    div.className = `image-item ${img.category}`;
    div.innerHTML = `
      <img src="${backendURL}/${img.path}" alt="${img.category}" width="100">
      <input type="checkbox" data-path="${img.path}">
    `;
    container.appendChild(div);
  });
}

// 篩選分類
function filterCategory(category) {
  const allImages = document.querySelectorAll('.image-item');
  allImages.forEach(img => {
    img.style.display = (category === 'all' || img.classList.contains(category)) ? 'block' : 'none';
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
