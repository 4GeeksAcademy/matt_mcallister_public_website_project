import { describe, expect, it } from "vitest";

import {
  validateCarrier,
  validateProduct,
  validateShipment,
} from "../src/utils/validations.js";
import { sampleCarriers, sampleProducts, sampleShipment } from "./fixtures.js";

describe("validation utilities", () => {
  it("validates a correct product", () => {
    const result = validateProduct(sampleProducts[0]);
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("collects multiple product validation errors", () => {
    const result = validateProduct({
      ...sampleProducts[0],
      sku: "  ",
      weightKg: 0,
      dimensions: { lengthCm: 0, widthCm: 201, heightCm: -1 },
      stockQuantity: -1,
      minStockThreshold: -2,
      unitCostUSD: 0,
    });

    expect(result.valid).toBe(false);
    expect(result.errors.length).toBe(8);
  });

  it("validates a correct shipment", () => {
    const result = validateShipment(sampleShipment);
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("collects multiple shipment validation errors", () => {
    const result = validateShipment({
      ...sampleShipment,
      quantity: 0,
      declaredValueUSD: 0,
      destination: { ...sampleShipment.destination, distanceKm: -1 },
    });

    expect(result.valid).toBe(false);
    expect(result.errors).toEqual([
      "quantity must be > 0",
      "declaredValueUSD must be > 0",
      "distanceKm must be >= 0",
    ]);
  });

  it("validates a correct carrier", () => {
    const result = validateCarrier(sampleCarriers[0]);
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("collects multiple carrier validation errors", () => {
    const result = validateCarrier({
      ...sampleCarriers[0],
      baseRateUSD: -1,
      ratePerKgUSD: -1,
      ratePerKmUSD: -1,
      avgDeliveryDays: 0,
      onTimeRate: 101,
      maxWeightKg: 0,
      operatesIn: [],
    });

    expect(result.valid).toBe(false);
    expect(result.errors.length).toBe(7);
  });
});
