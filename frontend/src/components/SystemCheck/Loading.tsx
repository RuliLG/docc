export default function Loading() {
  return (
    <div className="h-screen w-full flex items-center justify-center bg-background flex-col gap-4">
        <div className="spinner text-foreground"></div>
        <h2 className="text-foreground font-bold text-2xl">Checking system requirements</h2>
        <p className="text-foreground text-lg">Validating that AI CLI tools and TTS services are available...</p>
    </div>
  );
}
