import { StyledStatusBar } from './styles';

export interface StatusBarProps {
  status: string;
}

export function StatusBar(props: StatusBarProps): JSX.Element {
  return (
    <StyledStatusBar>
      <b>Status:</b> {props.status}
    </StyledStatusBar>
  );
}
