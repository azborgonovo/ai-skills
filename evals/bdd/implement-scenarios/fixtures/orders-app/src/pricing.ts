export type Order = { totalCents: number };

const DISCOUNT_RATES: Record<string, number> = { SPRING10: 0.1 };

export function applyDiscount(order: Order, code: string): Order {
  const rate = DISCOUNT_RATES[code] ?? 0;
  return { totalCents: Math.round(order.totalCents * (1 - rate)) };
}
