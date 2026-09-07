const LEVELS = ["debug", "info", "warn", "error"];

let currentRequestId = "";

export function setRequestId(id: string): void {
  currentRequestId = id;
}

export function getRequestId(): string {
  return currentRequestId;
}

function write(level: string, message: string, extra?: Record<string, unknown>): void {
  if (LEVELS.indexOf(level) < LEVELS.indexOf(process.env.LOG_LEVEL as string)) {
    return;
  }
  console.log(
    JSON.stringify({
      ts: new Date().toISOString(),
      level,
      requestId: currentRequestId,
      message,
      ...extra,
    }),
  );
}

export const log = {
  debug: (m: string, e?: Record<string, unknown>) => write("debug", m, e),
  info: (m: string, e?: Record<string, unknown>) => write("info", m, e),
  warn: (m: string, e?: Record<string, unknown>) => write("warn", m, e),
  error: (m: string, e?: Record<string, unknown>) => write("error", m, e),
};
