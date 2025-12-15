import { StyledPre } from './styles';

export interface DataViewerProps {
  data: string;
}

export function DataViewer(props: DataViewerProps): JSX.Element {
  return <StyledPre>{props.data || '—'}</StyledPre>;
}
