export const backendURL = 'https://ai-outfit-1027775725754.asia-east1.run.app';

async function uploadImages() {
  const input = document.getElementById('image-input');
  const category = document.getElementById('category').value;
  const userId = window.userId;
  if (!userId || !category) return;

  const files = input.files;
  if (!files.length) return;

  for (const file of files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('user_id', userId);

    try {
      const res = await fetch(`${backendURL}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.status === 'ok') {
        loadWardrobe();
      }
    } catch (err) {
      console.error('❌ 上傳錯誤:', err);
    }
  }
}

async function loadWardrobe(category = "all") {
  const userId = window.userId;
  if (!userId) return;

  try {
    const url = `${backendURL}/wardrobe?user_id=${userId}&category=${category}`;
    const res = await fetch(url);
    const data = await res.json();
    displayImages(data.images);
  } catch (err) {
    console.error("❌ 載入衣櫃失敗", err);
  }
}

function displayImages(images) {
  const imageList = document.getElementById("image-list");
  imageList.innerHTML = "";

  const categories = ["top", "bottom", "skirt", "dress", "shoes"];
  const categoryTitles = {
    "top": "上衣",
    "bottom": "褲子",
    "skirt": "裙子",
    "dress": "洋裝",
    "shoes": "鞋子"
  };

  categories.forEach(cat => {
    const title = document.createElement("div");
    title.textContent = categoryTitles[cat] || cat;
    title.style.fontWeight = "bold";
    title.style.fontSize = "1.3em";
    title.style.margin = "30px 0 10px 0";
    imageList.appendChild(title);

    const row = document.createElement("div");
    row.style.overflowX = "auto";
    row.style.whiteSpace = "nowrap";
    imageList.appendChild(row);

    images.filter(img => img.category === cat).forEach(img => {
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
      row.appendChild(wrapper);
    });
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
  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);
  document.getElementById('all-button').addEventListener('click', () => loadWardrobe("all"));
  document.getElementById('top-button').addEventListener('click', () => loadWardrobe("top"));
  document.getElementById('bottom-button').addEventListener('click', () => loadWardrobe("bottom"));
  document.getElementById('skirt-button').addEventListener('click', () => loadWardrobe("skirt"));
  document.getElementById('dress-button').addEventListener('click', () => loadWardrobe("dress"));
  document.getElementById('shoes-button').addEventListener('click', () => loadWardrobe("shoes"));
});

// 只保留這一行作為 module export（讓 liff-init.js 能 import）
export { loadWardrobe };
