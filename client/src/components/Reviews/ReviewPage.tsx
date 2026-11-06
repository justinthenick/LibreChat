import { useReviewConfigQuery } from '~/data-provider';
import { useAuthContext } from '~/hooks/AuthContext';
import ReviewPanel from './ReviewPanel';

/** The server's development gate and current session decide availability. */
export default function ReviewPage() {
  const { user, isAuthenticated, isAuthReady } = useAuthContext();
  const identity =
    isAuthenticated && isAuthReady && user?.id
      ? { userId: user.id, tenantId: user.tenantId }
      : undefined;
  const { data, isSuccess } = useReviewConfigQuery(identity);
  const enabled = Boolean(identity && isSuccess && data?.enabled === true);
  return <ReviewPanel enabled={enabled} repositories={enabled ? (data?.repositories ?? []) : []} />;
}
