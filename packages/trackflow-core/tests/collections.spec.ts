import { describe, expect, it } from "vitest";

import {
  filterLowStockProducts,
  filterProductsByCategory,
  filterProductsByWarehouse,
  sortCarriersByReliability,
  sortProductsByStock,
} from "../src/utils/collections.js";
import { sampleCarriers, sampleProducts } from "./fixtures.js";

describe("collections utilities", () => {
  it("filters products by warehouse", () => {
    const result = filterProductsByWarehouse(sampleProducts, "Los Angeles");
    expect(result).toHaveLength(2);
  });

  it("filters products by category", () => {
    const result = filterProductsByCategory(sampleProducts, "Electronics");
    expect(result).toHaveLength(1);
    expect(result[0].sku).toBe("LAPTOP-DELL-15");
  });

  it("returns low stock products", () => {
    const result = filterLowStockProducts(sampleProducts);
    expect(result.map((p) => p.sku)).toEqual(["LAPTOP-DELL-15"]);
  });

  it("sorts products by stock without mutating input", () => {
    const original = [...sampleProducts];
    const sorted = sortProductsByStock(sampleProducts, "asc");

    expect(sorted.map((p) => p.stockQuantity)).toEqual([8, 45, 120]);
    expect(sampleProducts).toEqual(original);
  });

  it("sorts carriers by reliability without mutating input", () => {
    const original = [...sampleCarriers];
    const sorted = sortCarriersByReliability(sampleCarriers, "desc");

    expect(sorted.map((c) => c.onTimeRate)).toEqual([95, 92, 88]);
    expect(sampleCarriers).toEqual(original);
  });

  it("handles empty arrays", () => {
    expect(filterProductsByWarehouse([], "Los Angeles")).toEqual([]);
    expect(sortProductsByStock([], "asc")).toEqual([]);
  });
});
