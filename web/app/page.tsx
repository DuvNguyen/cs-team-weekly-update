import SetupScreen from "./components/report/setup-screen";

// The home page is the report setup. Rendered behind the client-side sign-in gate (AppShell), so there is nothing to pre-validate.
export const instant = false;

export default function Home() {
  return <SetupScreen />;
}
