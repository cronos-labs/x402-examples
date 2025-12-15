import type { ReactNode } from 'react';
import { StyledAppShell, StyledDescription, StyledTitle } from './styles';

export interface AppShellProps {
  title: string;
  description: ReactNode;
  children: ReactNode;
}

export function AppShell(props: AppShellProps): JSX.Element {
  return (
    <StyledAppShell>
      <StyledTitle>{props.title}</StyledTitle>
      <StyledDescription>{props.description}</StyledDescription>
      {props.children}
    </StyledAppShell>
  );
}
