import { StyledPaymentIdBar } from './styles';

export interface PaymentIdBarProps {
  paymentId: string;
}

export function PaymentIdBar(props: PaymentIdBarProps): JSX.Element {
  if (!props.paymentId) return <></>;
  return (
    <StyledPaymentIdBar>
      <b>paymentId:</b> {props.paymentId}
    </StyledPaymentIdBar>
  );
}
