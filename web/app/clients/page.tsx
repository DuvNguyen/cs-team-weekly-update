import { ClientsEditor } from "../components/clients/clients-editor";

// Rendered behind the client-side sign-in gate (AppShell), so there is nothing to pre-validate.
export const instant = false;

export default function ClientsPage() {
  return <ClientsEditor />;
}
