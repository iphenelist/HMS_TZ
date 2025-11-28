/**
 * Signature Pad Class for HMS TZ
 * A reusable signature capture component that can be used across the application.
 * 
 * Usage:
 *   const signature = await new Signature({ label: "Sign Document" });
 *   if (signature) {
 *     console.log(signature.Data); // Base64 PNG image data
 *   }
 */

export class Signature {
  constructor(opts = {}) {
    this.label = opts.label || "Sign";
    this.title = opts.title || __("Draw Signature");
    this.canvasWidth = opts.width || 500;
    this.canvasHeight = opts.height || 250;
    this.lineColor = opts.lineColor || "#000";
    this.lineWidth = opts.lineWidth || 3;
    this.backgroundColor = opts.backgroundColor || "#fff";
    
    // Canvas state
    this.canvas = null;
    this.ctx = null;
    this.isDrawing = false;
    this.lastX = 0;
    this.lastY = 0;
    this.hasDrawn = false;

    return new Promise((resolve, reject) => {
      this.signaturePromiseResolve = resolve;
      this.signaturePromiseReject = reject;
      this.init();
    });
  }

  init() {
    this.showDialog();
  }

  showDialog() {
    this.dialog = new frappe.ui.Dialog({
      title: this.title,
      fields: [
        {
          fieldtype: "HTML",
          fieldname: "signature_container",
          options: this.getSignatureHTML(),
        },
      ],
      size: "large",
      primary_action_label: __(this.label),
      primary_action: () => this.submitSignature(),
      secondary_action_label: __("Cancel"),
      secondary_action: () => this.cancel(),
    });

    this.dialog.show();

    // Initialize canvas after dialog is rendered
    this.dialog.$wrapper.on("shown.bs.modal", () => {
      this.initCanvas();
    });

    // Fallback initialization with setTimeout
    setTimeout(() => {
      if (!this.canvas) {
        this.initCanvas();
      }
    }, 200);
  }

  getSignatureHTML() {
    return `
      <div class="signature-pad-container" style="text-align: center; padding: 10px;">
        <p style="margin-bottom: 15px; color: #666;">
          ${__("Please draw your signature below using a pen, stylus, or mouse")}
        </p>
        <div class="signature-canvas-wrapper" style="
          border: 2px solid #ccc; 
          border-radius: 10px; 
          background-color: ${this.backgroundColor}; 
          margin: 0 auto; 
          display: inline-block;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
          <canvas 
            id="hms-signature-canvas" 
            width="${this.canvasWidth}" 
            height="${this.canvasHeight}" 
            style="
              cursor: crosshair; 
              touch-action: none;
              display: block;
              border-radius: 8px;
            "
          ></canvas>
        </div>
        <div style="margin-top: 15px;">
          <button type="button" class="btn btn-default btn-sm" id="hms-clear-signature">
            <i class="fa fa-eraser"></i> ${__("Clear")}
          </button>
        </div>
        <p style="margin-top: 10px; font-size: 12px; color: #999;">
          <i class="fa fa-info-circle"></i> ${__("Click and drag to draw your signature")}
        </p>
      </div>
    `;
  }

  initCanvas() {
    this.canvas = document.getElementById("hms-signature-canvas");
    if (!this.canvas) {
      console.error("Signature canvas not found");
      return;
    }

    this.ctx = this.canvas.getContext("2d");
    
    // Set up canvas styles
    this.ctx.strokeStyle = this.lineColor;
    this.ctx.lineWidth = this.lineWidth;
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";

    // Fill with background color
    this.ctx.fillStyle = this.backgroundColor;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Bind event handlers
    this.bindEvents();

    // Set up clear button
    const clearBtn = document.getElementById("hms-clear-signature");
    if (clearBtn) {
      clearBtn.addEventListener("click", () => this.clearCanvas());
    }
  }

