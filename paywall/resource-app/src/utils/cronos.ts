import type { CronosNetwork } from '@crypto.com/facilitator-client';

/**
 * Ensures the user's wallet is connected to the required Cronos network.
 *
 * Behavior:
 * - Attempts to switch the wallet to the target Cronos chain.
 * - If the chain is not yet added (error code `4902`) and the target is
 *   `cronos-testnet`, attempts to add the network to the wallet.
 * - Re-throws any unsupported or unexpected errors.
 *
 * @remarks
 * This utility assumes an EIP-1193–compatible provider assumed to be exposed
 * at `window.ethereum` (e.g. MetaMask).
 *
 * Side effects:
 * - Triggers wallet UI prompts for network switching or addition.
 *
 * @param target - Target Cronos network identifier.
 * @returns Resolves once the wallet is connected to the requested network.
 * @throws If the wallet rejects the request or the provider is unavailable.
 */
export async function ensureCronosChain(target: CronosNetwork): Promise<void> {
  /**
   * Cronos chain id in hex format as expected by EIP-3085 / EIP-3326.
   *
   * @remarks
   * - `0x19`  → Cronos Mainnet (25)
   * - `0x152` → Cronos Testnet (338)
   */
  const chainIdHex = target === 'cronos-mainnet' ? '0x19' : '0x152';

  const anyWindow = window as any;

  try {
    await anyWindow.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: chainIdHex }],
    });
  } catch (e: any) {
    /**
     * Error code `4902` indicates the requested chain is not yet added
     * to the user's wallet.
     */
    if (e?.code === 4902 && target === 'cronos-testnet') {
      await anyWindow.ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [
          {
            chainId: '0x152',
            chainName: 'Cronos Testnet',
            nativeCurrency: { name: 'tCRO', symbol: 'tCRO', decimals: 18 },
            rpcUrls: ['https://evm-t3.cronos.org'],
            blockExplorerUrls: ['https://cronos.org/explorer/testnet3'],
          },
        ],
      });
    } else {
      throw e;
    }
  }
}
