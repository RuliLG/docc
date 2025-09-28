import { ServiceStatus as ServiceStatusType } from "@/types/system-check";
import { AlertOctagonIcon, CheckCircleIcon, XCircleIcon } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "../ui/alert";

export default function ServiceStatus({ name, status }: { name: string, status: ServiceStatusType }) {
    const isConfigured = status.configured || status.accessible;

    return (
      <div>
        <div className="flex items-center justify-between">
          <span className="font-medium">{name}</span>
          {isConfigured ? <CheckCircleIcon className="w-4 h-4 text-primary" /> : <XCircleIcon className="w-4 h-4 text-destructive" />}
        </div>
        <div className="space-y-2 mt-4">
          {status.version && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Version:</span>
              <span className="text-sm">{status.version}</span>
            </div>
          )}
          {status.installed !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Installed:</span>
              { status.installed && <CheckCircleIcon className="w-4 h-4 text-primary" /> }
              { !status.installed && <XCircleIcon className="w-4 h-4 text-destructive" /> }
            </div>
          )}
          {status.configured !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Configured:</span>
              { status.configured && <CheckCircleIcon className="w-4 h-4 text-primary" /> }
              { !status.configured && <XCircleIcon className="w-4 h-4 text-destructive" /> }
            </div>
          )}
          {status.api_key_set !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">API Key:</span>
              { status.api_key_set && <CheckCircleIcon className="w-4 h-4 text-primary" /> }
              { !status.api_key_set && <XCircleIcon className="w-4 h-4 text-destructive" /> }
            </div>
          )}
          {status.accessible !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Accessible:</span>
              { status.accessible && <CheckCircleIcon className="w-4 h-4 text-primary" /> }
              { !status.accessible && <XCircleIcon className="w-4 h-4 text-destructive" /> }
            </div>
          )}
          {status.error && (
            <Alert variant="destructive">
              <AlertOctagonIcon className="w-4 h-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{status.error}</AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    );
  };
