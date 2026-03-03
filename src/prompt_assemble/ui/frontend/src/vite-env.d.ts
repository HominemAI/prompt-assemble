/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL?: string;
  readonly VITE_SUPABASE_PUBLISHABLE_KEY?: string;
  readonly VITE_DEFAULT_BACKEND_MODE?: 'remote' | 'local' | 'filesystem';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
