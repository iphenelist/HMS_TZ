import { createApp } from "vue"
import { createPinia } from "pinia"

import App from "./App.vue"
import router from "./router"
import { initSocket } from "./socket"

import {
	Alert,
	Avatar,
	Badge,
	Button,
	Card,
	Checkbox,
	DatePicker,
	Dialog,
	Dropdown,
	ErrorMessage,
	FeatherIcon,
	FormControl,
	Input,
	LoadingIndicator,
	LoadingText,
	Popover,
	Select,
	Checkbox,
	TextInput,
	TextEditor,
	Tooltip,
	frappeRequest,
	pageMetaPlugin,
	resourcesPlugin,
	setConfig,
} from "frappe-ui"

import "./index.css"

const globalComponents = {
	// Basic UI Components
	Alert,
	Avatar,
	Badge,
	Button,
	Card,
	
	// Form Components
	Checkbox,
	DatePicker,
	FormControl,
	Input,
	Select,
	Checkbox,
	TextInput,
	TextEditor,
	
	// Layout & Navigation
	Dialog,
	Dropdown,
	Popover,
	Tooltip,
	
	// Icons & Indicators
	FeatherIcon,
	LoadingIndicator,
	LoadingText,
	
	// Utility Components
	ErrorMessage,
}

const app = createApp(App)
const pinia = createPinia()

setConfig("resourceFetcher", frappeRequest)

app.use(pinia)
app.use(router)
app.use(resourcesPlugin)
app.use(pageMetaPlugin)

const socket = initSocket()
app.config.globalProperties.$socket = socket

for (const key in globalComponents) {
	app.component(key, globalComponents[key])
}

app.mount("#app")
