import { ethers } from 'ethers';

/**
 * Ensures an EIP-1193–compatible wallet is available and authorized.
 *
 * Behavior:
 * - Verifies that a wallet provider (e.g. MetaMask) is exposed on `window.ethereum`.
 * - Prompts the user to authorize account access if not already granted.
 * - Returns an {@link ethers.BrowserProvider} bound to the injected provider.
 *
 * @remarks
 * This utility is intended for browser environments only.
 *
 * Side effects:
 * - Triggers a wallet UI prompt requesting account access.
 *
 * @returns An {@link ethers.BrowserProvider} connected to the user's wallet.
 * @throws If no injected wallet provider is found or access is denied.
 */
export async function ensureWallet(): Promise<ethers.BrowserProvider> {
  const anyWindow = window as any;

  if (!anyWindow.ethereum) {
    throw new Error('MetaMask not found');
  }

  const provider = new ethers.BrowserProvider(anyWindow.ethereum);
  await provider.send('eth_requestAccounts', []);

  return provider;
}
