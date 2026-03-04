import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ActionBadgeProps {
  action: string;
}

export function ActionBadge({ action }: ActionBadgeProps) {
  const a = action.toUpperCase();
  return (
    <Badge
      className={cn(
        a === "BUY" && "bg-green-600 hover:bg-green-700",
        a === "SELL" && "bg-red-600 hover:bg-red-700",
        a === "HOLD" && "bg-muted text-muted-foreground hover:bg-muted"
      )}
    >
      {a}
    </Badge>
  );
}
