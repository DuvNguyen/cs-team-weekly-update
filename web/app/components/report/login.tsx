import { LogIn } from "lucide-react";
import { Alert } from "../ui/feedback";

const REASONS: Record<string, string> = {
  denied: "Google sign-in was cancelled.",
  state: "The sign-in expired or was tampered with. Please try again.",
  exchange: "Google did not accept the sign-in. Please try again.",
  scopes: "Every permission is needed to read Search Console and the SEO sheet. Tick them all and try again.",
  domain: "That Google account is not allowed to use this tool.",
};

/* Shown while there is no valid session. The button is a plain link: the whole OAuth dance is redirects. */
export function Login({ reason }: { reason: string }) {
  return (
    <div className="mx-auto max-w-lg">
      <section className="card rise space-y-6 p-10 text-center">
        <h2 className="text-3xl">Sign in to continue</h2>
        <p className="text-grey-600">
          Use the Google account that has access to your clients&rsquo; Search Console and the SEO team sheet. You stay signed in for 30 days.
        </p>
        {reason && <Alert>{REASONS[reason] ?? "Sign-in failed. Please try again."}</Alert>}
        <a href="/api/auth/login" className="btn btn-primary btn-lg !text-white no-underline hover:!no-underline">
          <LogIn size={18} />
          Sign in with Google
        </a>
      </section>
    </div>
  );
}
