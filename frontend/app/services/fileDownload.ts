/**
 * fileDownload.ts — Browser download helper for generated artifacts
 * Supports: Word (.docx), PowerPoint (.pptx), Excel (.xlsx), Code (.py, .js, .json), PDF, Text
 */

const MIME_TYPES: Record<string, string> = {
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  pdf: "application/pdf",
  py: "text/x-python",
  json: "application/json",
  txt: "text/plain",
  md: "text/markdown",
  csv: "text/csv",
};

export function downloadArtifact(filename: string, content: string | Blob, mimeType?: string) {
  if (typeof window === "undefined") return;

  const ext = filename.split(".").pop()?.toLowerCase() || "txt";
  const resolvedMime = mimeType || MIME_TYPES[ext] || "application/octet-stream";

  let blob: Blob;
  if (content instanceof Blob) {
    blob = content;
  } else {
    blob = new Blob([content], { type: resolvedMime });
  }

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);

  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 1000);
}

export function downloadJson(filename: string, data: unknown) {
  const jsonString = JSON.stringify(data, null, 2);
  downloadArtifact(filename, jsonString, "application/json");
}
