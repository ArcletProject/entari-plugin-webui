export {}

declare global {
  interface Window {
    RUNTIME_CONFIG?: {
      baseURL?: string
    }
    WS_PATH: {
      baseURL?: string
    }
  }
}