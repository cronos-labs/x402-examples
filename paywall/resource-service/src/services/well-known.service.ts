import type { CronosNetwork } from '@crypto.com/facilitator-client';

const PORT = process.env.PORT || 8787;
const HOST = process.env.PUBLIC_HOST || `http://localhost:${PORT}`;
const NETWORK = (process.env.NETWORK ?? 'cronos-testnet') as CronosNetwork;

export class WellKnownService {
  /**
   * Returns the A2A Agent Card describing this resource service.
   *
   * Keep it simple for tutorial purposes:
   * - advertise resource url
   * - advertise paywall protocol + settlement endpoint
   */
  public getAgentCard() {
    return {
      name: 'paywall-resource',
      description: 'Cronos X402 paywalled resource service',
      url: HOST,
      network: NETWORK,
      resources: [
        {
          id: 'secret-data',
          title: 'Paywalled Demo Resource',
          url: '/api/data',
          paywall: {
            protocol: 'x402',
            settlement: '/api/pay',
          },
        },
      ],
    };
  }
}
