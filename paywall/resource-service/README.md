# Resource Service

The **Example Resource Service** is a minimal Express-based API that demonstrates how to protect HTTP resources using the x402 payment protocol.
It integrates the `@crypto.com/facilitator-client` to require on-chain ERC-20 payments (EIP-3009, `exact` scheme) before granting access to protected endpoints.

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Setup and Installation](#setup-and-installation)
* [Environment Variables](#environment-variables)
* [API Endpoints](#api-endpoints)

  * [Protected Resource](#protected-resource)
  * [Payment Settlement](#payment-settlement)
* [Architecture Overview](#architecture-overview)
* [Example Usage](#example-usage)

  * [Access Protected Resource](#access-protected-resource)
  * [Settle Payment](#settle-payment)
* [Technologies Used](#technologies-used)
* [License](#license)

## Overview

The **X402 Example Backend Service** showcases a simple merchant-style backend that protects API routes behind x402 payments.

When a client accesses a protected endpoint:

1. The server responds with a **402 Payment Required** challenge (Base-compatible schema).
2. The client submits payment via an x402-compatible wallet.
3. The backend verifies and settles the payment using a facilitator.
4. The client retries the request and receives the protected content.

This backend is intended for **local development, demos, and reference implementations**, not production-scale persistence.

## Features

**x402-Protected Endpoints** — HTTP routes gated by on-chain payments.
**Middleware-Based Enforcement** — payment checks handled via Express middleware.
**Exact Scheme Support** — uses EIP-3009 (`transferWithAuthorization`).
**Stateless Entitlement** — in-memory settlement tracking (no database).
**Cronos Network Support** — Cronos Testnet and Mainnet via configuration.

## Setup and Installation

### Prerequisites

* Node.js **v20+**
* npm or yarn
* Access to a **Cronos RPC endpoint** (Testnet or Mainnet)
* An x402-compatible wallet or client

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/cronos-labs/x402-examples/paywall/resource-service
   cd resource-service
   ```

2. **Install Dependencies**

   ```bash
   npm install
   ```

3. **Create Environment Variables**

   ```bash
   cp .env.example .env
   ```

4. **Example `.env` file**

   ```bash
   NODE_ENV=development
   PORT=8787

   # Network
   NETWORK=cronos-testnet

   # Merchant configuration
   MERCHANT_ADDRESS=0xMERCHANT_ADDRESS
   PRICE_BASE_UNITS=1000000   # 1 USDC (6 decimals)

   # Public resource URL (used in x402 challenge)
   PUBLIC_RESOURCE_URL=http://localhost:8787/api/data
   ```

5. **Run the Development Server**

   ```bash
   npm run dev
   ```

6. **Production Build**

   ```bash
   npm run build
   npm start
   ```

## API Endpoints

### Protected Resource

**GET** `/api/data`

Returns a protected payload.
If the client has not paid, the server responds with **402 Payment Required** and an x402 challenge.

**Response (Paid)**

```json
{
  "ok": true,
  "response": "paid content unlocked"
}
```

**Response (Unpaid)**

```json
{
  "x402Version": 1,
  "error": "payment_required",
  "accepts": [
    {
      "scheme": "exact",
      "network": "cronos-testnet",
      "payTo": "0xMERCHANT_ADDRESS",
      "asset": "0x...",
      "maxAmountRequired": "1000000",
      "maxTimeoutSeconds": 300,
      "description": "Unlock /api/data",
      "resource": "http://localhost:8787/api/data"
    }
  ]
}
```

### Payment Settlement

**POST** `/api/pay`

Verifies and settles an x402 payment using the facilitator SDK.
On success, the entitlement is recorded in memory and subsequent requests to the protected endpoint are allowed.

**Headers**

```
Content-Type: application/json
```

**Body Example**

```json
{
  "paymentId": "pay_123",
  "paymentHeader": "<base64-json>",
  "paymentRequirements": {
    "scheme": "exact",
    "network": "cronos-testnet",
    "payTo": "0xMERCHANT_ADDRESS",
    "asset": "0x...",
    "maxAmountRequired": "1000000",
    "maxTimeoutSeconds": 300
  }
}
```

**Response**

```json
{
  "ok": true,
  "txHash": "0xabc123..."
}
```

## Architecture Overview

```
src/
├── routes/
│   └── resource.routes.ts      # API routes
├── controllers/
│   └── resource.controller.ts  # HTTP request handling
├── services/
│   └── resource.service.ts     # Payment settlement + business logic
├── lib/
│   └── middlewares/
│       └── require.middleware.ts  # x402 enforcement middleware
├── index.ts                    # Express app entry point
└── config/
    └── x402.ts                 # Centralized x402 configuration
```

## Example Usage

### Access Protected Resource

```bash
curl -i http://localhost:8787/api/data
```

Returns `402 Payment Required` until paid.



### Settle Payment

```bash
curl -X POST http://localhost:8787/api/pay \
  -H "Content-Type: application/json" \
  -d "$PAYMENT_BODY"
```

After settlement, retry the protected request with the same payment context.



## Technologies Used

* **Node.js** + **TypeScript**
* **Express**
* **@crypto.com/facilitator-client**
* **x402 protocol**
* **EIP-3009 (Exact Scheme)**
* **dotenv**

## License

This project is licensed under the **MIT License**.

