import { proxyToBackend } from "@/app/api/v1/proxy";

export async function GET(req: Request) { return proxyToBackend(req); }
export async function POST(req: Request) { return proxyToBackend(req); }
