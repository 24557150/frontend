const backendURL = "https://liff-test-9xse.onrender.com";

document.addEventListener('DOMContentLoaded', () => {
  const uploadBtn = document.getElementById('upload-button');
  const deleteBtn = document.getElementById('delete-button');

  if (uploadBtn) uploadBtn.addEventListener('click', uploadImages);
  if (deleteBtn) deleteBtn.addEventListener('click', deleteSelected);

  const userId = localStorage.getItem('user_id') || 'guest';
  loadWardrobe(userId);
});

async function uploadImages() {
  const files = document.getElementById('image-input').files;
  const category = document.getElementById('category').value;
  const userId = localStorage.getItem('user_id') || 'guest';
  if (!files.length) return alert("請選擇圖片");

  for (let file of files) {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("category", category);
    formData.append("user_id", userId);

    await fetch(`${backendURL}/upload`, {
      method: "POST",
      body: formData
    });
  }
  loadWardrobe(userId);
}

async function loadWardrobe(userId) {
  const res = await fetch(`${backendURL}/wardrobe?user_id=${userId}`);
  const data = await res.json();
  displayImages(data.images);
}

function displayImages(images) {
  const container = document.getElementById("image-list");
  container.innerHTML = "";

  images.forEach(img => {
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
    container.appendChild(wrapper);
  });
}

async function deleteSelected() {
  const userId = localStorage.getItem('user_id') || 'guest';
  const selected = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
                        .map(cb => cb.dataset.url);
  if (!selected.length) return alert("請選擇要刪除的圖片");

  await fetch(`${backendURL}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, urls: selected })
  });

  loadWardrobe(userId);
}
