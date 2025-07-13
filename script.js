// 初始化 LIFF
window.onload = function () {
  liff.init({ liffId: "2007733246-nAexA2b9" }).catch(err => alert("LIFF 初始化失敗"));
};

async function uploadImage() {
  const input = document.getElementById('imageInput');
  const file = input.files[0];
  if (!file) return alert("請選擇圖片");

  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch("https://你的後端網址/remove_bg", {
    method: "POST",
    body: formData
  });

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  document.getElementById("resultImg").src = url;
}
