import { z } from 'zod';

export const reviewRunIdSchema: z.ZodType<string> = z
  .string()
  .uuid()
  .transform((id) => id.toLowerCase());
