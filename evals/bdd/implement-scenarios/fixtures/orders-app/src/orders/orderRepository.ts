import type { Order } from "../pricing.js";

export interface OrderRepository {
  save(orderId: string, order: Order): Promise<void>;
  find(orderId: string): Promise<Order | undefined>;
}

export class InMemoryOrderRepository implements OrderRepository {
  private readonly orders = new Map<string, Order>();

  async save(orderId: string, order: Order): Promise<void> {
    this.orders.set(orderId, order);
  }

  async find(orderId: string): Promise<Order | undefined> {
    return this.orders.get(orderId);
  }
}
