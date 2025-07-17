document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('upload-button').addEventListener('click', uploadImages);
  document.getElementById('delete-button').addEventListener('click', deleteSelected);
  document.getElementById('all-button').addEventListener('click', () => filterCategory('all'));
  document.getElementById('top-button').addEventListener('click', () => filterCategory('top'));
  document.getElementById('bottom-button').addEventListener('click', () => filterCategory('bottom'));
  document.getElementById('shoes-button').addEventListener('click', () => filterCategory('shoes'));
});