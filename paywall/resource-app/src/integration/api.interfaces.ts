import type { CronosNetwork, Contract } from '@crypto.com/facilitator-client';

/**
 * X402 payment challenge returned by `GET /api/data` when access requires payment.
 *
 * @remarks
 * This interface models the Base-compatible X402 402-response body used by the API.
 * Clients are expected to:
 * - Inspect `accepts` to determine how to pay.
 * - Extract `accepts[0].extra.paymentId` and reuse it during settlement.
 */
export interface PaymentChallenge {
  /** X402 protocol version. */
  x402Version: number;

  /** Optional error code describing why payment is required. */
  error?: string;

  /** Optional payer identifier/address, if known by the server. */
  payer?: string;

  /**
   * List of accepted payment options for the requested resource.
   *
   * @remarks
   * Most implementations return a single entry (`accepts[0]`).
   */
  accepts: Array<{
    /** Indicates the accepted payment scheme type. */
    scheme: 'exact';

    /** Cronos network on which the payment must be settled. */
    network: CronosNetwork;

    /** Maximum amount required to unlock the resource (base units recommended). */
    maxAmountRequired: string;

    /** Canonical resource identifier (e.g. URL path) being protected. */
    resource: string;

    /** Human-readable description of the protected resource. */
    description: string;

    /** MIME type of the protected resource response. */
    mimeType: string;

    /** Destination address that receives the payment. */
    payTo: string;

    /** Maximum time (in seconds) to complete the payment challenge. */
    maxTimeoutSeconds: number;

    /** Asset contract used for payment. */
    asset: Contract;

    /** Optional schema describing the successful payment output shape. */
    outputSchema?: unknown;

    /**
     * Extra, implementation-specific metadata.
     *
     * @remarks
     * The server includes a `paymentId` here that must be echoed back
     * during settlement.
     */
    extra?: { paymentId?: string };
  }>;
}

/**
 * Successful response payload returned by `GET /api/data`.
 *
 * @remarks
 * This is intentionally typed as `unknown` and should be narrowed by the caller
 * to match the actual schema of the protected resource.
 */
export type GetDataResponse = unknown;

/**
 * Request payload for `POST /api/pay`.
 */
export interface PostPayRequest {
  /** Payment identifier issued in the X402 challenge. */
  paymentId: string;

  /** Encoded payment header signed by the user's wallet. */
  paymentHeader: string;

  /**
   * Payment requirements returned by the X402 challenge.
   *
   * @remarks
   * This value is typically taken directly from `challenge.accepts[0]`.
   */
  paymentRequirements: PaymentChallenge['accepts'][number];
}

/**
 * Successful response payload returned by `POST /api/pay`.
 */
export interface PostPayResponse {
  /** Settlement transaction hash, if available. */
  txHash: string;

  /** Additional implementation-specific fields. */
  [k: string]: unknown;
}

/**
 * Generic API error response shape.
 *
 * @remarks
 * This is intentionally flexible to support multiple error formats.
 */
export interface ApiErrorResponse {
  /** Optional human-readable error message. */
  message?: string;

  /** Additional implementation-specific fields. */
  [k: string]: unknown;
}

/**
 * Discriminated result returned by {@link ApiClient.getData}.
 */
export type GetDataResult =
  | { kind: GetDataKind.Ok; data: unknown }
  | { kind: GetDataKind.PaymentRequired; challenge: PaymentChallenge }
  | { kind: GetDataKind.Error; status: number; text: string };

/**
 * Discriminated result returned by {@link ApiClient.postPay}.
 */
export type PostPayResult =
  | { kind: PostPayKind.Ok; data: PostPayResponse }
  | { kind: PostPayKind.Error; status: number; data: ApiErrorResponse };

/**
 * Discriminant values returned by {@link ApiClient.getData}.
 *
 * @remarks
 * Used as stable identifiers for branching on API responses.
 */
export enum GetDataKind {
  /** Access granted and resource returned. */
  Ok = 'ok',

  /** Payment is required to access the resource. */
  PaymentRequired = 'payment_required',

  /** An unexpected error occurred. */
  Error = 'error',
}

/**
 * Discriminant values returned by {@link ApiClient.postPay}.
 */
export enum PostPayKind {
  /** Payment verified and settled successfully. */
  Ok = 'ok',

  /** Payment verification or settlement failed. */
  Error = 'error',
}

/**
 * HTTP status codes used by this client.
 *
 * @remarks
 * This enum intentionally includes only the status codes
 * the client branches on explicitly.
 */
export enum HttpStatus {
  /** Request succeeded. */
  Ok = 200,

  /** Payment is required to access the resource. */
  PaymentRequired = 402,
}
