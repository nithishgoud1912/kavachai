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

function extractTextFromPdfBuffer(buffer: Buffer): string {
  let fullText = "";
  const rawString = buffer.toString("latin1");

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

  // 1. Try forwarding to backend if supported
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 2000);
    const backendRes = await fetch(`${BACKEND_URL}/investigations/upload`, {
      method: "POST",
      headers: {
        ...(req.headers.get("authorization")
          ? { Authorization: req.headers.get("authorization")! }
          : {}),
      },
      body: formData,
      signal: ctrl.signal,
    });
    clearTimeout(t);
    if (backendRes.ok) {
      return backendRes;
    }
  } catch {
    // If backend doesn't support investigation upload yet, handle locally
  }

  // 2. Standalone investigation upload handler
  try {
    const files = formData.getAll("files");
    const singleFile = formData.get("file");
    const allFiles: Blob[] = [];

    if (files && files.length > 0) {
      for (const f of files) {
        if (f instanceof Blob) allFiles.push(f);
      }
    } else if (singleFile && singleFile instanceof Blob) {
      allFiles.push(singleFile);
    }

    if (allFiles.length === 0) {
      return NextResponse.json(
        {
          error: {
            code: "NO_FILES",
            message: "No files uploaded.",
            status: 400,
          },
        },
        { status: 400 }
      );
    }

    let relativePaths: string[] = [];
    const pathsRaw = formData.get("paths");
    if (typeof pathsRaw === "string") {
      try {
        relativePaths = JSON.parse(pathsRaw);
      } catch {
        relativePaths = [pathsRaw];
      }
    }

    const uploaded = await Promise.all(
      allFiles.map(async (file, idx) => {
        const filename = (file as File).name || `investigation_file_${idx + 1}`;
        const relativePath = relativePaths[idx] || filename;
        const extMatch = filename.lastIndexOf(".");
        const ext = extMatch !== -1 ? filename.substring(extMatch).toLowerCase() : "";

        const isDocument = DOCUMENT_EXTENSIONS.has(ext);
        const isImage = IMAGE_EXTENSIONS.has(ext);
        const fileType: "document" | "image" = isImage ? "image" : "document";

        const uniqueId = `inv_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
        const safeFilename = filename.replace(/[^a-zA-Z0-9._-]/g, "_");
        const uniqueName = `${uniqueId}_${safeFilename}`;
        const sourceId = `src_${uniqueId}`;
        const fileUrl = `/api/v1/evidence/files/${sourceId}/raw`;

        let extractedText = "";
        const arrayBuffer = await file.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);

        if (isDocument) {
          if (ext === ".txt" || ext === ".csv" || ext === ".md" || ext === ".json") {
            extractedText = buffer.toString("utf-8");
          } else if (ext === ".pdf") {
            extractedText = extractTextFromPdfBuffer(buffer);
            if (!extractedText) {
              extractedText = `[Ingested Investigation PDF: ${filename}]`;
            }
          } else {
            extractedText = `[Investigation Evidence File: ${filename}]`;
          }
        }

        // Store in mock storage for raw download
        mockChatFiles[sourceId] = {
          filename,
          url: fileUrl,
          type: fileType,
          extracted_text: extractedText,
          dataBase64: buffer.toString("base64"),
          contentType:
            file.type || (isImage ? `image/${ext.replace(".", "")}` : "application/octet-stream"),
        };

        return {
          filename,
          relative_path: relativePath,
          source_id: sourceId,
          url: fileUrl,
          type: fileType,
          size: file.size,
          extracted_text: extractedText ? extractedText.substring(0, 4000) : undefined,
        };
      })
    );

    return NextResponse.json({ uploaded });
  } catch (err) {
    return NextResponse.json(
      {
        error: {
          code: "UPLOAD_ERROR",
          message: err instanceof Error ? err.message : "Failed to upload investigation files",
          status: 500,
        },
      },
      { status: 500 }
    );
  }
}
