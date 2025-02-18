import { loadDigitalPersonaSDK } from "../../utils";
import { FingerprintReader, SampleFormat } from '@digitalpersona/devices';


loadDigitalPersonaSDK('/assets/hms_tz/js/fingerprint/digatalPersona/modules/WebSdk/index.js').then(() => {
    console.log("DigitalPersona SDK loaded successfully.");
}).catch((error) => {
    console.error("Failed to load DigitalPersona SDK:", error);
});


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
        this.reader.on("onCommunicationFailed", this.onCommunicationFailed);
        this.reader.on("DeviceConnected", this.onDeviceConnected);
        this.reader.on("DeviceDisconnected", this.onDeviceDisconnected);
        this.reader.on("onAcquisitionStarted", this.onAcquisitionStarted);
        this.reader.on("onQualityReported", this.onQualityReported);
        this.reader.on("SamplesAcquired", this.onSamplesAcquired);
        this.reader.on("ErrorOccurred", this.onReaderError);

        this.showDialog();
        
        try {
            this.devices = await this.reader.enumerateDevices();
            this.updateDialog();
        } catch (err) {
            this.handleError(err, 'init');
        }
    }

    onDeviceConnected = (event) => {
        console.log("Device Connected: ", event);
        this.selectedDevice = event.deviceId;
        this.updateDialog();
    }

    onDeviceDisconnected = (event) => {
        console.log("Device Disconnected: ", event);
        this.selectedDevice = null;
        this.updateDialog();
    }

    onSamplesAcquired = async (event) => {
        try {
            const samples = event.samples;
            this.samples = samples;
            this.showFingerprintImage(samples[0]); 
            this.updatePrimaryLabel();
            this.fingerprintAcquired = true;
        } catch (error) {
            this.handleError(error, 'SampleAcquired');
            frappe.msgprint(__('Fingerprint scan failed. Please try again.'));
        }
    }

    onReaderError = (event) => {
        console.error("Reader Error:", event);
    }

    onCommunicationFailed = (event) => {
        console.error("Communication Error:", event);
    }

    onAcquisitionStarted = (event) => {
        console.log("Acquisition Started", event);
    }

    onQualityReported = (event) => {
        console.log("QualityReported started", event)
    }

    handleError = (error, stage) => {
        const err = `Stage: ${stage}`
        console.log(err, error);
    }

    destroy = () => {
        this.dialog.hide();
        this.reader.off();
        delete this.reader;
    }

    showDialog = () => {
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
                    onchange: () => this.toggleFingerprintField(),
                },
                {
                    fieldtype: 'Section Break',
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'fingerprint',
                    options: `<div id="fingerprint-image"></div>`,
                },
            ],
            secondary_action_label: __('Cancel'),
            secondary_action: () => this.destroy(),
        });

        this.dialog.show();
        this.updateDialog();
    }

    toggleFingerprintField = () => {
        if (this.dialog.get_value('finger')) {
            this.startScan();

            const fingerprintDiv = this.dialog.get_field('fingerprint').$wrapper;
            fingerprintDiv.html(
                `<div id="fingerprint-image" style="width: 100px; height: 100px; border: 1px solid black;
                    display: flex; justify-content: center; align-items: center; text-align: center; margin-left: 180px;">
                    <span>Place a finger on the device</span>
                </div>`
            )

        }
    }

    updateDialog = () => {
        if (this.devices.length > 0 && !this.selectedDevice) {
            this.selectedDevice = this.devices[0];
            this.dialog.set_value('device', this.selectedDevice);
            this.dialog.set_df_property('device', 'options', this.devices)
            this.dialog.get_field('device').set_options();
        }

        const devicemsg = `<div class="reader-communication-error text-sm">
                No device connected.. Try to downlaod <a href="https://crossmatch.hid.gl/lite-client" target="_blank" style='color: blue; font-weight: bold;'>DigitalPersona Client</a> and install it.
            </div>`
            
        const deviceStatus = this.selectedDevice ? `<div style="color: green;">${__('Device Connected')}</div>` : devicemsg;
        this.dialog.set_value('device_status', deviceStatus);
    }

    showFingerprintImage = (sample) => {
        const d = this.dialog.get_field('fingerprint').$wrapper;

        if (sample?.Data) {
            let imageSrc = "/assets/hms_tz/images/fingerprint.png";

            d.html(`
                <div id="fingerprint-image" 
                    style="width: 120px; height: 140px; border: 1px solid black; 
                        display: flex; flex-direction: column; align-items: center; margin-left: 180px; 
                        justify-content: center; text-align: center;">
                    <img src="${imageSrc}" alt="Fingerprint" style="width: 100px; height: 100px;">
                </div>
            `);
        } else {
            d.html(`
                <div id="fingerprint-image" 
                    style="width: 300px; height: 140px; border: 1px solid black; 
                        display: flex; flex-direction: column; align-items: center; 
                        justify-content: center; text-align: center; margin-left: 180px;">
                        <p>No fingerprint found, Pleas try again</p>
                </div>
            `);
        }
    }

    updatePrimaryLabel = () => {
        this.dialog.set_primary_action(this.label, () => this.sendToAPI());
    };

    startScan = async () => {
        this.selectedFinger = this.dialog.get_value('finger');
        if (!this.selectedFinger) {
            frappe.msgprint(__('Please select finger to scan.'));
            return;
        }

        const device = this.dialog.get_value("device");
        if (!device) {
            frappe.msgprint(__('Please select device.'));
            return;
        }
        if (this.selectedDevice !== device) {
            this.selectedDevice = device;
        }

        await this.reader.startAcquisition(SampleFormat.Intermediate, this.selectedDevice);
    }
}

window.dpFingerprint = dpFingerprint;


