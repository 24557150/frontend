const backendURL = "https://liff-test-9xse.onrender.com";

async function fetchWardrobe(category="all") {
  const userId = localStorage.getItem("userId") || "guest";
  const res = await fetch(`${backendURL}/wardrobe?user_id=${userId}&category=${category}`);
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
    image.src = backendURL + img.path;
    const caption = document.createElement("div");
    caption.className = "caption-text";
    caption.textContent = img.tags || "";
    wrapper.appendChild(image);
    wrapper.appendChild(caption);
    container.appendChild(wrapper);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fetchWardrobe("all");
});
