import type { Request, Response, NextFunction } from 'express';
import { HttpCode } from '../lib/interfaces/api.interface.js';
import { WellKnownService } from '../services/well-known.service.js';

export class WellKnownController {
  private service: WellKnownService;

  constructor() {
    this.service = new WellKnownService();
  }

  /**
   * GET `/.well-known/agent-card.json`
   *
   * Public discovery endpoint that advertises x402-gated resources.
   */
  public async getAgentCard(_req: Request, res: Response, next: NextFunction) {
    try {
      const card = this.service.getAgentCard();
      return res.status(HttpCode.Ok).json(card);
    } catch (e) {
      next(e);
    }
  }
}
