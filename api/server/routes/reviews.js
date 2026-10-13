const { createReviewRouter } = require('@librechat/api/coding');
const { requireJwtAuth, checkBan } = require('~/server/middleware');

// Factory only: deliberately not registered in the application route index.
module.exports = (config) => createReviewRouter(config, { authenticate: requireJwtAuth, checkBan });
