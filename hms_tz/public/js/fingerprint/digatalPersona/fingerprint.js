import { loadDigitalPersonaSDK } from "../../utils";
import { FingerprintReader, SampleFormat } from '@digitalpersona/devices';


loadDigitalPersonaSDK('/assets/hms_tz/js/modules/websdk/index.js')


class dpFingerprint {
    constructor(opts) {
        this.frm = opts.frm;
        this.api_url = opts.url;
        this.label = opts.label || 'Send Request';
        this.reader = new FingerprintReader();
        this.devices = [];
        this.selectedDevice = null;
        this.selectedFinger = null;
        this.samples = null;
        this.init();
    }

    async init() {
        this.reader.on("DeviceConnected", this.onDeviceConnected);
        this.reader.on("DeviceDisconnected", this.onDeviceDisconnected);
        this.reader.on("SamplesAcquired", this.onSamplesAcquired);
        this.reader.on("ErrorOccurred", this.onReaderError);

        try {
            await this.reader.startAcquisition(SampleFormat.Intermediate);
            this.devices = await this.reader.getDevices();
            this.updateDialog();
        } catch (err) {
            this.handleError(err);
        }
    }

    onDeviceConnected(event) {
        console.log("Device Connected:", event);
        this.selectedDevice = event.deviceId;
        this.updateDialog();
        setTimeout(() => {
            this.updateDialog();
        }, 3000);
    }

    onDeviceDisconnected(event) {
        console.log("Device Disconnected:", event);
        this.selectedDevice = null;
        this.updateDialog();
    }

    async onSamplesAcquired(event) {
        try {
            const samples = event.samples;
            console.log("Fingerprint samples acquired:", samples);
            this.samples = samples;
            this.showFingerprintThumbnail(samples[0]); 
            // await this.sendToAPI(samples);
            this.updatePrimaryLabel();
        } catch (error) {
            this.handleError(error);
            frappe.msgprint(__('Fingerprint scan failed. Please try again.'));
        }
    }

    onReaderError(event) {
        console.error("Reader Error:", event);
    }

    handleError(error) {
        console.error("Error:", error);
    }

    async sendToAPI(samples) {
        try {
            const response = await fetch('/api/method/your_app_name.api.handle_fingerprint', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ samples }),
            });
            const data = await response.json();
            console.log("API Response:", data);
        } catch (error) {
            console.error("Failed to send samples to API:", error);
        }
    }

    destroy() {
        this.reader.off();
        delete this.reader;
    }

    showDialog() {
        this.dialog = new frappe.ui.Dialog({
            title: __('Scan Fingerprint'),
            fields: [
                {
                    fieldtype: 'Select',
                    label: __('Select Device'),
                    fieldname: 'device',
                    options: this.devices.map(device => device.deviceId),
                    reqd: 1,
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'device_status',
                    options: `<div id="device-status">${__('No device connected.')}</div>`,
                },
                {
                    fieldtype: 'Column Break',
                },
                {
                    fieldtype: 'Select',
                    label: __('Select Fingers to Scan'),
                    fieldname: 'finger',
                    options: [
                        { label: __('Right Thumb (R1)'), value: 'R1' },
                        { label: __('Right Index (R2)'), value: 'R2' },
                        { label: __('Right Middle (R3)'), value: 'R3' },
                        { label: __('Right Ring (R4)'), value: 'R4' },
                        { label: __('Right Little (R5)'), value: 'R5' },
                        { label: __('Left Thumb (L1)'), value: 'L1' },
                        { label: __('Left Index (L2)'), value: 'L2' },
                        { label: __('Left Middle (L3)'), value: 'L3' },
                        { label: __('Left Ring (L4)'), value: 'L4' },
                        { label: __('Left Little (L5)'), value: 'L5' },
                    ],
                    reqd: 1,
                },
                {
                    fieldtype: 'Section Break',
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'fingerprint_thumbnail',
                    options: `<div id="fingerprint-thumbnail"></div>`,
                },
            ],
            primary_action_label: __('Scan'),
            primary_action: () => this.startScan(),
            secondary_action_label: __('Cancel'),
            secondary_action: () => this.dialog.hide(),
        });

        this.dialog.show();
        this.updateDialog();
    }

    updateDialog() {
        const devicemsg = `<div class="reader-communication-error text-sm">
                No device connected.. Try to downlaod <a href="https://crossmatch.hid.gl/lite-client" target="_blank" style='color: blue; font-weight: bold;'>DigitalPersona Client</a> and install it.
            </div>`
        // `<div style="color: red;">${__('No device connected.')}</div>`
            
        const deviceStatus = this.selectedDevice ? `<div style="color: green;">${__('Device Connected')}</div>` : devicemsg;
        this.dialog.set_value('device_status', deviceStatus);

        if (this.devices.length > 0 && !this.selectedDevice) {
            this.selectedDevice = this.devices[0].deviceId;
            this.dialog.set_value('device', this.selectedDevice);
        }
    }

    showFingerprintThumbnail(sample) {
        const thumbnailDiv = this.dialog.get_field('fingerprint_thumbnail').$wrapper;
        thumbnailDiv.html(`<img src="${sample}" alt="Fingerprint Thumbnail" style="width: 100px; height: 100px;">`);
    }

    updatePrimaryLabel() {
        this.dialog.set_primary_action_label(this.label);
    }

    startScan() {
        this.selectedFinger = this.dialog.get_value('finger');
        if (!this.selectedFinger) {
            frappe.msgprint(__('Please select finger to scan.'));
            return;
        }

        console.log('Starting scan for:', selectedFinger);
        // Implement the logic to scan the selected fingers

    }
}

window.dpFingerprint = dpFingerprint;


