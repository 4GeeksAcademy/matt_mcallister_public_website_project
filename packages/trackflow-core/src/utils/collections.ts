import type {
  Carrier,
  Product,
  ProductCategory,
  WarehouseLocation,
} from "../types/domain.js";

export function filterProductsByWarehouse(
  products: Product[],
  warehouse: WarehouseLocation,
): Product[] {
  return products.filter((product) => product.warehouse === warehouse);
}

export function filterProductsByCategory(
  products: Product[],
  category: ProductCategory,
): Product[] {
  return products.filter((product) => product.category === category);
}

export function filterLowStockProducts(products: Product[]): Product[] {
  return products.filter(
    (product) => product.stockQuantity <= product.minStockThreshold,
  );
}

export function sortProductsByStock(
  products: Product[],
  order: "asc" | "desc",
): Product[] {
  const direction = order === "asc" ? 1 : -1;
  return [...products].sort(
    (a, b) => (a.stockQuantity - b.stockQuantity) * direction,
  );
}

export function sortCarriersByReliability(
  carriers: Carrier[],
  order: "asc" | "desc",
): Carrier[] {
  const direction = order === "asc" ? 1 : -1;
  return [...carriers].sort((a, b) => (a.onTimeRate - b.onTimeRate) * direction);
}
