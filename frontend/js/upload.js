// frontend/js/upload.js
export const backendURL = 'https://liff-test-9xse.onrender.com'; // 改成 ngrok 提供的最新 URL

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);

  ['all', 'top', 'bottom', 'skirt', 'dress', 'shoes'].forEach(cat => {
    document.getElementById(`${cat}-button`).addEventListener('click', () => filterCategory(cat));
  });

  const userId = localStorage.getItem('user_id');
  if (userId) loadWardrobe(userId);
});

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
      await fetch(`${backendURL}/upload`, {
        method: 'POST',
        body: formData,
        headers: { 'ngrok-skip-browser-warning': 'any' },
        credentials: 'include'
      });
    } catch (err) {
      alert("⚠️ 後端連線失敗，請檢查 ngrok 是否啟動");
      console.error('❌ 上傳錯誤:', err);
    }
  }
  await loadWardrobe(userId);
  input.value = '';
}

export async function loadWardrobe(userId) {
  try {
    const res = await fetch(`${backendURL}/wardrobe?user_id=${userId}`, {
      headers: { 'ngrok-skip-browser-warning': 'any' },
      credentials: 'include'
    });
    const data = await res.json();
    displayImages(data.images);
  } catch (err) {
    alert("⚠️ 無法連接後端，請檢查 ngrok 是否運行");
    console.error("❌ 載入衣櫃失敗", err);
  }
}

function displayImages(images) {
  const categories = ['top', 'bottom', 'skirt', 'dress', 'shoes'];
  categories.forEach(cat => {
    document.getElementById(`${cat}-container`).innerHTML = "";
  });

  images.forEach(img => {
    const fullPath = `${backendURL}${img.path}`; // 正確的完整 URL (不會多 static)

    const container = document.getElementById(`${img.category}-container`);
    if (!container) return;

    const wrapper = document.createElement("div");
    wrapper.className = `image-item ${img.category}`;
    wrapper.style.display = "inline-block";
    wrapper.style.margin = "5px";
    wrapper.style.textAlign = "center";

    const imgElement = document.createElement("img");
    imgElement.src = fullPath;
    imgElement.style.width = "100px";
    imgElement.style.borderRadius = "8px";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.path = img.path;  // 使用相對路徑，刪除時直接比對
    checkbox.style.marginTop = "5px";

    wrapper.appendChild(imgElement);
    wrapper.appendChild(checkbox);
    container.appendChild(wrapper);
  });
}

function filterCategory(category) {
  const allSections = document.querySelectorAll('.category-section');
  allSections.forEach(sec => {
    sec.style.display = (category === 'all' || sec.id.startsWith(category)) ? 'block' : 'none';
  });
}

async function deleteSelected() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
  const paths = Array.from(checkboxes).map(cb => cb.dataset.path);
  const userId = localStorage.getItem('user_id');

  if (!paths.length) return alert('請選擇要刪除的圖片');

  try {
    await fetch(`${backendURL}/delete`, {
      method: 'POST',
      headers: {
        'ngrok-skip-browser-warning': 'any',
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({ user_id: userId, paths })
    });
    await loadWardrobe(userId);
  } catch (err) {
    alert("⚠️ 無法連接後端");
    console.error("❌ 刪除錯誤:", err);
  }
}
