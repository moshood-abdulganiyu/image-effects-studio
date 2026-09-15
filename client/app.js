// Step 6 scope: get an image into the page and enable the 5 effect buttons.
// Step 7 will wire each button to POST /predict.

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const originalImage = document.getElementById("original-image");
const originalPlaceholder = document.getElementById("original-placeholder");
const effectButtons = document.querySelectorAll(".effect-button");

// Holds the currently uploaded file so step 7's fetch calls can read it
// without re-prompting the user. Exported on window for now since there's
// no bundler; step 7 can tidy this into a module if it grows.
window.currentImageFile = null;

function handleFile(file) {
  if (!file || !file.type.startsWith("image/")) {
    return;
  }

  window.currentImageFile = file;

  const reader = new FileReader();
  reader.onload = () => {
    originalImage.src = reader.result;
    originalImage.hidden = false;
    originalPlaceholder.hidden = true;
  };
  reader.readAsDataURL(file);

  effectButtons.forEach((button) => {
    button.disabled = false;
  });
}

// File picker
fileInput.addEventListener("change", (event) => {
  const file = event.target.files[0];
  handleFile(file);
});

// Drag and drop
dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("drop-zone--active");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("drop-zone--active");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("drop-zone--active");
  const file = event.dataTransfer.files[0];
  handleFile(file);
});
