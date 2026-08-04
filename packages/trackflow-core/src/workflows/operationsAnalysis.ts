import type {
  Carrier,
  Product,
  Shipment,
  WarehouseLocation,
} from "../types/domain.js";
import {
  filterLowStockProducts,
  filterProductsByWarehouse,
  sortCarriersByReliability,
} from "../utils/collections.js";
import { findProductBySKU } from "../utils/search.js";
import {
  calculateTotalInventoryValue,
  selectBestCarrier,
} from "../utils/transformations.js";

export interface OperationsAnalysis {
  inventory: {
    productCount: number;
    totalUnits: number;
    totalValueUsd: number;
    lowStockProducts: Array<{
      sku: string;
      name: string;
      warehouse: WarehouseLocation;
      stockQuantity: number;
      minStockThreshold: number;
    }>;
    warehouses: Array<{
      warehouse: WarehouseLocation;
      productCount: number;
      stockUnits: number;
      inventoryValueUsd: number;
    }>;
  };
  carriers: {
    reliability: Array<{
      id: string;
      name: string;
      onTimeRate: number;
      averageDeliveryDays: number;
    }>;
    recommendations: Array<{
      shipmentId: string;
      productName: string;
      destination: string;
      priority: Shipment["priority"];
      carrierName: string | null;
      score: number | null;
      costUsd: number | null;
      reason: string | null;
    }>;
  };
}

const warehouses: WarehouseLocation[] = ["Los Angeles", "Zaragoza"];

export function buildOperationsAnalysis(
  products: Product[],
  shipments: Shipment[],
  carriers: Carrier[],
): OperationsAnalysis {
  const lowStockProducts = filterLowStockProducts(products).map((product) => ({
    sku: product.sku,
    name: product.name,
    warehouse: product.warehouse,
    stockQuantity: product.stockQuantity,
    minStockThreshold: product.minStockThreshold,
  }));

  const warehouseSummaries = warehouses.map((warehouse) => {
    const warehouseProducts = filterProductsByWarehouse(products, warehouse);

    return {
      warehouse,
      productCount: warehouseProducts.length,
      stockUnits: warehouseProducts.reduce(
        (sum, product) => sum + product.stockQuantity,
        0,
      ),
      inventoryValueUsd: calculateTotalInventoryValue(warehouseProducts),
    };
  });

  const recommendations = shipments.map((shipment) => {
    const product = findProductBySKU(products, shipment.sku);

    if (product === null) {
      return {
        shipmentId: shipment.id,
        productName: shipment.sku,
        destination: `${shipment.destination.city}, ${shipment.destination.country}`,
        priority: shipment.priority,
        carrierName: null,
        score: null,
        costUsd: null,
        reason: "Product SKU was not found in inventory.",
      };
    }

    const recommendation = selectBestCarrier(carriers, shipment, product);

    return {
      shipmentId: shipment.id,
      productName: product.name,
      destination: `${shipment.destination.city}, ${shipment.destination.country}`,
      priority: shipment.priority,
      carrierName: recommendation?.carrier.name ?? null,
      score: recommendation?.score ?? null,
      costUsd: recommendation?.cost ?? null,
      reason:
        recommendation === null
          ? "No carrier met the minimum suitability score."
          : null,
    };
  });

  return {
    inventory: {
      productCount: products.length,
      totalUnits: products.reduce(
        (sum, product) => sum + product.stockQuantity,
        0,
      ),
      totalValueUsd: calculateTotalInventoryValue(products),
      lowStockProducts,
      warehouses: warehouseSummaries,
    },
    carriers: {
      reliability: sortCarriersByReliability(carriers, "desc").map((carrier) => ({
        id: carrier.id,
        name: carrier.name,
        onTimeRate: carrier.onTimeRate,
        averageDeliveryDays: carrier.avgDeliveryDays,
      })),
      recommendations,
    },
  };
}
