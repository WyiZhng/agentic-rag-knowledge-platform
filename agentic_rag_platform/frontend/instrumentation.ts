
import { registerOTel } from "@vercel/otel";

export function register() {
  registerOTel({
    serviceName: "agentic_rag_platform-frontend",
  });
}
