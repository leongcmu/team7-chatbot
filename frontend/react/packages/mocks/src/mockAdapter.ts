import type { MessageAdapter } from "@eduling/contracts";
import { respond } from "./scenarios/respond.js";
/** Deterministic fixtures only: no fetch, model, catalog, prices or support submission. */
export function createMockAdapter({
  delayMs = 350,
  failOnce = false,
} = {}): MessageAdapter {
  let failed = false;
  return {
    async send(req, signal) {
      await new Promise<void>((resolve, reject) => {
        if (signal.aborted) {
          reject(new DOMException("Aborted", "AbortError"));
          return;
        }
        const timer = setTimeout(() => {
          signal.removeEventListener("abort", abort);
          resolve();
        }, delayMs);
        function abort() {
          clearTimeout(timer);
          reject(new DOMException("Aborted", "AbortError"));
        }
        signal.addEventListener("abort", abort, { once: true });
      });
      if (failOnce && !failed) {
        failed = true;
        throw new Error("Mock failure");
      }
      return respond(req);
    },
  };
}
