class FacialRecognition {
  constructor(opts) {
    this.label = opts.label || "Authorize";
    this.cameraStream = null;
    this.selectedCamera = null;
    this.imageData = null;
    this.faceCaptured = false;
    this.Data = null;
    this.fpCode = "FACE";

    return new Promise((resolve, reject) => {
      this.facialPromiseResolve = resolve;
      this.facialPromiseReject = reject;
      this.init();
    });
  }

  async init() {
    this.showDialog();
    try {
      this.cameras = await this.loadCameras();
      this.updateDialog();
    } catch (err) {
      this.handleError(err, "init");
    }
  }

  handleError(error, context) {
    console.error(`Error in ${context}:`, error);
    if (this.dialog) {
      this.showCameraError(error);
    }
    this.facialPromiseReject(error);
  }

  showDialog() {
    this.dialog = new frappe.ui.Dialog({
      title: __("Patient Face Capture"),
      width: 150,
      fields: [{
        fieldname: 'face_capture_section',
        fieldtype: 'HTML',
        options: `
          <div class="face-capture-container">
            <div class="camera-selector">
              <select id="camera-select" class="form-control">
                <option value="">Loading cameras...</option>
              </select>
            </div>

            <div class="face-preview-area" id="face-preview-area">
              <div class="face-guide"></div>
              <video id="face-camera" autoplay playsinline></video>
              <canvas id="face-canvas" style="display:none;"></canvas>
            </div>

            <div class="capture-controls">
              <button id="capture-btn" class="btn btn-sm btn-capture">
                <i class="fa fa-camera"></i> ${__('Capture')}
              </button>
            </div>

            <div class="photo-preview-container" id="photo-preview-container" style="display:none;">
              <div class="photo-preview">
                <img id="face-preview" style="display:none;"/>
                <div class="preview-overlay">
                  <button id="zoom-preview-btn" class="btn btn-info btn-sm" style="display:none;">
                    <i class="fa fa-search-plus"></i> ${__('View Full Size')}
                  </button>
                </div>
              </div>
              <div class="retake-controls" style="margin-top: 15px;">
                <button id="retake-btn" class="btn btn-default">
                  <i class="fa fa-refresh"></i> ${__('Retake')}
                </button>
              </div>
            </div>
          </div>
        `
      }],
      size: 'large',
    });

    // Add custom styles
    $('<style>').html(`
      .face-capture-container {
        text-align: center;
        max-width: 500px;
        margin: 0 auto;
        padding: 15px;
      }

      .camera-selector {
        margin-bottom: 20px;
      }

      .face-preview-area {
        position: relative;
        width: 350px;
        height: 350px;
        margin: 15px auto;
        border-radius: 50%;
        overflow: hidden;
        border: 3px solid #dfe3e8;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        background-color: #f8f9fa;
      }

      .face-guide {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px dashed rgba(255,255,255,0.5);
        pointer-events: none;
        z-index: 10;
      }

      #face-camera, #face-preview {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .capture-controls {
        margin: 25px 0;
      }

      .btn-capture {
        background-color:rgb(42, 124, 161);
        color: white;
        border: none;
        font-size: 14px;
      }

      .btn-capture:hover {
        background-color:rgb(139, 206, 224);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
      }

      .btn-capture:active {
        transform: translateY(0);
      }

      .photo-preview-container {
        margin: 20px 0;
      }

      .photo-preview {
        position: relative;
        width: 350px;
        height: 350px;
        border-radius: 50%;
        overflow: hidden;
        margin: 0 auto;
        border: 3px solid #dfe3e8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        background-color: #f8f9fa;
      }

      .photo-preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        cursor: pointer;
      }

      .preview-overlay {
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 20;
      }

      .preview-overlay .btn {
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid #dfe3e8;
        color: #333;
        font-size: 12px;
        padding: 5px 10px;
      }

      .retake-controls {
        text-align: center;
      }

      .retake-controls .btn {
        padding: 8px 20px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 4px;
      }

      .zoom-mode {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.9);
        z-index: 1050;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
      }

      .zoom-mode img {
        max-width: 90%;
        max-height: 70%;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
      }

      .zoom-controls {
        margin-top: 30px;
        text-align: center;
      }

      .zoom-controls .btn {
        margin: 0 10px;
        min-width: 120px;
        padding: 10px 20px;
        font-size: 14px;
      }

      @media (max-width: 576px) {
        .face-preview-area, .photo-preview {
          width: 280px;
          height: 280px;
        }
        
        .btn-capture {
          padding: 8px 20px;
          font-size: 14px;
        }
      }
    `).appendTo('head');

    this.dialog.show();
    this.setupFaceCapture();
  }

