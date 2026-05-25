import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function Svg({ size = 16, children, ...rest }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...rest}
    >
      {children}
    </svg>
  );
}

export const SparkleIcon = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" />
  </Svg>
);

export const SlidersIcon = (p: IconProps) => (
  <Svg {...p}>
    <line x1="4" y1="6" x2="14" y2="6" />
    <line x1="18" y1="6" x2="20" y2="6" />
    <circle cx="16" cy="6" r="2" />
    <line x1="4" y1="12" x2="6" y2="12" />
    <line x1="10" y1="12" x2="20" y2="12" />
    <circle cx="8" cy="12" r="2" />
    <line x1="4" y1="18" x2="14" y2="18" />
    <line x1="18" y1="18" x2="20" y2="18" />
    <circle cx="16" cy="18" r="2" />
  </Svg>
);

export const BookmarkIcon = (p: IconProps) => (
  <Svg {...p}>
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </Svg>
);

export const ThumbsUpIcon = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 11v8a2 2 0 0 0 2 2h7.5a2 2 0 0 0 1.95-1.55l1.4-6A2 2 0 0 0 17.9 11H14V6a2 2 0 0 0-2-2l-3 7" />
    <path d="M3 11h4v10H3z" />
  </Svg>
);

export const ThumbsDownIcon = (p: IconProps) => (
  <Svg {...p}>
    <path d="M17 13V5a2 2 0 0 0-2-2H7.5a2 2 0 0 0-1.95 1.55l-1.4 6A2 2 0 0 0 6.1 13H10v5a2 2 0 0 0 2 2l3-7" />
    <path d="M21 13h-4V3h4z" />
  </Svg>
);
