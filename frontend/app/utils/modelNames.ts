/**
 * Centralized mapping and resolver for local model display names.
 * Ensures friendly names appear consistently across all UI screens and hides raw technical tags:
 *   - qwen2.5:3b        -> "Reasoning model"
 *   - qwen2.5-coder:3b  -> "coder model"
 *   - qwen2.5vl:3b      -> "vision language model"
 *   - nomic-embed-text  -> "Embedding model"
 */

export const MODEL_DISPLAY_NAMES: Record<string, string> = {
  "qwen2.5:3b": "Reasoning model",
  "qwen2.5": "Reasoning model",
  "qwen2.5-coder:3b": "coder model",
  "qwen2.5-coder": "coder model",
  "qwen2.5vl:3b": "vision language model",
  "qwen2.5vl": "vision language model",
  "qwen2.5-vl:3b": "vision language model",
  "qwen2.5-vl": "vision language model",
  "nomic-embed-text:latest": "Embedding model",
  "nomic-embed-text": "Embedding model",
};

export function getModelDisplayName(modelIdOrName?: string | null): string {
  if (!modelIdOrName) return "";
  const trimmed = modelIdOrName.trim();
  if (MODEL_DISPLAY_NAMES[trimmed]) {
    return MODEL_DISPLAY_NAMES[trimmed];
  }
  const lower = trimmed.toLowerCase();
  if (MODEL_DISPLAY_NAMES[lower]) {
    return MODEL_DISPLAY_NAMES[lower];
  }
  for (const [key, val] of Object.entries(MODEL_DISPLAY_NAMES)) {
    if (lower === key.toLowerCase()) return val;
  }
  // Check substrings for Qwen variants
  if (lower.includes("qwen") && lower.includes("coder")) {
    return "coder model";
  }
  if (lower.includes("qwen") && (lower.includes("vl") || lower.includes("vision"))) {
    return "vision language model";
  }
  if (lower.includes("qwen")) {
    return "Reasoning model";
  }
  return trimmed;
}

/**
 * Filter out raw qwen identifiers from being displayed as secondary labels or subtitles.
 */
export function cleanModelSubtitle(modelIdOrName?: string | null): string {
  if (!modelIdOrName) return "";
  const lower = modelIdOrName.toLowerCase();
  if (lower.includes("qwen")) {
    return "";
  }
  return modelIdOrName;
}
