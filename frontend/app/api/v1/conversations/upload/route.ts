import { NextResponse } from "next/server";
import { mockChatFiles } from "../../mock-data";

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
    const t = setTimeout(() => ctrl.abort(), 400);
    const res = await fetch(`${BACKEND_URL}/knowledge-base/summary`, {
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

  // 1. If backend is online, forward the parsed formData
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
    } catch {
      // Backend failed, fall back to standalone handler
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
        // Simple plain text extraction from PDF stream if present
        const rawString = buffer.toString("latin1");
        const matches = rawString.match(/\(([^()]+)\)\s*Tj/g);
        if (matches && matches.length > 0) {
          extractedText = matches
            .map((m) => m.replace(/^\(|\)\s*Tj$/g, ""))
            .join(" ");
        }
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
      extracted_text_preview: extractedText ? extractedText.substring(0, 500) : null,
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
