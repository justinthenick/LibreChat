import { createFileRoute } from '@tanstack/react-router';
import { handleDeploymentControl } from '@/server/deploymentProxy';

const proxy = ({ request }: { request: Request }) => handleDeploymentControl(request);

export const Route = createFileRoute('/deployment-control/$')({
  server: {
    handlers: {
      GET: proxy,
      HEAD: proxy,
      POST: proxy,
    },
  },
});
