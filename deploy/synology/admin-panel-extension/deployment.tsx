import { createFileRoute } from '@tanstack/react-router';

const configuredPort = import.meta.env.VITE_DEPLOYMENT_SETTINGS_PORT || '3210';

export const Route = createFileRoute('/_app/deployment')({
  component: DeploymentPage,
});

function DeploymentPage() {
  const deploymentUrl = `${window.location.protocol}//${window.location.hostname}:${configuredPort}/`;

  return (
    <section className="flex min-h-0 flex-1 flex-col gap-4 p-6">
      <div>
        <h1 className="text-xl font-semibold text-(--cui-color-title-default)">Deployment</h1>
        <p className="mt-1 text-sm text-(--cui-color-text-muted)">
          Synology host, environment, secret, service health and rollback controls. These controls remain
          isolated from LibreChat application administration and are executed through the restricted host worker.
        </p>
      </div>

      <div className="min-h-[640px] flex-1 overflow-hidden rounded-lg border border-(--cui-color-stroke-default) bg-(--cui-color-background-panel)">
        <iframe
          title="Synology Deployment Control"
          src={deploymentUrl}
          className="h-full min-h-[640px] w-full border-0"
          referrerPolicy="no-referrer"
        />
      </div>
    </section>
  );
}
