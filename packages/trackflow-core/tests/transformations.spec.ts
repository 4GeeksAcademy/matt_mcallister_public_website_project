import { describe, expect, it } from "vitest";

import {
  calculateAverageShipmentDistance,
  calculateShippingCost,
  calculateTotalInventoryValue,
  countProductsByCategory,
  findTopCarriers,
  groupShipmentsByStatus,
  scoreCarrierForShipment,
  selectBestCarrier,
} from "../src/utils/transformations.js";
import type { Carrier } from "../src/types/domain.js";
import { sampleCarriers, sampleProducts, sampleShipment } from "./fixtures.js";

describe("transformations utilities", () => {
  it("calculates shipping cost with priority surcharge and rounding", () => {
    const cost = calculateShippingCost(sampleShipment, sampleProducts[1], sampleCarriers[1]);
    expect(cost).toBe(46.22);
  });

  it("scores a carrier for shipment", () => {
    const score = scoreCarrierForShipment(
      sampleCarriers[1],
      sampleShipment,
      sampleProducts[1],
    );
    expect(score).toBe(97.6);
  });

  it("selects lowest-cost suitable carrier", () => {
    const best = selectBestCarrier(sampleCarriers, sampleShipment, sampleProducts[1]);
    expect(best).not.toBeNull();
    expect(best?.carrier.name).toBe("UPS");
    expect(best?.cost).toBe(30.89);
  });

  it("returns null when no carrier is suitable", () => {
    const impossibleShipment = { ...sampleShipment, priority: "Same-day" as const };
    const fragileProduct = { ...sampleProducts[1], isFragile: true };
    const carriers: Carrier[] = [
      {
        ...sampleCarriers[0],
        handlesFragile: false,
        acceptsPriority: ["Standard"],
        maxWeightKg: 1,
        operatesIn: ["United States"],
      },
    ];

    const best = selectBestCarrier(carriers, impossibleShipment, fragileProduct);
    expect(best).toBeNull();
  });

  it("counts products by category", () => {
    const counts = countProductsByCategory(sampleProducts);
    expect(counts).toEqual({
      Fashion: 1,
      Electronics: 1,
      Cosmetics: 1,
      Home: 0,
      Other: 0,
    });
  });

  it("calculates total inventory value with rounding", () => {
    const total = calculateTotalInventoryValue(sampleProducts);
    expect(total).toBe(16975);
  });

  it("calculates average shipment distance and handles empty array", () => {
    const avg = calculateAverageShipmentDistance([
      sampleShipment,
      {
        ...sampleShipment,
        id: "SH-2",
        destination: { ...sampleShipment.destination, distanceKm: 100 },
      },
    ]);

    expect(avg).toBe(210);
    expect(calculateAverageShipmentDistance([])).toBe(0);
  });

  it("groups shipments by status", () => {
    const grouped = groupShipmentsByStatus([
      sampleShipment,
      { ...sampleShipment, id: "SH-2", status: "Delivered" as const },
    ]);

    expect(grouped.Pending).toHaveLength(1);
    expect(grouped.Delivered).toHaveLength(1);
    expect(grouped.Assigned).toHaveLength(0);
  });

  it("finds top carriers by usage and ignores null carriers", () => {
    const shipments = [
      { ...sampleShipment, id: "A", carrier: "SEUR" },
      { ...sampleShipment, id: "B", carrier: "DHL Express" },
      { ...sampleShipment, id: "C", carrier: "SEUR" },
      { ...sampleShipment, id: "D", carrier: null },
    ];

    const top = findTopCarriers(shipments, 2);
    expect(top).toEqual([
      { carrier: "SEUR", count: 2 },
      { carrier: "DHL Express", count: 1 },
    ]);
  });
});
