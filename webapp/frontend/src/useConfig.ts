import { useEffect, useState } from "react";
import { api } from "./api";
import type { SiteConfig } from "./types";

let cache: SiteConfig | null = null;
let pending: Promise<SiteConfig> | null = null;

export function useConfig() {
  const [config, setConfig] = useState<SiteConfig | null>(cache);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (cache) return;
    pending = pending ?? api.config();
    pending.then((c) => { cache = c; setConfig(c); }).catch((e: Error) => { pending = null; setError(e.message); });
  }, []);
  return { config, error };
}
export function _resetConfigCache() { cache = null; pending = null; }
