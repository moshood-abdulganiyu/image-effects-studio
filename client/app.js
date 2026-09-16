
const API_BASE_URL = "http://localhost:8000";

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

// --- Step 7: per-box predict wiring ---
// Each box is independent: its own button, its own fetch, its own result
// and download link. Clicking one never touches another box's state, and
// a slow effect (oil painting) never blocks the others from finishing.

async function runEffect(box) {
  const effect = box.dataset.effect;
  const button = box.querySelector(".effect-button");
  const resultImage = box.querySelector(".effect-result");
  const placeholder = box.querySelector(".placeholder-text");
  const downloadLink = box.querySelector(".download-link");

  if (!window.currentImageFile) {
    return;
  }

  const originalLabel = button.textContent;
  const originalPlaceholderText = placeholder.dataset.defaultText || placeholder.textContent;
  placeholder.dataset.defaultText = originalPlaceholderText;

  button.disabled = true;
  button.textContent = "Developing...";
  downloadLink.hidden = true;

  const formData = new FormData();
  formData.append("image", window.currentImageFile);
  formData.append("effect", effect);

  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      const detail = errorBody && errorBody.detail ? errorBody.detail : response.statusText;
      throw new Error(detail);
    }

    const data = await response.json();
    const dataUrl = `data:image/${data.format};base64,${data.image_base64}`;

    // Restart the develop-in animation even on a re-click of the same
    // box: drop the class, force a reflow, then re-add it.
    resultImage.classList.remove("develop-in");
    void resultImage.offsetWidth;
    resultImage.src = dataUrl;
    resultImage.hidden = false;
    resultImage.classList.add("develop-in");
    placeholder.textContent = originalPlaceholderText;
    placeholder.hidden = true;

    downloadLink.href = dataUrl;
    downloadLink.download = `${effect}-result.${data.format}`;
    downloadLink.hidden = false;
  } catch (error) {
    // Box-scoped failure: this box shows the error, the other 4 boxes
    // are untouched and remain clickable.
    placeholder.textContent = `Failed: ${error.message}`;
    placeholder.hidden = false;
    resultImage.hidden = true;
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

document.querySelectorAll(".effect-box").forEach((box) => {
  const button = box.querySelector(".effect-button");
  button.addEventListener("click", () => runEffect(box));
});