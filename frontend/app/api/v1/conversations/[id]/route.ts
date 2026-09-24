import { proxyToBackend } from "@/app/api/v1/proxy";

export async function GET(req: Request) { return proxyToBackend(req); }
export async function DELETE(req: Request) { return proxyToBackend(req); }
