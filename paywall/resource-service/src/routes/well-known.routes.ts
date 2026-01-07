import express from 'express';
import { WellKnownController } from '../controllers/well-known.controller.js';

const router = express.Router();
const controller = new WellKnownController();

/**
 * Well-known discovery routes (A2A Agent Card).
 *
 * Mounted at `/.well-known` by route registration.
 */
router.get('/agent-card.json', controller.getAgentCard.bind(controller));

export default router;
