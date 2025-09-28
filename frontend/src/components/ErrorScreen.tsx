import { AlertOctagonIcon } from "lucide-react";

interface ErrorScreenProps {
    error: string;
    title: string;
    children?: React.ReactNode;
}

export default function ErrorScreen({ error, title, children }: ErrorScreenProps) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background flex-col gap-4">
          <AlertOctagonIcon className="w-10 h-10 text-destructive" />
          <h2 className="text-foreground font-bold text-2xl">{title}</h2>
          <p className="text-foreground text-lg">{error}</p>
          {children}
      </div>
    );
  }
