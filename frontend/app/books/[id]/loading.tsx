export default function BookDetailLoading() {
  return (
    <div className="space-y-8">
      <div className="h-96 animate-pulse rounded-[34px] border border-white/10 bg-panel/50" />
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <div className="h-52 animate-pulse rounded-[28px] border border-white/10 bg-panel/50" />
        <div className="h-52 animate-pulse rounded-[28px] border border-white/10 bg-panel/50" />
        <div className="h-52 animate-pulse rounded-[28px] border border-white/10 bg-panel/50" />
      </div>
    </div>
  );
}
