import { describe, expect, it } from "vitest";

import {
  buildOperationsAnalysis,
  demoCarriers,
  demoProducts,
  demoShipments,
} from "../src/index.js";

describe("operations analysis workflow", () => {
  it("builds the inventory and carrier output displayed by backoffice", () => {
    const analysis = buildOperationsAnalysis(
      demoProducts,
      demoShipments,
      demoCarriers,
    );

    expect(analysis.inventory).toMatchObject({
      productCount: 3,
      totalUnits: 173,
      totalValueUsd: 16975,
    });
    expect(analysis.inventory.lowStockProducts).toEqual([
      expect.objectContaining({
        sku: "LAPTOP-DELL-15",
        warehouse: "Zaragoza",
        stockQuantity: 8,
      }),
    ]);
    expect(analysis.inventory.warehouses).toEqual([
      {
        warehouse: "Los Angeles",
        productCount: 2,
        stockUnits: 165,
        inventoryValueUsd: 11775,
      },
      {
        warehouse: "Zaragoza",
        productCount: 1,
        stockUnits: 8,
        inventoryValueUsd: 5200,
      },
    ]);
    expect(analysis.carriers.reliability.map((carrier) => carrier.name)).toEqual([
      "DHL Express",
      "SEUR",
      "UPS",
    ]);
    expect(analysis.carriers.recommendations).toEqual([
      expect.objectContaining({
        shipmentId: "SH-2024-8821",
        carrierName: "UPS",
        score: 76.4,
        costUsd: 30.89,
      }),
      expect.objectContaining({
        shipmentId: "SH-2024-8822",
        carrierName: "UPS",
        score: 96.4,
        costUsd: 16.67,
      }),
    ]);
  });

  it("returns a UI-safe explanation when shipment inventory is missing", () => {
    const analysis = buildOperationsAnalysis(
      demoProducts,
      [{ ...demoShipments[0], sku: "MISSING-SKU" }],
      demoCarriers,
    );

    expect(analysis.carriers.recommendations[0]).toMatchObject({
      carrierName: null,
      costUsd: null,
      reason: "Product SKU was not found in inventory.",
    });
  });

  it("does not mutate canonical demo data", () => {
    const carrierOrder = demoCarriers.map((carrier) => carrier.id);

    buildOperationsAnalysis(demoProducts, demoShipments, demoCarriers);

    expect(demoCarriers.map((carrier) => carrier.id)).toEqual(carrierOrder);
  });
});
