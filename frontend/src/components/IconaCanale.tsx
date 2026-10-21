import { Badge } from "@mantine/core";
import { useId } from "react";

const NOMI: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
};

function nomeCanale(canale: string): string {
  return NOMI[canale] ?? canale;
}

export function IconaCanale({
  canale,
  size = 18,
}: {
  canale: string;
  size?: number;
}) {
  const gradId = useId();
  if (canale === "facebook") {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        aria-hidden="true"
        style={{ flex: "none", display: "block" }}
      >
        <circle cx="12" cy="12" r="12" fill="#1877F2" />
        <path
          d="M15.12 15.32l.45-2.9h-2.78v-1.88c0-.8.39-1.57 1.64-1.57h1.27V6.5s-1.15-.2-2.25-.2c-2.3 0-3.8 1.39-3.8 3.91v2.21H7.1v2.9h2.55V24a12.1 12.1 0 003.14 0v-8.68h2.33z"
          fill="#ffffff"
        />
      </svg>
    );
  }
  if (canale === "instagram") {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        aria-hidden="true"
        style={{ flex: "none", display: "block" }}
      >
        <defs>
          <radialGradient id={gradId} cx="30%" cy="107%" r="150%">
            <stop offset="0%" stopColor="#fdf497" />
            <stop offset="5%" stopColor="#fdf497" />
            <stop offset="45%" stopColor="#fd5949" />
            <stop offset="60%" stopColor="#d6249f" />
            <stop offset="90%" stopColor="#285AEB" />
          </radialGradient>
        </defs>
        <rect width="24" height="24" rx="6" fill={`url(#${gradId})`} />
        <rect
          x="4.5"
          y="4.5"
          width="15"
          height="15"
          rx="4.2"
          fill="none"
          stroke="#ffffff"
          strokeWidth="1.8"
        />
        <circle
          cx="12"
          cy="12"
          r="3.6"
          fill="none"
          stroke="#ffffff"
          strokeWidth="1.8"
        />
        <circle cx="16.3" cy="7.7" r="1.1" fill="#ffffff" />
      </svg>
    );
  }
  return null;
}

export function EtichettaCanale({
  canale,
  testo,
  size = 18,
}: {
  canale: string;
  testo?: string;
  size?: number;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        fontWeight: 600,
      }}
    >
      <IconaCanale canale={canale} size={size} />
      <span>{testo ?? nomeCanale(canale)}</span>
    </span>
  );
}

export function BadgeCanale({
  canale,
  size = "sm",
}: {
  canale: string;
  size?: "xs" | "sm" | "md";
}) {
  const iconSize = size === "xs" ? 13 : 15;
  return (
    <Badge
      size={size}
      variant="default"
      radius="xl"
      leftSection={<IconaCanale canale={canale} size={iconSize} />}
      styles={{
        root: {
          textTransform: "none",
          fontWeight: 600,
          background: "#ffffff",
          borderColor: "rgba(15, 23, 42, 0.12)",
          color: "#0f172a",
          paddingLeft: 7,
        },
      }}
    >
      {nomeCanale(canale)}
    </Badge>
  );
}
