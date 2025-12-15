import { StyledButton, StyledButtonsRow } from './styles';

export interface ActionButtonsProps {
  onFetch: () => void;
  onRetry: () => void;
  retryDisabled: boolean;
}

export function ActionButtons(props: ActionButtonsProps): JSX.Element {
  return (
    <StyledButtonsRow>
      <StyledButton onClick={props.onFetch}>Fetch Data</StyledButton>
      <StyledButton onClick={props.onRetry} disabled={props.retryDisabled}>
        Retry with paymentId
      </StyledButton>
    </StyledButtonsRow>
  );
}
