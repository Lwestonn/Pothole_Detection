const videoEl = document.getElementById("video");
const resultEl = document.getElementById("result");
const statusEl = document.getElementById("status");

let sending = false;
let streamReady = false;

// Get camera from the phone
async function startCamera() {
  try {
    const constraints = {
      audio: false,
      video: {
        facingMode: { ideal: "environment" }, // back camera if available
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
    };

    const stream = await navigator.mediaDevices.getUserMedia(constraints);

    videoEl.srcObject = stream;
    await videoEl.play(); // <<< Safari fix

    streamReady = true;
    statusEl.textContent = "Status: Camera started, sending frames...";
    startSendingFrames();
  } catch (err) {
    console.error("Error starting camera:", err);
    statusEl.textContent = "Status: Failed to access camera. Check permissions.";
  }
}

if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    statusEl.textContent = "Status: getUserMedia NOT supported on this iPhone Safari.";
    return;
}


// Capture current frame as JPEG blob
function captureFrame(video, mimeType = "image/jpeg", quality = 0.7) {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  return new Promise((resolve) => {
    canvas.toBlob(
      (blob) => {
        resolve(blob);
      },
      mimeType,
      quality
    );
  });
}

// Loop that sends frames to the backend
async function sendFrameLoop() {
  if (!streamReady || !videoEl.srcObject) {
    return;
  }

  if (sending) {
    // Avoid overlapping requests
    requestAnimationFrame(sendFrameLoop);
    return;
  }

  try {
    sending = true;
    const frameBlob = await captureFrame(videoEl);

    const formData = new FormData();
    formData.append("file", frameBlob, "frame.jpg");

    const response = await fetch("/detect", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      console.error("Detect request failed:", response.status);
      statusEl.textContent = "Status: Error from server, check console.";
    } else {
      const imgBlob = await response.blob();
      const imgUrl = URL.createObjectURL(imgBlob);
      resultEl.src = imgUrl;
      statusEl.textContent = "Status: Running detection...";
    }
  } catch (err) {
    console.error("Error in sendFrameLoop:", err);
    statusEl.textContent = "Status: Error sending frame, see console.";
  } finally {
    sending = false;
    // Call again on next animation frame for live feel
    requestAnimationFrame(sendFrameLoop);
  }
}

function startSendingFrames() {
  requestAnimationFrame(sendFrameLoop);
}

window.addEventListener("load", () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    statusEl.textContent = "Status: getUserMedia not supported on this browser.";
    return;
  }
  startCamera();
});
