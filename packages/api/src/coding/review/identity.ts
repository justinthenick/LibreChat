import { z } from 'zod';

export const reviewRunIdSchema = z
  .string()
  .uuid()
  .transform((id) => id.toLowerCase());
