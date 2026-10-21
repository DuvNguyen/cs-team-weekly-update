import SetupScreen from "../components/report/setup-screen";

// Rendered behind the client-side sign-in gate (AppShell), so there is nothing to pre-validate.
export const instant = false;

export default function SetupPage() {
  return <SetupScreen />;
}