  setupFaceCapture() {
    const $wrapper = this.dialog.$wrapper;
    const video = $wrapper.find('#face-camera')[0];
    const canvas = $wrapper.find('#face-canvas')[0];
    const photo = $wrapper.find('#face-preview')[0];
    const captureBtn = $wrapper.find('#capture-btn')[0];
    const retakeBtn = $wrapper.find('#retake-btn')[0];
    const zoomPreviewBtn = $wrapper.find('#zoom-preview-btn')[0];
    const cameraSelect = $wrapper.find('#camera-select')[0];
    const facePreviewArea = $wrapper.find('#face-preview-area')[0];
    const photoPreviewContainer = $wrapper.find('#photo-preview-container')[0];

    // Set initial button states
    retakeBtn.style.display = 'none';

    // Handle camera selection change
    cameraSelect.addEventListener('change', () => {
      this.startCamera(cameraSelect.value);
    });

    // Capture face photo
    captureBtn.onclick = () => {
      const size = Math.min(video.videoWidth, video.videoHeight);
      const x = (video.videoWidth - size) / 2;
      const y = (video.videoHeight - size) / 2;

      canvas.width = size;
      canvas.height = size;
      canvas.getContext('2d').drawImage(video, x, y, size, size, 0, 0, size, size);

      photo.src = canvas.toDataURL('image/jpeg', 0.9);
      this.Data = photo.src.split(',')[1];

      // Update UI
      facePreviewArea.style.display = 'none';
      photoPreviewContainer.style.display = 'block';
      photo.style.display = 'block';
      zoomPreviewBtn.style.display = 'inline-block';
      captureBtn.style.display = 'none';
      retakeBtn.style.display = 'inline-block';

      this.faceCaptured = true;
      this.dialog.enable_primary_action();
      this.set_primary_action(this.faceCaptured)
    //   this.dialog.set_primary_btn_label(__(this.label));
    };

    // Retake functionality
    retakeBtn.onclick = () => {
      photoPreviewContainer.style.display = 'none';
      facePreviewArea.style.display = 'block';
      photo.style.display = 'none';
      zoomPreviewBtn.style.display = 'none';
      captureBtn.style.display = 'inline-block';
      retakeBtn.style.display = 'none';

      this.faceCaptured = false;
      this.Data = null;
      this.dialog.disable_primary_action();
    };

    // Zoom preview
    zoomPreviewBtn.onclick = () => this.showZoomMode(photo.src);
    photo.onclick = () => this.faceCaptured && this.showZoomMode(photo.src);

    // Cleanup on dialog close
    this.dialog.$wrapper.on('hidden.bs.modal', () => this.stopCamera());
  }

  showZoomMode(imageSrc) {
    const $zoomMode = $(`
      <div class="zoom-mode">
        <img src="${imageSrc}" alt="Patient Face" />
        <div class="zoom-controls">
          <button class="btn btn-default zoom-close-btn">
            <i class="fa fa-times"></i> ${__('Close')}
          </button>
          <button class="btn btn-primary zoom-authorize-btn">
            <i class="fa fa-check"></i> ${__('Authorize')}
          </button>
        </div>
      </div>
    `).appendTo('body');

    $zoomMode.find('.zoom-close-btn').on('click', () => $zoomMode.remove());
    $zoomMode.find('.zoom-authorize-btn').on('click', () => {
      $zoomMode.remove();
      this.dialog.hide();
      this.facialPromiseResolve(this);
    });
    $zoomMode.on('click', (e) => e.target === $zoomMode[0] && $zoomMode.remove());
  }

  startCamera(deviceId) {
    this.stopCamera();
    const constraints = {
      video: {
        deviceId: deviceId ? { exact: deviceId } : undefined,
        width: { ideal: 720 },
        height: { ideal: 720 },
        facingMode: 'user'
      }
    };

    navigator.mediaDevices.getUserMedia(constraints)
      .then((stream) => {
        const video = this.dialog.$wrapper.find('#face-camera')[0];
        this.cameraStream = stream;
        video.srcObject = stream;

        video.onloadedmetadata = () => {
          const videoRatio = video.videoWidth / video.videoHeight;
          const containerRatio = 1;

          if (videoRatio > containerRatio) {
            const newWidth = video.videoHeight * containerRatio;
            video.style.width = 'auto';
            video.style.height = '100%';
            video.style.marginLeft = `-${(newWidth - video.videoWidth) / 2}px`;
          } else {
            const newHeight = video.videoWidth / containerRatio;
            video.style.width = '100%';
            video.style.height = 'auto';
            video.style.marginTop = `-${(newHeight - video.videoHeight) / 2}px`;
          }
        };
      })
      .catch((err) => this.showCameraError(err));
  }

  stopCamera() {
    if (this.cameraStream) {
      this.cameraStream.getTracks().forEach(track => track.stop());
      this.cameraStream = null;
    }
  }

  async loadCameras() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter(device => device.kind === 'videoinput');
    } catch (error) {
      console.error('Error loading cameras:', error);
      return [];
    }
  }

  updateDialog() {
    const $wrapper = this.dialog.$wrapper;
    const cameraSelect = $wrapper.find('#camera-select')[0];

    cameraSelect.innerHTML = this.cameras.length ? 
      this.cameras.map((device, index) => 
        `<option value="${device.deviceId}">${device.label || `Camera ${index + 1}`}</option>`
      ).join('') :
      '<option value="">No cameras found</option>';

    if (this.cameras.length > 0) {
      this.startCamera(this.cameras[0].deviceId);
    } else {
      this.showCameraError({ name: 'NotFoundError' });
    }
  }

  showCameraError(err) {
    let message = __('Could not access camera');
    if (err.name === 'NotAllowedError') message = __('Please allow camera access');
    if (err.name === 'NotFoundError') message = __('No camera found');

    this.dialog.fields_dict.face_capture_section.$wrapper.html(`
      <div class="alert alert-danger text-center" style="margin: 20px;">
        <i class="fa fa-camera" style="font-size: 24px;"></i><br><br>
        ${message}<br><br>
        <button class="btn btn-default" onclick="window.location.reload()">
          ${__('Try Again')}
        </button>
      </div>
    `);
  }

  destroy() {
    this.dialog.hide();
    this.stopCamera();
  }
  set_primary_action (faceCaptured) {
    let me = this
    this.dialog.set_primary_action(__(this.label), function () {
        if (faceCaptured) {
          me.facialPromiseResolve(me);
          me.destroy();
        } else {
          frappe.msgprint(__("Please capture a face photo first."));
          return;
        }
    });
  }
}

window.FacialRecognition = FacialRecognition;