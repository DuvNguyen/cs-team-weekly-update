import { VoiceManager } from "../components/report/voice-manager";

// Rendered behind the client-side sign-in gate (AppShell), so there is nothing to pre-validate.
export const instant = false;

export default function VoicePage() {
  return <VoiceManager />;
}
