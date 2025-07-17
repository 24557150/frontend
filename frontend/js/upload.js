let selectedFiles = [];
let images = [];
let idCounter = 0;
let currentFilter = 'all';

const fileInput = document.getElementById('file-input');
const status = document.getElementById('status');
const gallery = document.getElementById('closet-gallery');

fileInput.addEventListener('change', () => {
  const files = Array.from(fileInput.files);
  if (files.length === 0) {
    status.innerText = '請選擇圖片';
    return;
  }
  selectedFiles = files;
  status.innerText = `已從本機選擇 ${files.length} 張圖片，請選擇分類並上傳`;
});

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

window.uploadImages = function () {
  if (selectedFiles.length === 0) {
    alert('請先選擇圖片');
    return;
  }
  const category = document.getElementById('category-select').value;
  selectedFiles.forEach(file => {
    const url = URL.createObjectURL(file);
    images.push({ id: idCounter++, file, category, url, selected: false });
  });
  status.innerText = `已新增 ${selectedFiles.length} 張圖片到分類「${category}」`;
  fileInput.value = '';
  renderGallery();
};

window.filterCategory = function (cat) {
  currentFilter = cat;
  renderGallery();
};

window.deleteSelected = function () {
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
};

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
    imgEl.alt = img.file.name;
    imgEl.title = `${img.file.name} (${img.category})`;

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.name = 'delete-checkbox';
    checkbox.value = img.url;

    wrapper.appendChild(imgEl);
    wrapper.appendChild(checkbox);
    gallery.appendChild(wrapper);
  });
}
