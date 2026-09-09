import { NextResponse } from "next/server";
import { mockChatFiles } from "../../mock-data";
import zlib from "zlib";

const DOCUMENT_EXTENSIONS = new Set([
  ".pdf",
  ".txt",
  ".csv",
  ".docx",
  ".text",
  ".md",
  ".json",
]);
const IMAGE_EXTENSIONS = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".gif",
  ".svg",
]);

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api/v1";

let isBackendOnline: boolean | null = null;
let lastCheckTime = 0;

async function checkBackend(): Promise<boolean> {
  const now = Date.now();
  if (isBackendOnline !== null && now - lastCheckTime < 15000) {
    return isBackendOnline;
  }
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 1500);
    const healthUrl = `${BACKEND_URL.replace(/\/api\/v1\/?$/, "")}/api/v1/health`;
    const res = await fetch(healthUrl, {
      method: "GET",
      signal: ctrl.signal,
    });
    clearTimeout(t);
    isBackendOnline = res.ok;
  } catch {
    isBackendOnline = false;
  }
  lastCheckTime = Date.now();
  return isBackendOnline;
}

function extractTextFromPdfBuffer(buffer: Buffer): string {
  let fullText = "";
  const rawString = buffer.toString("latin1");

  // 1. Search for FlateDecode or uncompressed streams
  const streamRegex = /stream\r?\n([\s\S]*?)\r?\nendstream/g;
  let match: RegExpExecArray | null;
  while ((match = streamRegex.exec(rawString)) !== null) {
    const streamBytes = Buffer.from(match[1], "latin1");
    let decompressed: Buffer | null = null;
    try {
      decompressed = zlib.inflateSync(streamBytes);
    } catch {
      try {
        decompressed = zlib.inflateRawSync(streamBytes);
      } catch {
        decompressed = null;
      }
    }

    const textChunk = decompressed ? decompressed.toString("latin1") : match[1];

    // Extract text in Tj and TJ operators
    const tjMatches = textChunk.match(/\(([^()]+)\)\s*Tj/g);
    if (tjMatches) {
      fullText += " " + tjMatches.map((m) => m.replace(/^\(|\)\s*Tj$/g, "")).join(" ");
    }
    const tjArrayMatches = textChunk.match(/\[([^\]]+)\]\s*TJ/g);
    if (tjArrayMatches) {
      for (const arr of tjArrayMatches) {
        const innerStrings = arr.match(/\(([^()]+)\)/g);
        if (innerStrings) {
          fullText += " " + innerStrings.map((s) => s.slice(1, -1)).join("");
        }
      }
    }
  }

  // 2. Check for literal uncompressed strings in whole document if streams yielded nothing
  if (!fullText.trim()) {
    const uncompressedMatches = rawString.match(/\(([^()]+)\)\s*Tj/g);
    if (uncompressedMatches) {
      fullText = uncompressedMatches.map((m) => m.replace(/^\(|\)\s*Tj$/g, "")).join(" ");
    }
  }

  return fullText
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export async function POST(req: Request) {
  // Parse formData once safely
  let formData: FormData;
  try {
    formData = await req.formData();
  } catch (err) {
    return NextResponse.json(
      {
        error: {
          code: "PARSE_ERROR",
          message: err instanceof Error ? err.message : "Failed to parse form data",
          status: 400,
        },
      },
      { status: 400 }
    );
  }

  // 1. If backend is online, forward the parsed formData to FastAPI (PyMuPDF)
  const backendUp = await checkBackend();
  if (backendUp) {
    try {
      const backendRes = await fetch(`${BACKEND_URL}/conversations/upload`, {
        method: "POST",
        headers: {
          ...(req.headers.get("authorization")
            ? { Authorization: req.headers.get("authorization")! }
            : {}),
        },
        body: formData,
      });

      if (backendRes.ok) {
        return backendRes;
      }
    } catch (e) {
      console.warn("[Upload Proxy] Forwarding to backend failed, falling back to standalone:", e);
    }
  }

  // 2. Next.js standalone file upload handler
  try {
    const file = formData.get("file");

    if (!file || !(file instanceof Blob)) {
      return NextResponse.json(
        {
          error: {
            code: "NO_FILE",
            message: "No file provided in form data.",
            status: 400,
          },
        },
        { status: 400 }
      );
    }

    const filename = (file as File).name || "uploaded_file";
    const extMatch = filename.lastIndexOf(".");
    const ext = extMatch !== -1 ? filename.substring(extMatch).toLowerCase() : "";

    const isDocument = DOCUMENT_EXTENSIONS.has(ext);
    const isImage = IMAGE_EXTENSIONS.has(ext);

    if (!isDocument && !isImage) {
      return NextResponse.json(
        {
          error: {
            code: "UNSUPPORTED_TYPE",
            message: `Unsupported file type: ${ext}. Supported: ${Array.from(
              new Set([...DOCUMENT_EXTENSIONS, ...IMAGE_EXTENSIONS])
            ).join(", ")}`,
            status: 400,
          },
        },
        { status: 400 }
      );
    }

    const fileType = isDocument ? "document" : "image";
    const uniqueId = `${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
    const safeFilename = filename.replace(/[^a-zA-Z0-9._-]/g, "_");
    const uniqueName = `${uniqueId}_${safeFilename}`;
    const fileUrl = `/api/v1/files/chat/${uniqueName}`;

    // Extract text preview
    let extractedText = "";
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    if (isDocument) {
      if (ext === ".txt" || ext === ".csv" || ext === ".md" || ext === ".json") {
        extractedText = buffer.toString("utf-8");
      } else if (ext === ".pdf") {
        extractedText = extractTextFromPdfBuffer(buffer);
        if (!extractedText) {
          extractedText = `[Ingested PDF Document: ${filename}, Size: ${(file.size / 1024).toFixed(1)} KB]`;
        }
      } else {
        extractedText = `[Attached technical document: ${filename}, Size: ${(file.size / 1024).toFixed(1)} KB]`;
      }
    }

    // Save in in-memory file store
    mockChatFiles[uniqueName] = {
      filename,
      url: fileUrl,
      type: fileType,
      extracted_text: extractedText,
      dataBase64: buffer.toString("base64"),
      contentType: file.type || (isImage ? `image/${ext.replace(".", "")}` : "application/octet-stream"),
    };

    return NextResponse.json({
      filename,
      url: fileUrl,
      type: fileType,
      extracted_text_preview: extractedText ? extractedText.substring(0, 2000) : null,
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: {
          code: "UPLOAD_ERROR",
          message: err instanceof Error ? err.message : "Failed to upload file.",
          status: 500,
        },
      },
      { status: 500 }
    );
  }
}
