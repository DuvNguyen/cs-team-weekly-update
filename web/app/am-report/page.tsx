import { AmReport } from "../components/am/am-report";

// Rendered behind the client-side sign-in gate (AppShell), so there is nothing to pre-validate.
export const instant = false;

export default function AmReportPage() {
  return <AmReport />;
}
