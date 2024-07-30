// static/script.js

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');
const resultElement = document.getElementById('result');

document.getElementById('start-camera').addEventListener('click', startCamera);
document.getElementById('capture').addEventListener('click', captureImage);

function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.play();
            requestAnimationFrame(scanQRCode);
        })
        .catch(err => {
            console.error("Error accessing the camera: ", err);
        });
}

function scanQRCode() {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, canvas.width, canvas.height);

    if (code) {
        resultElement.textContent = `QR Code URL: ${code.data}`;
        // Redirect to the QR code link
        window.location.href = code.data;
    } else {
        requestAnimationFrame(scanQRCode);
    }
}

function captureImage() {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
}