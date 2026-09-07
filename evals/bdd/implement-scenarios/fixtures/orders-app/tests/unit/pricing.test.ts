import { describe, expect, it } from "vitest";

import { applyDiscount } from "../../src/pricing.js";

describe("applyDiscount", () => {
  it("rounds a discounted total to the nearest cent", () => {
    expect(applyDiscount({ totalCents: 999 }, "SPRING10").totalCents).toBe(899);
  });
});
