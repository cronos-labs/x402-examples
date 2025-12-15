import { useCallback, useMemo, useState } from 'react';
import { Facilitator } from '@crypto.com/facilitator-client';
import { createApiClient } from '../integration/api';
import type { PaymentChallenge } from '../integration/api.interfaces';
import { ensureWallet } from '../utils/wallet';
import { ensureCronosChain } from '../utils/cronos';

/**
 * Options for configuring the X402 payment flow hook.
 */
export interface UseX402FlowOptions {
  /**
   * Base URL of the API server (e.g. `http://localhost:8787`).
   */
  apiBase: string;
}

/**
 * Result returned by {@link useX402Flow}.
 *
 * Responsibilities:
 * - Expose UI-friendly state for the current payment/access flow.
 * - Provide helper functions to trigger and retry the protected fetch.
 *
 * @remarks
 * - `status` is intended for display to end users.
 * - `data` is a serialized representation of the protected payload.
 */
export interface UseX402FlowResult {
  /** Human-readable status describing the current step of the flow. */
  status: string;

  /** Serialized response data from the protected endpoint. */
  data: string;

  /** Payment identifier associated with the last successful settlement. */
  paymentId: string;

  /**
   * Requests the protected resource.
   *
   * @param existingPaymentId - Optional previously-settled payment id to reuse.
   * @returns Resolves when the request (and any required payment flow) completes.
   * @throws If an unexpected API response is encountered.
   */
  fetchSecret: (existingPaymentId?: string) => Promise<void>;

  /**
   * Retries the protected request using the last known `paymentId`, if present.
   *
   * @returns Resolves when the request completes (or no-ops if `paymentId` is empty).
   */
  retryWithPaymentId: () => Promise<void>;
}

/**
 * React hook implementing an X402 payment + access flow.
 *
 * Flow overview:
 * 1) Attempt to fetch the protected resource.
 * 2) If access is granted, store the returned payload.
 * 3) If a 402/X402 challenge is returned, prompt the user to sign a payment.
 * 4) POST the signed payment to `/api/pay` for verification and settlement.
 * 5) Retry the protected request using the settled payment id.
 *
 * @param options - Hook configuration options.
 * @returns State and helpers for driving the X402 flow from a UI.
 */
export function useX402Flow(options: UseX402FlowOptions): UseX402FlowResult {
  const { apiBase } = options;

  /**
   * API client memoized by base URL.
   */
  const api = useMemo(() => createApiClient({ apiBase }), [apiBase]);

  const [status, setStatus] = useState<string>('');
  const [data, setData] = useState<string>('');
  const [paymentId, setPaymentId] = useState<string>('');

  /**
   * Handles an X402 payment challenge by guiding the user through wallet-based payment.
   *
   * Responsibilities:
   * - Validate the challenge payload.
   * - Ensure wallet connection and correct Cronos network.
   * - Generate and sign an EIP-3009 payment header.
   * - Submit the payment for verification and settlement.
   * - Retry the protected request on success.
   *
   * @param challenge - X402 payment challenge returned by the API.
   * @returns Resolves after attempting settlement and (if successful) re-fetching the resource.
   * @throws If the challenge payload is malformed or incomplete.
   */
  const handlePaymentChallenge = useCallback(
    async (challenge: PaymentChallenge) => {
      const accepts0 = challenge.accepts?.[0];
      if (!accepts0) throw new Error('Invalid x402 response: accepts[0] missing');

      const nextPaymentId = accepts0.extra?.paymentId;
      if (!nextPaymentId) {
        throw new Error('Invalid x402 response: accepts[0].extra.paymentId missing');
      }

      const provider = await ensureWallet();
      await ensureCronosChain(accepts0.network);
      const signer = await provider.getSigner();

      setStatus('Signing EIP-3009 payment header in wallet...');

      const fac = new Facilitator({ network: accepts0.network });
      const paymentHeader = await fac.generatePaymentHeader({
        to: accepts0.payTo,
        value: accepts0.maxAmountRequired,
        asset: accepts0.asset,
        signer,
        validBefore: Math.floor(Date.now() / 1000) + accepts0.maxTimeoutSeconds,
        validAfter: 0,
      });

      setStatus('Sending /api/pay (verify + settle) ...');

      const payRes = await api.postPay({
        paymentId: nextPaymentId,
        paymentHeader,
        paymentRequirements: accepts0,
      });

      if (payRes.kind === 'error') {
        setStatus(`Payment failed: ${JSON.stringify(payRes.data)}`);
        return;
      }

      setPaymentId(nextPaymentId);
      setStatus(`Payment settled. txHash=${payRes.data.txHash ?? '—'}`);

      await fetchSecret(nextPaymentId);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [api]
  );

  /**
   * Requests the protected resource, optionally using an existing payment id.
   *
   * @param existingPaymentId - Previously-settled payment id to reuse, if available.
   * @returns Resolves when the request completes (including any required payment flow).
   * @throws If an unexpected API response is encountered.
   */
  const fetchSecret = useCallback(
    async (existingPaymentId?: string) => {
      setStatus('Requesting /api/data ...');
      setData('');

      const result = await api.getData(existingPaymentId);

      if (result.kind === 'ok') {
        setData(JSON.stringify(result.data, null, 2));
        setStatus('Access granted');
        return;
      }

      if (result.kind === 'payment_required') {
        setStatus(`Payment required: ${result.challenge.error ?? 'payment_required'}`);
        await handlePaymentChallenge(result.challenge);
        return;
      }

      throw new Error(`Unexpected response: ${result.status} ${result.text}`);
    },
    [api, handlePaymentChallenge]
  );

  /**
   * Retries the protected request using the last successful payment id.
   *
   * @returns Resolves when the request completes (or no-ops if `paymentId` is empty).
   */
  const retryWithPaymentId = useCallback(async () => {
    if (!paymentId) return;
    await fetchSecret(paymentId);
  }, [paymentId, fetchSecret]);

  return { status, data, paymentId, fetchSecret, retryWithPaymentId };
}
