import crypto from 'node:crypto';
import type { Request, Response, NextFunction } from 'express';
import type {
  Facilitator,
  VerifyRequest,
  X402VerifyResponse,
  X402SettleResponse,
} from '@crypto.com/facilitator-client';
import type {
  Accepts,
  PaidRecord,
  PayResult,
  RequireX402Options,
  X402Response,
} from '../../services/resource.interface.js';
import { PaymentStatus } from '../interfaces/api.interface.js';

/**
 * In-memory entitlement store keyed by an entitlement key (typically a payment id).
 *
 * @remarks
 * This is process-local and non-durable:
 * - Data is lost on process restart.
 * - Data is not shared across multiple instances.
 * If you run multiple replicas, replace this with a shared persistent store.
 */
const paid = new Map<string, PaidRecord>();

/**
 * Generates a unique payment identifier.
 *
 * @returns A payment id in the form `pay_<uuid>`.
 */
const newPaymentId = (): string => `pay_${crypto.randomUUID()}`;

/**
 * Creates an Express middleware that enforces an X402 paywall using Base discovery schema.
 *
 * Behavior:
 * - If the request is already entitled, calls `next()`.
 * - Otherwise, responds with HTTP 402 and an {@link X402Response} containing
 *   an `accepts` entry describing how to pay.
 *
 * @param options - Configuration for X402 enforcement and challenge generation.
 * @returns An Express middleware function enforcing X402 payment.
 */
export const requireX402Payment = (options: RequireX402Options) => {
  const {
    network,
    payTo,
    asset,
    maxAmountRequired,
    maxTimeoutSeconds = 300,
    description,
    mimeType = 'application/json',
    resource,
    outputSchema,
    getEntitlementKey,
  } = options;

  return (req: Request, res: Response, next: NextFunction): void => {
    const entitlementKey = (getEntitlementKey?.(req) ?? req.header('x-payment-id') ?? '').trim();

    if (entitlementKey && paid.get(entitlementKey)?.settled) {
      next();
      return;
    }

    const paymentId = newPaymentId();

    const accepts: Accepts = {
      scheme: 'exact',
      network,
      asset,
      payTo,
      maxAmountRequired,
      maxTimeoutSeconds,
      description,
      mimeType,
      resource,
      outputSchema,
      extra: { paymentId },
    };

    const response: X402Response = {
      x402Version: 1,
      error: PaymentStatus.PaymentRequired,
      accepts: [accepts],
    };

    res.status(402).json(response);
  };
};

/**
 * Verifies and settles an X402 payment and records entitlement on success.
 *
 * @remarks
 * This helper is intended to back a settlement endpoint (e.g. `POST /api/pay`).
 * On successful settlement, this function stores an in-memory entitlement record
 * keyed by `paymentId`.
 *
 * @param params - Settlement parameters.
 * @param params.facilitator - Facilitator SDK client used to verify and settle payments.
 * @param params.paymentId - Payment identifier to record as entitled after settlement.
 * @param params.paymentHeader - Encoded payment header provided by the client.
 * @param params.paymentRequirements - Requirements returned by a prior 402 challenge.
 * @returns A {@link PayResult} indicating success or a typed failure with details.
 * @throws Re-throws any error raised by the underlying SDK calls.
 */
export async function handleX402Payment(params: {
  facilitator: Facilitator;
  paymentId: string;
  paymentHeader: string;
  paymentRequirements: VerifyRequest['paymentRequirements'];
}): Promise<PayResult> {
  const { facilitator, paymentId, paymentHeader, paymentRequirements } = params;

  const body: VerifyRequest = {
    x402Version: 1,
    paymentHeader,
    paymentRequirements,
  };

  const verify = (await facilitator.verifyPayment(body)) as X402VerifyResponse;
  if (!verify.isValid) {
    return {
      ok: false,
      error: PaymentStatus.VerifyFailed,
      details: verify,
    };
  }

  const settle = (await facilitator.settlePayment(body)) as X402SettleResponse;
  if (settle.event !== 'payment.settled') {
    return {
      ok: false,
      error: PaymentStatus.SettleFailed,
      details: settle,
    };
  }

  paid.set(paymentId, { settled: true, txHash: settle.txHash, at: Date.now() });
  return {
    ok: true,
    txHash: settle.txHash,
  };
}
