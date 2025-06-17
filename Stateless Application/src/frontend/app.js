const form = document.getElementById('upload-form');
const statusDiv = document.getElementById('status');
const outputDiv = document.getElementById('output');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusDiv.textContent = '';
  outputDiv.innerHTML = '';

  const fileInput = document.getElementById('image-file');
  const operationSelect = document.getElementById('operation');

  if (fileInput.files.length === 0) {
    statusDiv.textContent = 'Please select an image file.';
    return;
  }

  const file = fileInput.files[0];
  const operation = operationSelect.value;
  const formData = new FormData();
  formData.append('file', file);

  statusDiv.textContent = 'Uploading and processing...';

  try {
    const backendUrl = `/upload?operation=${encodeURIComponent(operation)}`;

    const response = await fetch(backendUrl, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    const blob = await response.blob();
    const imageUrl = URL.createObjectURL(blob);

    statusDiv.textContent = 'Image processed successfully!';
    outputDiv.innerHTML = `<img src="${imageUrl}" alt="Processed Image" />`;
  } catch (error) {
    statusDiv.textContent = `Error: ${error.message}`;
  }
});
