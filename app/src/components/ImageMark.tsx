/** 含图标识：提示该篇正文内嵌有配图。形制与 Web 站 ImageMark.astro 一致。 */
export default function ImageMark({ count = 1, size = 13 }: { count?: number; size?: number }) {
  const label = count > 1 ? `正文含图 ${count} 幅` : '正文含图';
  return (
    <i className="image-mark" title={label} aria-label={label}>
      <svg viewBox="0 0 16 16" width={size} height={size} aria-hidden="true">
        <rect
          x="1.4"
          y="2.6"
          width="13.2"
          height="10.8"
          rx="1.6"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.15"
        />
        <circle cx="5.5" cy="6" r="1.35" fill="currentColor" />
        <path
          d="M2.2 12.2 6 8.6l2.6 2.3 2.1-1.9 3.1 3.2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.15"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {count > 1 && <span>{count}</span>}
    </i>
  );
}
