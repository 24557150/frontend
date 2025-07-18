export const backendURL = 'https://03f969b6c0f7.ngrok-free.app';

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);
  document.getElementById('all-button').addEventListener('click', () => filterCategory('all'));
  document.getElementById('top-button').addEventListener('click', () => filterCategory('top'));
  document.getElementById('bottom-button').addEventListener('click', () => filterCategory('bottom'));
  document.getElementById('shoes-button').addEventListener('click', () => filterCategory('shoes'));

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
      const res = await fetch(`${backendURL}/upload`, {
        method: 'POST',
        body: formData,
        headers: { 'ngrok-skip-browser-warning': 'any' },
        credentials: 'include'
      });
      const json = await res.json();
      if (!res.ok || json.status !== "ok") console.error(`❌ 上傳失敗: ${file.name}`, json);
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
    const text = await res.text();
    try {
      const data = JSON.parse(text);
      displayImages(data.images);
    } catch (e) {
      alert("⚠️ 後端回應錯誤，請確認 ngrok URL 是否正確啟動");
      console.error("❌ API 回應非 JSON:", text);
    }
  } catch (err) {
    alert("⚠️ 無法連接後端，請檢查 ngrok 是否運行");
    console.error("❌ 載入衣櫃失敗", err);
  }
}

function displayImages(images) {
  const imageList = document.getElementById("image-list");
  imageList.innerHTML = "";

  images.forEach(img => {
    const fullPath = `${backendURL}${img.path}`;

    const wrapper = document.createElement("div");
    wrapper.className = `image-item ${img.category}`;
    wrapper.style.display = "inline-block";
    wrapper.style.margin = "10px";
    wrapper.style.textAlign = "center";

    const imgElement = document.createElement("img");
    imgElement.src = fullPath;
    imgElement.style.width = "100px";
    imgElement.style.borderRadius = "8px";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.path = fullPath;
    checkbox.style.marginTop = "5px";

    wrapper.appendChild(imgElement);
    wrapper.appendChild(checkbox);
    imageList.appendChild(wrapper);
  });
}

function filterCategory(category) {
  const allImages = document.querySelectorAll('.image-item');
  allImages.forEach(img => {
    img.style.display = (category === 'all' || img.classList.contains(category)) ? 'inline-block' : 'none';
  });
}

async function deleteSelected() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
  const paths = Array.from(checkboxes).map(cb => cb.dataset.path);
  const userId = localStorage.getItem('user_id');

  if (!paths.length) return alert('請選擇要刪除的圖片');

  try {
    const res = await fetch(`${backendURL}/delete`, {
      method: 'POST',
      headers: {
        'ngrok-skip-browser-warning': 'any',
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({ user_id: userId, paths })
    });
    const json = await res.json();
    if (res.ok && json.status === "ok") {
      await loadWardrobe(userId);
    } else {
      console.error("❌ 刪除失敗:", json);
    }
  } catch (err) {
    alert("⚠️ 無法連接後端，請檢查 ngrok 是否運行");
    console.error("❌ 刪除錯誤:", err);
  }
}
