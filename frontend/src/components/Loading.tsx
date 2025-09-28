export default function Loading({ title, description }: { title: string, description: string }) {
  return (
    <div className="h-screen w-full flex items-center justify-center bg-background flex-col gap-4">
        <div className="spinner text-foreground"></div>
        <h2 className="text-foreground font-bold text-2xl">{title}</h2>
        <p className="text-foreground text-lg">{description}</p>
    </div>
  );
}
