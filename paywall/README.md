# X402 Paywalled Resource Monorepo

This repository contains a complete **end-to-end example** of using the **x402 payment protocol** to protect HTTP resources and consume them from a frontend client.

It includes:

- A **Resource Service** (backend) that exposes x402-protected endpoints
- A **Resource App** (frontend) that handles `402 Payment Required`, signs payments, and retries requests

Together, these projects demonstrate the **full client ↔ merchant flow** for x402-based paywalls.

## Repository Structure

```
.
├── resource-service/   # x402-protected backend (Express)
├── resource-app/       # x402-enabled frontend (Vite + React)
└── README.md           # Monorepo documentation (this file)
```

Each package has its **own README** with detailed setup and implementation notes.

## Overview

The flow implemented in this monorepo is:

1. The frontend requests a protected backend endpoint.
2. The backend responds with **402 Payment Required** and an x402 challenge.
3. The frontend parses the challenge and prompts the user to sign an **EIP-3009 authorization**.
4. The frontend submits the signed authorization to the backend.
5. The backend verifies and settles the payment via the facilitator.
6. The frontend retries the original request using `x-payment-id`.
7. The backend returns the protected resource.

This setup is intended for **local development, demos, and reference implementations**.

## Prerequisites

Before running the monorepo locally, ensure you have:

- **Node.js v20+**
- **npm** or **yarn**
- An **EVM-compatible wallet** (e.g. MetaMask)
- Test funds on **Cronos Testnet**
- A local or public Cronos RPC endpoint

## Running the Full Stack Locally

### 1. Clone the Repository

```bash
git clone https://github.com/cronos-labs/x402-examples.git
cd x402-examples/paywall
```

### 2. Start the Backend (Resource Service)

```bash
cd resource-service
npm install
cp .env.example .env
```

Update `.env` with your merchant configuration:

```bash
NODE_ENV=development
PORT=8787

NETWORK=cronos-testnet
MERCHANT_ADDRESS=0xYOUR_MERCHANT_ADDRESS
PRICE_BASE_UNITS=1000000

PUBLIC_RESOURCE_URL=http://localhost:8787/api/data
```

Run the service:

```bash
npm run dev
```

The backend will be available at:

```
http://localhost:8787
```

### 3. Start the Frontend (Resource App)

In a new terminal:

```bash
cd resource-app
npm install
cp .env.example .env
```

Set the backend API URL:

```bash
VITE_API_BASE=http://localhost:8787
```

Run the frontend:

```bash
npm run dev
```

The frontend will be available at:

```
http://localhost:5173
```

## End-to-End Flow

Once both services are running:

1. Open the frontend in your browser.
2. Click **Fetch Secret**.
3. The backend returns `402 Payment Required`.
4. MetaMask prompts you to sign an **EIP-3009 authorization**.
5. The backend settles the payment.
6. The frontend retries the request.
7. The protected content is displayed.

## Package-Specific Documentation

For implementation details, refer to the individual READMEs:

- **Frontend** → [`resource-app/README.md`](./resource-app/README.md)
- **Backend** → [`resource-service/README.md`](./resource-service/README.md)

## Notes & Limitations

- Entitlements are stored **in memory** on the backend (no persistence).
- This repository is **not production-ready**.
- The API contract assumes:

  - `GET /api/data`
  - `POST /api/pay`
  - `paymentId` returned in the x402 challenge

- The frontend switches wallet networks based on the challenge payload.

## Technologies Used

- **TypeScript**
- **Node.js**
- **Express**
- **Vite**
- **React**
- **ethers**
- **@crypto.com/facilitator-client**
- **x402 protocol**
- **EIP-3009 (Exact Scheme)**

## License

This project is licensed under the **MIT License**.
