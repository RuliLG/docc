import { AlertOctagonIcon } from "lucide-react";

export default function ErrorScreen({ error }: { error: string }) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background flex-col gap-4">
          <AlertOctagonIcon className="w-10 h-10 text-destructive" />
          <h2 className="text-foreground font-bold text-2xl">There was an error checking system requirements</h2>
          <p className="text-foreground text-lg">{error}</p>
      </div>
    );
  }
