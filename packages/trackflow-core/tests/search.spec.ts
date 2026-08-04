import { describe, expect, it } from "vitest";

import {
  binarySearchProductByWeight,
  findProductBySKU,
  findShipmentById,
} from "../src/utils/search.js";
import { sampleProducts, sampleShipment } from "./fixtures.js";

describe("search utilities", () => {
  it("finds product by SKU case-insensitively", () => {
    const result = findProductBySKU(sampleProducts, "shoe-blk-42");
    expect(result?.name).toBe("Black Running Shoes - Size 42");
  });

  it("returns null when product SKU is not found", () => {
    const result = findProductBySKU(sampleProducts, "missing-sku");
    expect(result).toBeNull();
  });

  it("finds shipment by ID", () => {
    const result = findShipmentById([sampleShipment], "SH-2024-8821");
    expect(result?.sku).toBe("LAPTOP-DELL-15");
  });

  it("returns null when shipment ID is not found", () => {
    const result = findShipmentById([sampleShipment], "bad-id");
    expect(result).toBeNull();
  });

  it("performs binary search by product weight", () => {
    const sorted = [...sampleProducts].sort((a, b) => a.weightKg - b.weightKg);
    const index = binarySearchProductByWeight(sorted, 0.8);

    expect(index).toBeGreaterThanOrEqual(0);
    expect(sorted[index].sku).toBe("SHOE-BLK-42");
  });

  it("returns -1 when weight does not exist", () => {
    const sorted = [...sampleProducts].sort((a, b) => a.weightKg - b.weightKg);
    const index = binarySearchProductByWeight(sorted, 99.9);
    expect(index).toBe(-1);
  });
});
