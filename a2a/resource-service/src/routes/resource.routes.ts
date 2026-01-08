import express from 'express';
import { ResourceController } from '../controllers/resource.controller.js';
import { requirePaidAccess } from '../lib/utils/require.util.js';

const router = express.Router();
const controller = new ResourceController();

/**
 * Resource API routes.
 *
 * Responsibilities:
 * - Define HTTP routes for protected resources.
 * - Apply X402 payment enforcement middleware where required.
 * - Delegate request handling to {@link ResourceController}.
 *
 * @remarks
 * All routes defined here are mounted under the `/api` prefix by the application
 * router registration.
 */

/**
 * GET `/api/data`
 *
 * Protected endpoint that requires successful X402 payment before access.
 *
 * Middleware chain:
 * 1) {@link requirePaidAccess} – enforces payment and issues a 402 challenge if unpaid.
 * 2) {@link ResourceController.getSecret} – returns the protected payload.
 */
router.get('/data', requirePaidAccess({ description: 'Unlock /api/data' }), controller.getSecret.bind(controller));

/**
 * POST `/api/pay`
 *
 * Settlement endpoint used to verify and settle an X402 payment.
 *
 * Delegates processing to {@link ResourceController.pay}.
 */
router.post('/pay', controller.pay.bind(controller));

export default router;
