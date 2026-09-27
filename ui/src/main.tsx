import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/hanken-grotesk'
import '@fontsource/martian-mono/300.css'
import '@fontsource/martian-mono/400.css'
import '@fontsource/martian-mono/500.css'
import './styles/tokens.css'
import './styles/app.css'
import './styles/pages.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
