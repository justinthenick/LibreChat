const express = require('express');
const { createPreviewJobHandlers } = require('@librechat/api/coding');

function createPreviewRouter(options = {}) {
  const router = express.Router();
  const handlers = createPreviewJobHandlers(options);
  router.post('/jobs', handlers.start);
  router.get('/jobs/:jobId', handlers.get);
  router.post('/jobs/:jobId/cancel', handlers.cancel);
  router.post('/jobs/:jobId/resume', handlers.unsupported);
  router.post('/jobs/:jobId/steer', handlers.unsupported);
  return router;
}

module.exports = createPreviewRouter({
  enabled: process.env.CODING_OPENHANDS_PREVIEW === 'true',
});
module.exports.createPreviewRouter = createPreviewRouter;
