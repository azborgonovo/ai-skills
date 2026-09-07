import { Router } from "express";
import { randomUUID } from "node:crypto";
import { log, setRequestId } from "../lib/logger.js";

export const payments = Router();

payments.post("/payments", async (req, res) => {
  setRequestId(req.header("x-request-id") ?? randomUUID());
  log.info("payment received", { amount: req.body.amount });

  try {
    const receipt = await capture(req.body);
    log.info("payment captured", { receiptId: receipt.id });
    res.status(201).json(receipt);
  } catch (err) {
    log.error("payment failed", { err });
    res.status(502).json({ error: "capture failed" });
  }
});

async function capture(body: unknown): Promise<{ id: string }> {
  return { id: randomUUID() };
}
