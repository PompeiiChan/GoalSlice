/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_USE_MOCK: string
  readonly VITE_BACKEND_PROXY_TARGET: string
  readonly VITE_DEMO_RESET: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
