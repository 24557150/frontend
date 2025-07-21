const backendURL = "https://liff-test-9xse.onrender.com";

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('upload-button').addEventListener('click', uploadImages);
  loadWardrobe();
});

async function uploadImages() {
  const files = document.getElementById('image-input').files;
  const category = document.getElementById('category').value;
  const userId = "Uxxxxxxxx"; // 測試用，實際用 LIFF
  if (!files.length) return alert("請選擇圖片");
  for (let file of files) {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("category", category);
    formData.append("user_id", userId);
    const res = await fetch(backendURL + "/upload", { method: "POST", body: formData });
    const data = await res.json();
    console.log("上傳結果", data);
  }
  loadWardrobe();
}

async function loadWardrobe() {
  const userId = "Uxxxxxxxx"; // 測試用
  const res = await fetch(`${backendURL}/wardrobe?user_id=${userId}`);
  const data = await res.json();
  const container = document.getElementById("image-list");
  container.innerHTML = "";
  data.images.forEach(img => {
    const div = document.createElement("div");
    div.className = "image-item";
    const image = document.createElement("img");
    image.src = backendURL + img.path;
    const caption = document.createElement("div");
    caption.className = "caption";
    caption.innerText = img.tags || "（無描述）";
    div.appendChild(image);
    div.appendChild(caption);
    container.appendChild(div);
  });
}
