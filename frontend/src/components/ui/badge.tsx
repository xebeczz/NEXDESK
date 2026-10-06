import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold transition-all duration-200",
  {
    variants: {
      variant: {
        default: "badge-primary",
        secondary: "badge-neutral",
        destructive: "badge-danger",
        outline: "border border-border bg-transparent text-text-secondary hover:bg-surface-hover",
        success: "badge-success",
        warning: "badge-warning",
        danger: "badge-danger",
        info: "badge-info",
        neutral: "badge-neutral",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };