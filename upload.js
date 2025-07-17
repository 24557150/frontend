let selectedFiles = [];
let images = [];
let idCounter = 0;
let currentFilter = 'all';

const fileInput = document.getElementById('file-input');
const status = document.getElementById('status');
const gallery = document.getElementById('closet-gallery');

// 本機選檔時處理
fileInput.addEventListener('change', () => {
  const files = Array.from(fileInput.files);
  if (files.length === 0) {
    status.innerText = '請選擇圖片';
    return;
  }
  selectedFiles = files;
  status.innerText = `已從本機選擇 ${files.length} 張圖片，請選擇分類並上傳`;
});

// LINE or 本機 選擇圖片
export async function openImageSourceSelector() {
  const choice = confirm("點選「確定」用 LINE 拍照/相簿，點選「取消」用本機選擇");
  if (choice) {
    try {
      const media = await liff.chooseMedia({
        count: 5,
        mediaType: ['image'],
        source: ['camera', 'gallery']
      });
      if (!media || media.length === 0) {
        status.innerText = '未選擇任何圖片';
        return;
      }
      selectedFiles = media.map((item, index) =>
        new File([item.blob], `image_${Date.now()}_${index}.jpg`, { type: item.mimeType })
      );
      status.innerText = `已從 LINE 選擇 ${selectedFiles.length} 張圖片，請選擇分類並上傳`;
    } catch (err) {
      console.error('選擇圖片錯誤:', err);
      status.innerText = '選擇圖片失敗';
    }
  } else {
    fileInput.click();
  }
}
window.openImageSourceSelector = openImageSourceSelector;

// 上傳圖片
async function uploadImages() {
  if (selectedFiles.length === 0) {
    alert('請先選擇圖片');
    return;
  }

  const category = document.getElementById('category-select').value;
  const userId = localStorage.getItem('user_id');

  if (!userId) {
    alert('尚未登入，請重新登入');
    return;
  }

  for (const file of selectedFiles) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('category', category);
    formData.append('user_id', userId);

    try {
      const res = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await res.json();
      if (result.status === 'ok') {
        const url = `http://localhost:5000/static/uploads/${userId}/${category}/${result.filename}`;
        images.push({ id: idCounter++, file, category, url, selected: false });
      } else {
        console.error('後端錯誤:', result.message);
      }
    } catch (err) {
      console.error('上傳失敗:', err);
    }
  }

  status.innerText = `✅ 已成功上傳 ${selectedFiles.length} 張圖片`;
  selectedFiles = [];
  fileInput.value = '';
  renderGallery();
}

// 分類過濾
function filterCategory(cat) {
  currentFilter = cat;
  renderGallery();
}

// 刪除圖片（僅前端預覽用）
function deleteSelected() {
  const checked = document.querySelectorAll('input[name="delete-checkbox"]:checked');
  if (checked.length === 0) {
    alert('請先選擇要刪除的圖片');
    return;
  }
  const paths = Array.from(checked).map(cb => cb.value);
  images = images.filter(img => !paths.includes(img.url));
  paths.forEach(path => URL.revokeObjectURL(path));
  status.innerText = '已刪除選取的圖片';
  renderGallery();
}

// 從後端載入已上傳圖片
export async function loadWardrobe(userId, category = 'all') {
  try {
    const res = await fetch(`http://localhost:5000/wardrobe?user_id=${userId}&category=${category}`);
    const data = await res.json();
    images = data.map(item => ({
      id: idCounter++,
      file: null,
      category: item.category,
      url: item.url,
      selected: false,
    }));
    renderGallery();
  } catch (err) {
    console.error('載入 wardrobe 失敗:', err);
  }
}

// 顯示圖片列表
function renderGallery() {
  gallery.innerHTML = '';
  const filtered = currentFilter === 'all' ? images : images.filter(img => img.category === currentFilter);
  if (filtered.length === 0) {
    gallery.innerHTML = '<p style="color:#666;">沒有符合條件的圖片</p>';
    return;
  }
  filtered.forEach(img => {
    const wrapper = document.createElement('div');
    wrapper.classList.add('image-wrapper');

    const imgEl = document.createElement('img');
    imgEl.src = img.url;
    imgEl.alt = img.file ? img.file.name : '';
    imgEl.title = `${img.category}`;

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.name = 'delete-checkbox';
    checkbox.value = img.url;

    wrapper.appendChild(imgEl);
    wrapper.appendChild(checkbox);
    gallery.appendChild(wrapper);
  });
}

// ✅ 綁定所有按鈕事件
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('upload-button')?.addEventListener('click', uploadImages);
  document.getElementById('delete-button')?.addEventListener('click', deleteSelected);
  document.getElementById('all-button')?.addEventListener('click', () => filterCategory('all'));
  document.getElementById('top-button')?.addEventListener('click', () => filterCategory('top'));
  document.getElementById('bottom-button')?.addEventListener('click', () => filterCategory('bottom'));
  document.getElementById('shoes-button')?.addEventListener('click', () => filterCategory('shoes'));
});
