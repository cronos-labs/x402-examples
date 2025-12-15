import { AppShell } from '../../components/AppShell';
import { ActionButtons } from '../../components/ActionButtons';
import { StatusBar } from '../../components/StatusBar';
import { PaymentIdBar } from '../../components/PaymentIdBar';
import { DataViewer } from '../../components/DataViewer';
import { useX402Flow } from '../../hooks/useX402Flow';
import { StyledContainer } from './styles';

export interface ResourceContainerProps {
  apiBase: string;
}

export function ResourceContainer(props: ResourceContainerProps): JSX.Element {
  const { status, data, paymentId, fetchSecret, retryWithPaymentId } = useX402Flow({
    apiBase: props.apiBase,
  });

  return (
    <StyledContainer>
      <AppShell
        title="X402 Paywalled Resource Demo (Cronos)"
        description={
          <>
            Click <b>Fetch Data</b>. If the server returns a 402 payment challenge, you’ll be asked
            to sign an EIP-3009 authorization in MetaMask, the backend will verify + settle via the
            facilitator, and the resource will unlock.
          </>
        }
      >
        <ActionButtons
          onFetch={() => void fetchSecret()}
          onRetry={() => void retryWithPaymentId()}
          retryDisabled={!paymentId}
        />

        <StatusBar status={status} />
        <PaymentIdBar paymentId={paymentId} />
        <DataViewer data={data} />
      </AppShell>
    </StyledContainer>
  );
}
