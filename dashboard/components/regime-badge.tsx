import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface RegimeBadgeProps {
  regime: string | null | undefined;
}

export function RegimeBadge({ regime }: RegimeBadgeProps) {
  const r = regime?.toLowerCase() ?? "unknown";
  return (
    <Badge
      variant="outline"
      className={cn(
        "capitalize",
        r === "bull" && "border-green-500 text-green-500",
        r === "bear" && "border-red-500 text-red-500",
        r === "sideways" && "border-yellow-500 text-yellow-500",
        r === "unknown" && "border-muted-foreground text-muted-foreground"
      )}
    >
      {r}
    </Badge>
  );
}
