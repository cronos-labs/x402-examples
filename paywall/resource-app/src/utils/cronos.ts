import type { CronosNetwork } from '@crypto.com/facilitator-client';

const CRONOS = {
  mainnet: {
    chainId: '0x19',
    chainName: 'Cronos Mainnet',
    nativeCurrency: { name: 'CRO', symbol: 'CRO', decimals: 18 },
    rpcUrls: ['https://evm.cronos.org'],
    blockExplorerUrls: ['https://cronoscan.com'],
  },
  testnet: {
    chainId: '0x152',
    chainName: 'Cronos Testnet',
    nativeCurrency: { name: 'tCRO', symbol: 'tCRO', decimals: 18 },
    rpcUrls: ['https://evm-t3.cronos.org'],
    blockExplorerUrls: ['https://cronos.org/explorer/testnet3'],
  },
} as const;

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
  const anyWindow = window as any;
  const eth = anyWindow?.ethereum;
  if (!eth?.request) throw new Error('No EIP-1193 provider found (window.ethereum missing)');

  const cfg = target === 'cronos-mainnet' ? CRONOS.mainnet : CRONOS.testnet;

  const switchTo = async () =>
    eth.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: cfg.chainId }],
    });

  try {
    await switchTo();
    return;
  } catch (e: any) {
    // 4902 = chain not added
    if (e?.code === 4902) {
      await eth.request({
        method: 'wallet_addEthereumChain',
        params: [cfg],
      });

      // IMPORTANT: switch after adding
      await switchTo();
      return;
    }

    // user rejected, or other error
    throw e;
  }
}
