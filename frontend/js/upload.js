const backendURL = "https://liff-test-9xse.onrender.com";
let userId = "";
let currentCategory = "all";

window.onload = async function () {
  // 初始化 LINE LIFF
  await liff.init({ liffId: "2007733246-nAexA2b9" });
  if (!liff.isLoggedIn()) liff.login();
  const profile = await liff.getProfile();
  userId = profile.userId;
  document.getElementById("user-name").innerText = profile.displayName;
  document.getElementById("user-id").value = userId;
  document.getElementById("login-check").checked = true;
  loadWardrobe(userId);
};

document.getElementById("upload-button").onclick = uploadImages;
document.getElementById("delete-button").onclick = deleteSelected;
document.getElementById("category").onchange = function () {
  currentCategory = this.value;
};
document.getElementById("image-input").onchange = function () {
  // 可做預覽功能（如果需要即時本地預覽可以補這裡）
};

// 分類篩選
function filterCategory(cat) {
  currentCategory = cat;
  loadWardrobe(userId, cat);
}

// 載入衣櫃圖片（分類分區顯示）
async function loadWardrobe(uid, filter = "all") {
  const res = await fetch(`${backendURL}/wardrobe?user_id=${uid}`);
  const data = await res.json();
  const group = { top: [], bottom: [], skirt: [], dress: [], shoes: [] };
  (data.images || []).forEach(img => {
    if (group[img.category]) group[img.category].push(img);
  });
  displayImages(group, filter);
}

// 上傳多張
async function uploadImages() {
  const files = document.getElementById("image-input").files;
  const category = document.getElementById("category").value;
  if (!files.length) return alert("請選擇圖片");
  for (let file of files) {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("category", category);
    formData.append("user_id", userId);
    await fetch(`${backendURL}/upload`, { method: "POST", body: formData });
  }
  loadWardrobe(userId, currentCategory);
  document.getElementById("image-input").value = ""; // 清空選取
}

// 圖片顯示 & 分類
function displayImages(imagesByCategory, filter) {
  const container = document.getElementById("image-list");
  container.innerHTML = "";
  const showCats = (filter === "all")
    ? ["top", "bottom", "skirt", "dress", "shoes"]
    : [filter];
  const catName = {
    top: "上衣", bottom: "褲子", skirt: "裙子", dress: "洋裝", shoes: "鞋子"
  };

  showCats.forEach(cat => {
    const section = document.createElement("div");
    section.className = "category-section";
    const title = document.createElement("h3");
    title.innerText = catName[cat] || "";
    section.appendChild(title);

    const row = document.createElement("div");
    row.className = "image-row";
    (imagesByCategory[cat] || []).forEach(img => {
      const wrapper = document.createElement("div");
      wrapper.className = "image-item";
      const image = document.createElement("img");
      image.src = img.url;
      const caption = document.createElement("div");
      caption.className = "caption-text";
      caption.textContent = img.tags || "(描述生成中...)";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.dataset.url = img.url;
      wrapper.appendChild(image);
      wrapper.appendChild(caption);
      wrapper.appendChild(checkbox);
      row.appendChild(wrapper);
    });
    section.appendChild(row);
    container.appendChild(section);
  });
}

// 刪除
async function deleteSelected() {
  const selected = Array.from(document.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.dataset.url);
  if (!selected.length) return alert("請選擇要刪除的圖片");
  await fetch(`${backendURL}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, urls: selected })
  });
  loadWardrobe(userId, currentCategory);
}
