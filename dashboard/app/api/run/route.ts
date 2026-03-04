import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const sidecarUrl = process.env.SIDECAR_URL;
  if (!sidecarUrl) {
    return NextResponse.json(
      { error: "SIDECAR_URL not configured" },
      { status: 503 }
    );
  }

  const body = await req.json();

  try {
    const res = await fetch(`${sidecarUrl}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: "Sidecar unreachable — is it running?" },
      { status: 502 }
    );
  }
}

export async function GET() {
  const sidecarUrl = process.env.SIDECAR_URL;
  if (!sidecarUrl) {
    return NextResponse.json(
      { error: "SIDECAR_URL not configured", running: false },
      { status: 503 }
    );
  }

  try {
    const res = await fetch(`${sidecarUrl}/status`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ running: false, error: "Sidecar unreachable" });
  }
}
