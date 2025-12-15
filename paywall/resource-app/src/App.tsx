import { ResourceContainer } from './containers/ResourceContainer';

const API_BASE = import.meta.env.VITE_API_BASE as string;

export default function App(): JSX.Element {
  return <ResourceContainer apiBase={API_BASE} />;
}
