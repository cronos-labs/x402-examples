import type { GetDataResult, PostPayRequest, PostPayResult } from './api.interfaces';
import { GetDataKind, PostPayKind, HttpStatus } from './api.interfaces';

/**
 * Options for constructing an {@link ApiClient}.
 */
export interface ApiClientOptions {
  /**
   * Base URL of the API server (e.g. `http://localhost:8787`).
   *
   * @remarks
   * This value should not include a trailing `/api` segment; routes are appended internally.
   */
  apiBase: string;
}

/**
 * Minimal client for interacting with the X402-protected API.
 *
 * Responsibilities:
 * - Fetch the protected resource endpoint (`GET /api/data`).
 * - Submit payment settlement requests (`POST /api/pay`).
 *
 * @remarks
 * This client uses the global `fetch` API and returns discriminated-union results
 * rather than throwing on non-2xx responses.
 */
export interface ApiClient {
  /**
   * Requests the protected resource.
   *
   * @param paymentId - Optional previously-settled payment id to present for entitlement.
   * @returns A discriminated union describing success, payment challenge, or error.
   */
  getData(paymentId?: string): Promise<GetDataResult>;

  /**
   * Submits a signed payment for verification and settlement.
   *
   * @param body - Payment settlement request payload.
   * @returns A discriminated union describing success or error.
   */
  postPay(body: PostPayRequest): Promise<PostPayResult>;
}

/**
 * Creates an {@link ApiClient} bound to a given API base URL.
 *
 * @param options - Client configuration options.
 * @returns An {@link ApiClient} instance.
 */
export function createApiClient(options: ApiClientOptions): ApiClient {
  const { apiBase } = options;

  return {
    /**
     * Requests the protected resource endpoint (`GET /api/data`).
     *
     * @remarks
     * If `paymentId` is provided, it is sent via the `x-payment-id` header so the
     * server can recognize a previously-settled entitlement.
     *
     * @param paymentId - Optional previously-settled payment id to present for entitlement.
     * @returns A {@link GetDataResult} describing:
     * - `kind: "ok"` when access is granted (HTTP 200)
     * - `kind: "payment_required"` when a payment challenge is returned (HTTP 402)
     * - `kind: "error"` for all other responses
     */
    async getData(paymentId?: string): Promise<GetDataResult> {
      const res = await fetch(`${apiBase}/api/data`, {
        headers: paymentId ? { 'x-payment-id': paymentId } : {},
      });

      if (res.status === HttpStatus.Ok) {
        return {
          kind: GetDataKind.Ok,
          data: await res.json(),
        };
      }

      if (res.status === HttpStatus.PaymentRequired) {
        const challenge = await res.json();
        return {
          kind: GetDataKind.PaymentRequired,
          challenge,
        };
      }

      return {
        kind: GetDataKind.Error,
        status: res.status,
        text: await res.text(),
      };
    },

    /**
     * Submits a signed payment to the settlement endpoint (`POST /api/pay`).
     *
     * @remarks
     * The response body is parsed as JSON when possible. If parsing fails, an empty
     * object is used to avoid throwing and to preserve the union result contract.
     *
     * @param body - Payment settlement request payload.
     * @returns A {@link PostPayResult} describing success (`kind: "ok"`) or error (`kind: "error"`).
     */
    async postPay(body: PostPayRequest): Promise<PostPayResult> {
      const res = await fetch(`${apiBase}/api/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const json = await res.json().catch(() => ({}));
      if (res.ok) {
        return {
          kind: PostPayKind.Ok,
          data: json,
        };
      }

      return {
        kind: PostPayKind.Error,
        status: res.status,
        data: json,
      };
    },
  };
}