  bindEvents() {
    // Mouse events
    this.canvas.addEventListener("mousedown", (e) => this.startDrawing(e));
    this.canvas.addEventListener("mousemove", (e) => this.draw(e));
    this.canvas.addEventListener("mouseup", (e) => this.stopDrawing(e));
    this.canvas.addEventListener("mouseleave", (e) => this.stopDrawing(e));

    // Touch events for tablet/mobile
    this.canvas.addEventListener("touchstart", (e) => this.startDrawing(e), { passive: false });
    this.canvas.addEventListener("touchmove", (e) => this.draw(e), { passive: false });
    this.canvas.addEventListener("touchend", (e) => this.stopDrawing(e), { passive: false });
    this.canvas.addEventListener("touchcancel", (e) => this.stopDrawing(e), { passive: false });

    // Pointer events (for stylus support)
    this.canvas.addEventListener("pointerdown", (e) => this.startDrawing(e));
    this.canvas.addEventListener("pointermove", (e) => this.draw(e));
    this.canvas.addEventListener("pointerup", (e) => this.stopDrawing(e));
    this.canvas.addEventListener("pointerleave", (e) => this.stopDrawing(e));
  }

  getCoordinates(e) {
    const rect = this.canvas.getBoundingClientRect();
    let clientX, clientY;

    if (e.touches && e.touches.length > 0) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else if (e.clientX !== undefined) {
      clientX = e.clientX;
      clientY = e.clientY;
    } else {
      return null;
    }

    // Calculate the scaling factor
    const scaleX = this.canvas.width / rect.width;
    const scaleY = this.canvas.height / rect.height;

    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY,
    };
  }

  startDrawing(e) {
    e.preventDefault();
    
    const coords = this.getCoordinates(e);
    if (!coords) return;

    this.isDrawing = true;
    this.lastX = coords.x;
    this.lastY = coords.y;

    // Draw a dot for single click
    this.ctx.beginPath();
    this.ctx.arc(coords.x, coords.y, this.lineWidth / 2, 0, Math.PI * 2);
    this.ctx.fillStyle = this.lineColor;
    this.ctx.fill();
  }

  draw(e) {
    if (!this.isDrawing) return;
    e.preventDefault();

    const coords = this.getCoordinates(e);
    if (!coords) return;

    this.ctx.beginPath();
    this.ctx.moveTo(this.lastX, this.lastY);
    this.ctx.lineTo(coords.x, coords.y);
    this.ctx.stroke();

    this.lastX = coords.x;
    this.lastY = coords.y;
    this.hasDrawn = true;
  }

  stopDrawing(e) {
    if (e) e.preventDefault();
    this.isDrawing = false;
  }

  clearCanvas() {
    if (!this.ctx) return;
    
    this.ctx.fillStyle = this.backgroundColor;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this.hasDrawn = false;
  }

  isCanvasBlank() {
    if (!this.hasDrawn) return true;
    
    const pixelData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height).data;

    // Check if all pixels match the background color
    // For white background (255, 255, 255)
    for (let i = 0; i < pixelData.length; i += 4) {
      if (pixelData[i] !== 255 || pixelData[i + 1] !== 255 || pixelData[i + 2] !== 255) {
        return false;
      }
    }
    return true;
  }

  submitSignature() {
    if (this.isCanvasBlank()) {
      frappe.msgprint({
        title: __("Signature Required"),
        message: __("Please draw your signature before proceeding."),
        indicator: "orange",
      });
      return;
    }

    const signatureData = this.canvas.toDataURL("image/png");
    
    this.dialog.hide();
    
    if (this.signaturePromiseResolve) {
      this.signaturePromiseResolve({
        Data: signatureData,
        format: "png",
        timestamp: new Date().toISOString(),
      });
    }
  }

  cancel() {
    this.dialog.hide();
    
    if (this.signaturePromiseResolve) {
      this.signaturePromiseResolve(null);
    }
  }

  destroy() {
    if (this.dialog) {
      this.dialog.hide();
    }
  }
}

// Make Signature available globally
window.Signature = Signature;
