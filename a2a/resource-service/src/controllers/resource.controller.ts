import { Request, Response, NextFunction } from 'express';
import { HttpCode } from '../lib/interfaces/api.interface.js';
import { ResourceService } from '../services/resource.service.js';

/**
 * Express controller for resource-related endpoints.
 *
 * Responsibilities:
 * - Validate incoming request payloads for resource routes.
 * - Delegate business logic to {@link ResourceService}.
 * - Translate service results into HTTP responses.
 *
 * @remarks
 * Methods are intended to be used as Express route handlers.
 * All errors are forwarded to Express error middleware via `next`.
 */
export class ResourceController {
  /**
   * Service layer for resource operations and payment settlement.
   */
  private resourceService: ResourceService;

  /**
   * Creates a new {@link ResourceController}.
   *
   * @remarks
   * Instantiates its own {@link ResourceService}. For improved testability,
   * this dependency may be injected instead.
   */
  constructor() {
    this.resourceService = new ResourceService();
  }

  /**
   * GET `/api/secret`
   *
   * Returns the entitled ("secret") payload.
   *
   * If the caller is not entitled, the underlying service is expected to
   * return a 402-style Base-schema challenge payload.
   *
   * @param _req - Express request (unused).
   * @param res - Express response.
   * @param next - Express next middleware function.
   * @returns A JSON response containing the secret payload, or forwards errors to `next`.
   * @throws Forwards any thrown error to Express error middleware.
   */
  public async getSecret(_req: Request, res: Response, next: NextFunction) {
    try {
      const response = this.resourceService.getSecretPayload();
      return res.status(HttpCode.Ok).json(response);
    } catch (e) {
      next(e);
    }
  }

  /**
   * POST `/api/pay`
   *
   * Validates required payment fields, then:
   * 1) Verifies and settles the X402 payment via the facilitator SDK (service layer).
   * 2) Stores the resulting entitlement (service layer).
   *
   * Expected request body (shape):
   * - `paymentId`: string
   * - `paymentHeader`: string (SDK-specific, opaque)
   * - `paymentRequirements`: {@link PaymentRequirements}
   *
   * On missing or invalid fields, responds with HTTP 400.
   *
   * @param req - Express request containing payment fields in `req.body`.
   * @param res - Express response.
   * @param next - Express next middleware function.
   * @returns A JSON response containing the settlement result, or forwards errors to `next`.
   * @throws Forwards any thrown error to Express error middleware.
   */
  public async pay(req: Request, res: Response, next: NextFunction): Promise<Response | void> {
    try {
      const { paymentId, paymentHeader, paymentRequirements } = req.body ?? {};

      if (!paymentId || !paymentHeader || !paymentRequirements) {
        return res.status(HttpCode.BadRequest).json({ error: 'missing payment fields' });
      }

      const response = await this.resourceService.settlePayment({
        paymentId,
        paymentHeader,
        paymentRequirements,
      });

      if (!response.ok) {
        return res.status(HttpCode.BadRequest).json(response);
      }

      return res.json(response);
    } catch (e) {
      next(e);
    }
  }
}
