// Restrained compass-ring visual (Phase 5 brief Section 6): a static 8-sector
// ring with the authorized reference_directions highlighted. Deliberately:
// - no animation (Section 14: motion is optional, this component uses none)
// - no day-level precision, no score meter, no radar-chart complexity
// - color is never the only signal: highlighted sectors also get bold text
//   and a filled vs. outlined treatment; the same information is restated
//   as plain text beside the ring (Section 15: color-independent meaning)
const DIRECTION_LABELS = ["北", "北東", "東", "南東", "南", "南西", "西", "北西"] as const;

const SIZE = 220;
const CENTER = SIZE / 2;
const OUTER_RADIUS = 96;
const INNER_RADIUS = 58;
const LABEL_RADIUS = 112;
const GAP_DEGREES = 2;

function polarToCartesian(radius: number, angleDeg: number) {
  const angleRad = ((angleDeg - 0) * Math.PI) / 180;
  return {
    x: CENTER + radius * Math.sin(angleRad),
    y: CENTER - radius * Math.cos(angleRad),
  };
}

function describeSector(startAngle: number, endAngle: number) {
  const outerStart = polarToCartesian(OUTER_RADIUS, startAngle);
  const outerEnd = polarToCartesian(OUTER_RADIUS, endAngle);
  const innerEnd = polarToCartesian(INNER_RADIUS, endAngle);
  const innerStart = polarToCartesian(INNER_RADIUS, startAngle);

  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${OUTER_RADIUS} ${OUTER_RADIUS} 0 0 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${INNER_RADIUS} ${INNER_RADIUS} 0 0 0 ${innerStart.x} ${innerStart.y}`,
    "Z",
  ].join(" ");
}

export type CompassDirectionVisualProps = {
  referenceDirections: string[];
};

export default function CompassDirectionVisual({ referenceDirections }: CompassDirectionVisualProps) {
  const highlighted = new Set(referenceDirections);
  const summary =
    referenceDirections.length > 0
      ? `今月意識したい方向: ${referenceDirections.join("・")}`
      : "今月意識したい方向は算出されていません";

  return (
    <div className="flex flex-col items-center gap-3">
      <svg
        role="img"
        aria-label={summary}
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="max-w-full"
      >
        <g aria-hidden="true">
          {DIRECTION_LABELS.map((label, index) => {
            const centerAngle = index * 45;
            const isActive = highlighted.has(label);
            const path = describeSector(centerAngle - 22.5 + GAP_DEGREES, centerAngle + 22.5 - GAP_DEGREES);
            const labelPos = polarToCartesian(LABEL_RADIUS, centerAngle);

            return (
              <g key={label}>
                <path
                  d={path}
                  fill={isActive ? "var(--kt-color-action-primary)" : "var(--kt-color-background-subtle)"}
                  stroke={isActive ? "var(--kt-color-action-primary)" : "var(--kt-color-border-default)"}
                  strokeWidth={1}
                />
                <text
                  x={labelPos.x}
                  y={labelPos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={isActive ? 15 : 13}
                  fontWeight={isActive ? 700 : 400}
                  fill={isActive ? "var(--kt-color-text-primary)" : "var(--kt-color-text-muted)"}
                >
                  {label}
                </text>
              </g>
            );
          })}
        </g>
        <circle
          cx={CENTER}
          cy={CENTER}
          r={INNER_RADIUS - 6}
          fill="var(--kt-color-surface-default)"
          stroke="var(--kt-color-border-default)"
          strokeWidth={1}
        />
      </svg>

      <p className="text-center text-sm text-[var(--kt-color-text-secondary)]">{summary}</p>
    </div>
  );
}
