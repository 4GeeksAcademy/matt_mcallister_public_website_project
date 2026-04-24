import type {
  Carrier,
  Product,
  ProductCategory,
  Shipment,
  ShipmentStatus,
} from "../types/domain.js";

function roundToTwoDecimals(value: number): number {
  return Math.round(value * 100) / 100;
}

export function calculateShippingCost(
  shipment: Shipment,
  product: Product,
  carrier: Carrier,
): number {
  const baseRate = carrier.baseRateUSD;
  const weightCost = product.weightKg * carrier.ratePerKgUSD * shipment.quantity;
  const distanceCost = shipment.destination.distanceKm * carrier.ratePerKmUSD;

  let surchargeMultiplier = 1;
  if (shipment.priority === "Express") {
    surchargeMultiplier = 1.3;
  } else if (shipment.priority === "Same-day") {
    surchargeMultiplier = 1.6;
  }

  const total = (baseRate + weightCost + distanceCost) * surchargeMultiplier;
  return roundToTwoDecimals(total);
}

export function scoreCarrierForShipment(
  carrier: Carrier,
  shipment: Shipment,
  product: Product,
): number {
  let score = 0;

  if (carrier.operatesIn.includes(shipment.destination.country)) {
    score += 20;
  }

  const shipmentWeight = product.weightKg * shipment.quantity;
  if (shipmentWeight <= carrier.maxWeightKg) {
    score += 20;
  }

  if (carrier.acceptsPriority.includes(shipment.priority)) {
    score += 15;
  }

  if (!product.isFragile || carrier.handlesFragile) {
    score += 15;
  }

  score += carrier.onTimeRate * 0.3;

  return roundToTwoDecimals(score);
}

export function selectBestCarrier(
  carriers: Carrier[],
  shipment: Shipment,
  product: Product,
): { carrier: Carrier; score: number; cost: number } | null {
  let best: { carrier: Carrier; score: number; cost: number } | null = null;

  for (const carrier of carriers) {
    const score = scoreCarrierForShipment(carrier, shipment, product);
    if (score < 50) {
      continue;
    }

    const cost = calculateShippingCost(shipment, product, carrier);

    if (best === null || cost < best.cost) {
      best = { carrier, score, cost };
    }
  }

  return best;
}

export function countProductsByCategory(
  products: Product[],
): Record<ProductCategory, number> {
  const counts: Record<ProductCategory, number> = {
    Fashion: 0,
    Electronics: 0,
    Cosmetics: 0,
    Home: 0,
    Other: 0,
  };

  for (const product of products) {
    counts[product.category] += 1;
  }

  return counts;
}

export function calculateTotalInventoryValue(products: Product[]): number {
  const total = products.reduce(
    (sum, product) => sum + product.stockQuantity * product.unitCostUSD,
    0,
  );

  return roundToTwoDecimals(total);
}

export function calculateAverageShipmentDistance(shipments: Shipment[]): number {
  if (shipments.length === 0) {
    return 0;
  }

  const totalDistance = shipments.reduce(
    (sum, shipment) => sum + shipment.destination.distanceKm,
    0,
  );

  return roundToTwoDecimals(totalDistance / shipments.length);
}

export function groupShipmentsByStatus(
  shipments: Shipment[],
): Record<ShipmentStatus, Shipment[]> {
  const grouped: Record<ShipmentStatus, Shipment[]> = {
    Pending: [],
    Assigned: [],
    "In transit": [],
    Delivered: [],
    Failed: [],
  };

  for (const shipment of shipments) {
    grouped[shipment.status].push(shipment);
  }

  return grouped;
}

export function findTopCarriers(
  shipments: Shipment[],
  topN: number,
): Array<{ carrier: string; count: number }> {
  const usage = new Map<string, number>();

  for (const shipment of shipments) {
    if (shipment.carrier === null) {
      continue;
    }

    usage.set(shipment.carrier, (usage.get(shipment.carrier) ?? 0) + 1);
  }

  return Array.from(usage.entries())
    .map(([carrier, count]) => ({ carrier, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, topN);
}
