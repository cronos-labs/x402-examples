import type {
  Contract,
  CronosNetwork,
  PaymentRequirements,
  X402OutputSchema,
  X402SettleResponse,
  X402VerifyResponse,
} from '@crypto.com/facilitator-client';
import type { Request } from 'express';

/**
 * Generic field definition used to describe input/output schemas.
 *
 * @remarks
 * This is intentionally flexible to support schema-like shapes (e.g. JSON Schema–style
 * objects) without coupling this project to a specific schema standard.
 */
export interface FieldDef {
  /** Primitive or structural type name (e.g. `"string"`, `"object"`). */
  type?: string;
  /** Whether the field is required; may be a boolean or a list of required keys for objects. */
  required?: boolean | string[];
  /** Human-readable description of the field. */
  description?: string;
  /** Set of allowed string values when the field is enumerable. */
  enum?: string[];
  /** Nested object properties keyed by property name. */
  properties?: Record<string, FieldDef>;
}

/**
 * Base-compatible "accepts" entry for X402 challenges.
 *
 * @remarks
 * This interface models the exact shape expected by x402scan and Base-schema consumers.
 * Any additions should be made using {@link Accepts.extra} to preserve compatibility.
 */
export interface Accepts {
  /** Indicates the accepted payment scheme type. */
  scheme: 'exact';

  /**
   * Target Cronos network for settlement.
   *
   * @remarks
   * Although {@link CronosNetwork} is used here, deployments may treat this as a string
   * for forward compatibility with future network identifiers.
   */
  network: CronosNetwork;

  /** Maximum amount required to access the resource (typically in base units). */
  maxAmountRequired: string;

  /** Canonical resource identifier (e.g. URL path) being protected. */
  resource: string;

  /** Human-readable description of the protected resource. */
  description: string;

  /** MIME type of the protected resource response (e.g. `application/json`). */
  mimeType: string;

  /** Destination address that receives the payment. */
  payTo: string;

  /** Maximum time (in seconds) the payer has to fulfill the payment challenge. */
  maxTimeoutSeconds: number;

  /** Asset/denomination identifier used for payment. */
  asset: string;

  /** Optional schema describing the successful payment output shape. */
  outputSchema?: X402OutputSchema;

  /**
   * Extra, implementation-specific metadata.
   *
   * @remarks
   * Use this for non-standard fields to avoid breaking Base-schema compatibility.
   */
  extra?: Record<string, unknown>;
}

/**
 * Base-compatible X402 402-response body.
 *
 * @remarks
 * This is the payload returned when a client must complete an X402 payment challenge.
 */
export interface X402Response {
  /** X402 protocol version. */
  x402Version: number;

  /** Optional error message describing the reason for the challenge/failure. */
  error?: string;

  /** List of accepted payment options for the challenged resource. */
  accepts?: Accepts[];

  /** Optional payer identifier/address, if known. */
  payer?: string;
}

/**
 * Parameters required to settle an X402 payment.
 */
export interface PayParams {
  /** Unique identifier for the payment attempt. */
  paymentId: string;

  /** Encoded payment header provided by the client (SDK-specific, opaque). */
  paymentHeader: string;

  /** Requirements returned by a prior 402 challenge (SDK-specific). */
  paymentRequirements: PaymentRequirements;
}

/**
 * Stored record representing a settled (or attempted) payment.
 */
export interface PaidRecord {
  /** Whether settlement succeeded. */
  settled: boolean;

  /** Optional settlement transaction hash, if available. */
  txHash?: string;

  /** Unix timestamp (milliseconds) when the record was stored. */
  at: number;
}

/**
 * Result of a payment attempt.
 *
 * @remarks
 * - On success, `ok: true` may include an optional `txHash`.
 * - On failure, `ok: false` includes a stable error code and SDK response details.
 */
export type PayResult =
  | { ok: true; txHash?: string }
  | { ok: false; error: 'verify_failed'; details: X402VerifyResponse }
  | { ok: false; error: 'settle_failed'; details: X402SettleResponse };

/**
 * Options for configuring X402 protection middleware.
 *
 * @remarks
 * These options define the challenge parameters (asset, amount, timeout) and allow
 * callers to customize how entitlements are keyed per-request.
 */
export interface RequireX402Options {
  /** Cronos network used for verification and settlement. */
  network: CronosNetwork;

  /** Destination address that receives the payment. */
  payTo: string;

  /** Asset contract used for payment. */
  asset: Contract;

  /** Maximum amount required (recommended to use base units). */
  maxAmountRequired: string;

  /**
   * Maximum time (in seconds) to allow completion of the payment challenge.
   *
   * @defaultValue Implementation-defined (if omitted).
   */
  maxTimeoutSeconds?: number;

  /** Human-readable description of the protected resource. */
  description: string;

  /**
   * MIME type of the protected resource response.
   *
   * @defaultValue `"application/json"` (commonly used, if implementation applies a default).
   */
  mimeType?: string;

  /** Canonical resource identifier (e.g. URL path) being protected. */
  resource: string;

  /** Optional schema describing the successful payment output shape. */
  outputSchema?: Accepts['outputSchema'];

  /**
   * Computes a stable entitlement key for the current request.
   *
   * @param req - Express request being authorized.
   * @returns A stable key used to store/lookup entitlements, or `undefined` to disable custom keying.
   */
  getEntitlementKey?: (req: Request) => string | undefined;
}
