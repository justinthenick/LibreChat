import { useEffect, useRef, useState } from 'react';
import { isAxiosError } from 'axios';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { dataService, MutationKeys, QueryKeys } from 'librechat-data-provider';
import type { PreviewJob, PreviewReply } from 'librechat-data-provider';
import type { PreviewSession } from './session';
import { acceptJob, newSession, readSession, settled, writeSession } from './session';

export function previewFailure(error: unknown): 'disabled' | 'unavailable' | 'identity' | 'access' {
  if (error instanceof Error && error.message === 'preview_identity') return 'identity';
  if (isAxiosError<PreviewReply>(error)) {
    const reply = error.response?.data;
    if (reply?.ok === false && reply.error === 'preview_jobs_disabled') return 'disabled';
    if ([401, 403, 404].includes(error.response?.status ?? 0)) return 'access';
  }
  return 'unavailable';
}

/** Mount once per authenticated owner. No cached result is trusted after reopening. */
export function usePreviewJob(owner: string) {
  const client = useQueryClient();
  const [session, setSession] = useState(() => readSession(owner));
  const [failure, setFailure] = useState<ReturnType<typeof previewFailure> | null>(null);
  const [busy, setBusy] = useState(false);
  const active = useRef(true);
  const locked = useRef(false);
  const latest = useRef<PreviewJob>();
  const current = useRef(session);
  const queryKey = [QueryKeys.previewJob, owner, session?.jobId];

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      client.removeQueries({ queryKey: [QueryKeys.previewJob, owner] });
    };
  }, [client, owner]);

  const save = (value: PreviewSession | null) => {
    writeSession(owner, value);
    current.current = value;
    setSession(value);
  };
  const query = useQuery({
    queryKey,
    queryFn: async () => {
      if (!session?.jobId) throw new Error('preview_missing');
      const job = acceptJob(
        await dataService.getPreviewJob(session.jobId),
        session,
        latest.current,
      );
      if (!active.current || current.current?.generation !== session.generation)
        throw new Error('preview_identity');
      latest.current = job;
      if (!locked.current) setFailure(null);
      return job;
    },
    enabled: !!session?.jobId,
    cacheTime: 0,
    retry: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    refetchInterval: (job, observer) =>
      (settled(job) && !failure) ||
      (observer.state.error && previewFailure(observer.state.error) !== 'unavailable')
        ? false
        : 2000,
  });
  const start = useMutation({
    mutationKey: [MutationKeys.previewStart, owner],
    mutationFn: async (value: PreviewSession) => {
      if (!active.current) throw new Error('preview_owner_changed');
      return acceptJob(await dataService.startPreviewJob(value.request), value);
    },
    retry: false,
  });
  const cancel = useMutation({
    mutationKey: [MutationKeys.previewCancel, owner],
    mutationFn: async (value: PreviewSession) => {
      if (!value.jobId) throw new Error('preview_missing');
      const before = acceptJob(await dataService.getPreviewJob(value.jobId), value, latest.current);
      if (!active.current) throw new Error('preview_owner_changed');
      latest.current = before;
      return acceptJob(await dataService.cancelPreviewJob(value.jobId), value, latest.current);
    },
    retry: false,
  });

  const run = async (operation: () => Promise<void>) => {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setFailure(null);
    try {
      await operation();
    } catch (error) {
      if (active.current) setFailure(previewFailure(error));
    } finally {
      locked.current = false;
      if (active.current) setBusy(false);
    }
  };

  return {
    session,
    job: query.data,
    busy,
    loading: query.isFetching,
    failure: failure ?? (query.isError ? previewFailure(query.error) : null),
    refresh: () => {
      setFailure(null);
      void query.refetch();
    },
    start: (prompt: string, repository: string) =>
      run(async () => {
        if (current.current?.jobId) return;
        const value = current.current ?? (await newSession(prompt, repository));
        if (!active.current) return;
        save(value);
        const job = await start.mutateAsync(value);
        if (!active.current) return;
        save({ ...value, jobId: job.job_id });
        latest.current = job;
        client.setQueryData([QueryKeys.previewJob, owner, job.job_id], job);
      }),
    cancel: () =>
      run(async () => {
        const value = current.current;
        if (!value?.jobId) return;
        const job = await cancel.mutateAsync(value);
        if (!active.current) return;
        latest.current = job;
        client.setQueryData(queryKey, job);
        void client.invalidateQueries({ queryKey });
      }),
    reset: () => {
      if (locked.current || query.isError || !settled(query.data)) return;
      save(null);
      latest.current = undefined;
      setFailure(null);
      client.removeQueries({ queryKey });
    },
  };
}
