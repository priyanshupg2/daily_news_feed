import Link from 'next/link';

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function ItemRow({
  id,
  title,
  publishedAt,
}: {
  id: string;
  title: string;
  publishedAt: string | null;
}) {
  return (
    <Link
      href={`/discovery/item/${id}`}
      className="block border-b border-gray-100 px-4 py-3 hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm text-gray-900 leading-snug">{title}</p>
        {publishedAt && (
          <span className="text-xs text-gray-400 whitespace-nowrap mt-0.5">
            {timeAgo(publishedAt)}
          </span>
        )}
      </div>
    </Link>
  );
}
