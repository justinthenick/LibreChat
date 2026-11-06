const { SystemCapabilities } = require('@librechat/data-schemas');
const { createReviewRouter, getDevelopmentReviewConfig } = require('@librechat/api/coding');
const { requireJwtAuth, checkBan } = require('~/server/middleware');
const { requireCapability } = require('~/server/middleware/roles/capabilities');

// Only the explicit development environment can produce enabled configuration.
module.exports = createReviewRouter(getDevelopmentReviewConfig(process.env), {
  authenticate: requireJwtAuth,
  checkBan,
  authorize: requireCapability(SystemCapabilities.ACCESS_ADMIN),
});
