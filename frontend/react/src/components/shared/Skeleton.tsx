/**
 * Skeleton components — reusable loading placeholders
 *
 * Used across tabs while API data is loading.
 * All use animate-pulse from Tailwind.
 */

export function SkeletonLine({ className = "" }: { className?: string }) {
  return (
    <div className={`bg-white/5 rounded animate-pulse ${className}`} />
  );
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div
      className={`bg-dark-card border border-white/5 rounded-2xl
                  animate-pulse ${className}`}
    />
  );
}
