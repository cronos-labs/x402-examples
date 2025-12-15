# Resource App

The **Example Resource Frontend** is a reference client that demonstrates how to access x402-protected HTTP resources.
It interacts with an x402-enabled backend by handling `402 Payment Required` challenges, signing payment authorizations, and retrying requests once payment is settled.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [Application Flow](#application-flow)
- [Example Usage](#example-usage)
- [Technologies Used](#technologies-used)
- [License](#license)

## Overview

The **X402 Example Frontend** showcases the client-side flow required to consume APIs protected by the [x402 payment protocol](https://github.com/coinbase/x402).

The application:

1. Requests a protected backend resource.
2. Detects a `402 Payment Required` response.
3. Parses the x402 challenge metadata (including `paymentId`).
4. Prompts the user to sign an **EIP-3009 authorization** (`exact` scheme) in their wallet.
5. Sends the signed authorization to the backend (`POST /api/pay`) for verification + settlement.
6. Retries the original request with `x-payment-id` and receives the protected content.

This frontend is intended for **local demos, development, and reference implementations**.

## Features

**Automatic 402 Handling** — detects and parses x402 challenges.  
**Wallet Integration** — signs EIP-3009 (`exact` scheme) authorizations.  
**Backend Settlement Flow** — backend verifies + settles via the facilitator.  
**Retry Logic** — replays the original request after successful settlement using `x-payment-id`.  
**Network-Aware** — switches the wallet chain based on the challenge (`cronos-testnet` / `cronos-mainnet`).  
**Minimal UI** — focuses on protocol flow rather than styling.

> Note: This client expects the backend to expose `GET /api/data` and `POST /api/pay`, and to include `accepts[0].extra.paymentId` in the 402 challenge payload.

## Setup and Installation

### Prerequisites

- Node.js **v20+**
- npm or yarn
- MetaMask (or compatible EVM wallet)
- Access to the example backend

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/cronos-labs/x402-examples/paywall/resource-app
   cd resource-app
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

   # Backend API
   VITE_API_BASE=http://localhost:8787
   ```

5. **Run the Development Server**

   ```bash
   npm run dev
   ```

6. **Production Build**

   ```bash
   npm run build
   npm run preview
   ```

## Environment Variables

| Variable        | Description                            |
| --------------- | -------------------------------------- |
| `VITE_API_BASE` | Base URL of the x402-protected backend |

## Application Flow

```
Client
  │
  │  GET /api/data
  ▼
Backend
  │
  │  402 Payment Required (x402 challenge + paymentId)
  ▼
Client
  │
  │  Sign EIP-3009 authorization (wallet)
  ▼
Backend (/api/pay)
  │
  │  Verify + settle (facilitator)
  ▼
Client
  │
  │  Retry GET /api/data with x-payment-id
  ▼
Protected Content
```

Entitlement is enforced server-side; the frontend only stores `paymentId` to support retry UX.

## Example Usage

### Access Protected Resource

```ts
const res = await fetch(`${API_BASE}/api/data`);

if (res.status === 402) {
  // parse x402 challenge and initiate payment flow
}
```

### Retry After Settlement

```ts
await fetch(`${API_BASE}/api/data`, {
  headers: {
    'x-payment-id': paymentId,
  },
});
```

## Technologies Used

- **TypeScript**
- **Vite**
- **React**
- **ethers**
- **@crypto.com/facilitator-client**
- **x402 protocol**
- **EIP-3009 (Exact Scheme)**

## License

This project is licensed under the **MIT License**.
