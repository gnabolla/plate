let currentTab = 'upload';
let selectedFile = null;
let capturedImageData = null;
let stream = null;

// Elements
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const previewImage = document.getElementById('previewImage');
const cameraVideo = document.getElementById('cameraVideo');
const cameraCanvas = document.getElementById('cameraCanvas');
const capturedImage = document.getElementById('capturedImage');
const startCameraBtn = document.getElementById('startCameraBtn');
const captureBtn = document.getElementById('captureBtn');
const retakeBtn = document.getElementById('retakeBtn');
const manualInput = document.getElementById('manualInput');
const detectBtn = document.getElementById('detectBtn');
const results = document.getElementById('results');
const resultsContent = document.getElementById('resultsContent');
const loading = document.getElementById('loading');

// Tab switching
function switchTab(tab) {
    currentTab = tab;
    
    // Update tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tab}-tab`).classList.add('active');
    
    // Stop camera when switching away
    if (tab !== 'camera' && stream) {
        stopCamera();
    }
    
    // Hide results
    results.classList.add('hidden');
}

// File upload
uploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImage.classList.remove('hidden');
            uploadArea.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewImage.classList.remove('hidden');
            uploadArea.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
});

// Camera
startCameraBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
        });
        cameraVideo.srcObject = stream;
        startCameraBtn.classList.add('hidden');
        captureBtn.classList.remove('hidden');
    } catch (err) {
        alert('Unable to access camera. Please ensure you have granted camera permissions.');
    }
});

captureBtn.addEventListener('click', () => {
    const context = cameraCanvas.getContext('2d');
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    context.drawImage(cameraVideo, 0, 0);
    
    capturedImageData = cameraCanvas.toDataURL('image/jpeg');
    capturedImage.src = capturedImageData;
    capturedImage.classList.remove('hidden');
    
    cameraVideo.style.display = 'none';
    captureBtn.classList.add('hidden');
    retakeBtn.classList.remove('hidden');
    
    stopCamera();
});

retakeBtn.addEventListener('click', () => {
    capturedImage.classList.add('hidden');
    cameraVideo.style.display = 'block';
    retakeBtn.classList.add('hidden');
    startCameraBtn.classList.remove('hidden');
    capturedImageData = null;
});

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

// Detection
detectBtn.addEventListener('click', async () => {
    const formData = new FormData();
    let hasInput = false;
    
    if (currentTab === 'upload' && selectedFile) {
        formData.append('file', selectedFile);
        hasInput = true;
    } else if (currentTab === 'camera' && capturedImageData) {
        formData.append('image_data', capturedImageData);
        hasInput = true;
    } else if (currentTab === 'manual' && manualInput.value.trim()) {
        formData.append('manual_plate', manualInput.value.trim());
        hasInput = true;
    }
    
    if (!hasInput) {
        alert('Please provide an image or enter a license plate number.');
        return;
    }
    
    loading.classList.remove('hidden');
    detectBtn.disabled = true;
    
    try {
        const response = await fetch('/plate/detect', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        displayResults(data);
    } catch (err) {
        alert('Error processing request. Please try again.');
    } finally {
        loading.classList.add('hidden');
        detectBtn.disabled = false;
    }
});

function displayResults(data) {
    results.classList.remove('hidden');
    resultsContent.innerHTML = '';
    
    if (!data.success) {
        resultsContent.innerHTML = `<div class="error">${data.error}</div>`;
        return;
    }
    
    if (data.plates && data.plates.length > 0) {
        resultsContent.innerHTML = `<p class="source">Source: ${data.source}</p>`;
        
        data.plates.forEach(plate => {
            const plateDiv = document.createElement('div');
            plateDiv.className = 'plate-result';
            
            let vehicleInfo = '';
            if (plate.vehicle_info) {
                const info = plate.vehicle_info;
                vehicleInfo = `
                    <div class="vehicle-info">
                        <div class="vehicle-details">
                            <strong>Vehicle:</strong> ${info.year || ''} ${info.make || ''} ${info.model || ''} ${info.color || ''}
                            <span class="status-badge ${info.status}">${info.status}</span>
                        </div>
                        <div class="owner-details">
                            <strong>Owner:</strong> ${info.owner.name}
                            ${info.owner.email ? `<br>Email: ${info.owner.email}` : ''}
                            ${info.owner.phone ? `<br>Phone: ${info.owner.phone}` : ''}
                            ${info.owner.city && info.owner.state ? `<br>Location: ${info.owner.city}, ${info.owner.state}` : ''}
                        </div>
                    </div>
                `;
            }
            
            plateDiv.innerHTML = `
                <div class="plate-header">
                    <div class="plate-number">${plate.text}</div>
                    <div class="confidence">Confidence: ${plate.confidence}%</div>
                </div>
                ${vehicleInfo}
            `;
            resultsContent.appendChild(plateDiv);
        });
    } else {
        resultsContent.innerHTML = '<p class="no-results">No license plates detected</p>';
    }
}

// Reset button
document.getElementById('resetBtn').addEventListener('click', () => {
    // Hide results
    results.classList.add('hidden');
    
    // Reset upload tab
    previewImage.classList.add('hidden');
    uploadArea.style.display = 'block';
    selectedFile = null;
    fileInput.value = '';
    
    // Reset camera tab
    capturedImage.classList.add('hidden');
    cameraVideo.style.display = 'block';
    retakeBtn.classList.add('hidden');
    startCameraBtn.classList.remove('hidden');
    capturedImageData = null;
    
    // Reset manual input
    manualInput.value = '';
    
    // Stop camera if running
    stopCamera();
});

// Cleanup
window.addEventListener('beforeunload', () => {
    stopCamera();
});