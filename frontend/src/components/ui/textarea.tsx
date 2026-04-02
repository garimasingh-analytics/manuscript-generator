import * as React from "react";
import { cn } from "../../lib/utils";

export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm",
        "focus:outline-none focus:ring-2 focus:ring-slate-400",
        className,
      )}
      {...props}
    />
  );
}

