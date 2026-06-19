import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import MainRouter from './routers/MainRouter.js'
import './index.css'

const app = createApp(App)

app.use(createPinia())
app.use(MainRouter)
app.mount('#app')
