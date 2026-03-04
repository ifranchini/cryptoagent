"use client";

import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Play, Loader2, Check, X } from "lucide-react";

type Status = "idle" | "running" | "done" | "error";
const RESET_DELAY_MS = 4000;

export function RunTrigger() {
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resetAfterDelay = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setStatus("idle");
      setMessage("");
    }, RESET_DELAY_MS);
  }, []);

  async function handleRun() {
    setStatus("running");
    setMessage("");
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: "SOL", cycles: 1 }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus("done");
        setMessage(data.status ?? "Pipeline triggered");
      } else {
        setStatus("error");
        setMessage(data.error ?? "Failed to trigger run");
      }
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Network error");
    }
    resetAfterDelay();
  }

  const icon = {
    idle: <Play className="mr-2 h-4 w-4" />,
    running: <Loader2 className="mr-2 h-4 w-4 animate-spin" />,
    done: <Check className="mr-2 h-4 w-4" />,
    error: <X className="mr-2 h-4 w-4" />,
  }[status];

  return (
    <div className="flex items-center gap-3">
      <Button
        onClick={handleRun}
        disabled={status === "running"}
        size="sm"
        variant={status === "error" ? "destructive" : "default"}
      >
        {icon}
        Run Pipeline
      </Button>
      {message && (
        <span className="text-xs text-muted-foreground">{message}</span>
      )}
    </div>
  );
}
