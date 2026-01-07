/**
 * Enumeration of HTTP status codes used by the API.
 *
 * @remarks
 * This enum centralizes HTTP status codes to:
 * - Avoid magic numbers in controllers and services.
 * - Ensure consistent usage and naming across the codebase.
 *
 * Values map directly to standard HTTP status codes.
 */
export enum HttpCode {
  /** Request succeeded. */
  Ok = 200,

  /** Resource successfully created. */
  Created = 201,

  /** Request succeeded with no response body. */
  NoContent = 204,

  /** Request was malformed or missing required parameters. */
  BadRequest = 400,

  /** Authentication is required or has failed. */
  Unauthorized = 401,

  /** Requested resource was not found. */
  NotFound = 404,

  /** Payment is required to access the requested resource. */
  PaymentRequired = 402,

  /** Request was well-formed but could not be processed. */
  UnproccessableEntity = 422,

  /** An unexpected server-side error occurred. */
  InternalServerError = 500,

  /** Service is temporarily unavailable. */
  ServiceUnavailable = 503,

  /** Client has sent too many requests in a given amount of time. */
  TooManyRequests = 429,
}

/**
 * Enumeration of payment lifecycle statuses.
 *
 * @remarks
 * These values are used as stable, machine-readable identifiers for
 * payment verification and settlement outcomes.
 */
export enum PaymentStatus {
  /** Payment verification failed. */
  VerifyFailed = 'verify_failed',

  /** Payment verification succeeded. */
  VerifySuccess = 'verify_success',

  /** Payment settlement failed. */
  SettleFailed = 'settle_failed',

  /** Payment settlement succeeded. */
  SettleSuccess = 'settle_success',

  /** Payment is required before the resource can be accessed. */
  PaymentRequired = 'payment_required',
}
