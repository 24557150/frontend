const backendURL = "https://你的-render-backend-url";  // 請改成 Render 的後端網址
let userId = "";

// LIFF 自動登入（假設已經初始化過）
document.addEventListener('DOMContentLoaded', () => {
  // 這裡替換為你的 LIFF 登入流程，並取得 userId
  userId = "測試用戶"; // 假資料，實際請從 LIFF 拿 userId
  document.getElementById('user-name').innerText = userId;

  loadWardrobe();

  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);

  document.getElementById('all-button').addEventListener('click', () => loadWardrobe("all"));
  document.getElementById('top-button').addEventListener('click', () => loadWardrobe("top"));
  document.getElementById('bottom-button').addEventListener('click', () => loadWardrobe("pants"));
  document.getElementById('skirt-button').addEventListener('click', () => loadWardrobe("skirt"));
  document.getElementById('dress-button').addEventListener('click', () => loadWardrobe("dress"));
  document.getElementById('shoes-button').addEventListener('click', () => loadWardrobe("shoes"));
});

function openImageSourceSelector() {
  document.getElementById('image-input').click();
}

function uploadImages() {
  const files = document.getElementById('image-input').files;
  const category = document.getElementById('category').value;
  if (!files.length) {
    alert("請選擇圖片");
    return;
  }
  for (let file of files) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('user_id', userId);

    fetch(`${backendURL}/upload`, {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "ok") {
        loadWardrobe();
      } else {
        alert("上傳失敗");
      }
    })
    .catch(err => console.error("上傳錯誤:", err));
  }
}

function loadWardrobe(category = "all") {
  fetch(`${backendURL}/wardrobe?user_id=${userId}&category=${category}`)
    .then(res => res.json())
    .then(data => displayImages(data.images))
    .catch(err => console.error("載入錯誤:", err));
}

function displayImages(images) {
  const imageList = document.getElementById("image-list");
  imageList.innerHTML = "";

  images.forEach(img => {
    const fullPath = `${backendURL}${img.path}`;
    const wrapper = document.createElement("div");
    wrapper.className = `image-item ${img.category}`;

    const imgElement = document.createElement("img");
    imgElement.src = fullPath;

    const caption = document.createElement("div");
    caption.className = "caption-text";
    caption.innerText = img.tags || "(無描述)";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.path = fullPath;

    wrapper.appendChild(imgElement);
    wrapper.appendChild(caption);
    wrapper.appendChild(checkbox);
    imageList.appendChild(wrapper);
  });
}

function deleteSelected() {
  const selected = [...document.querySelectorAll("#image-list input:checked")];
  if (!selected.length) return;
  const paths = selected.map(cb => cb.dataset.path.replace(backendURL, ""));
  fetch(`${backendURL}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, paths })
  })
  .then(res => res.json())
  .then(() => loadWardrobe())
  .catch(err => console.error("刪除錯誤:", err));
}
