export interface CountryKpiInput {
  country: "Brazil" | "Portugal";
  shipments: number;
  onTimeDeliveries: number;
  returnedOrders: number;
  customerSatisfaction: number;
  operatingCostUsd: number;
}

export interface ExecutiveSnapshot {
  globalShipmentVolume: number;
  globalOnTimeRate: number;
  globalReturnRate: number;
  averageCsat: number;
  totalOperatingCostUsd: number;
  performanceStatus: "Healthy" | "Warning" | "Critical";
  countryBreakdown: Array<{
    country: "Brazil" | "Portugal";
    shipmentVolume: number;
    onTimeRate: number;
    returnRate: number;
    customerSatisfaction: number;
    operatingCostUsd: number;
  }>;
}

const round = (value: number, decimals = 2): number => {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
};

const getStatus = (
  onTimeRate: number,
  returnRate: number,
  averageCsat: number,
): ExecutiveSnapshot["performanceStatus"] => {
  if (onTimeRate < 85 || returnRate > 8 || averageCsat < 75) {
    return "Critical";
  }

  if (onTimeRate < 92 || returnRate > 5 || averageCsat < 82) {
    return "Warning";
  }

  return "Healthy";
};

export const buildExecutiveSnapshot = (
  data: CountryKpiInput[],
): ExecutiveSnapshot => {
  const globalShipmentVolume = data.reduce((sum, row) => sum + row.shipments, 0);
  const totalOnTimeDeliveries = data.reduce(
    (sum, row) => sum + row.onTimeDeliveries,
    0,
  );
  const totalReturns = data.reduce((sum, row) => sum + row.returnedOrders, 0);
  const totalOperatingCostUsd = data.reduce(
    (sum, row) => sum + row.operatingCostUsd,
    0,
  );

  const averageCsat =
    data.length === 0
      ? 0
      : round(
          data.reduce((sum, row) => sum + row.customerSatisfaction, 0) /
            data.length,
        );

  const globalOnTimeRate =
    globalShipmentVolume === 0
      ? 0
      : round((totalOnTimeDeliveries / globalShipmentVolume) * 100);

  const globalReturnRate =
    globalShipmentVolume === 0
      ? 0
      : round((totalReturns / globalShipmentVolume) * 100);

  return {
    globalShipmentVolume,
    globalOnTimeRate,
    globalReturnRate,
    averageCsat,
    totalOperatingCostUsd: round(totalOperatingCostUsd),
    performanceStatus: getStatus(globalOnTimeRate, globalReturnRate, averageCsat),
    countryBreakdown: data.map((row) => ({
      country: row.country,
      shipmentVolume: row.shipments,
      onTimeRate:
        row.shipments === 0 ? 0 : round((row.onTimeDeliveries / row.shipments) * 100),
      returnRate:
        row.shipments === 0 ? 0 : round((row.returnedOrders / row.shipments) * 100),
      customerSatisfaction: round(row.customerSatisfaction),
      operatingCostUsd: round(row.operatingCostUsd),
    })),
  };
};

export const milestone2SampleInput: CountryKpiInput[] = [
  {
    country: "Brazil",
    shipments: 1940,
    onTimeDeliveries: 1785,
    returnedOrders: 88,
    customerSatisfaction: 84.2,
    operatingCostUsd: 148500,
  },
  {
    country: "Portugal",
    shipments: 1510,
    onTimeDeliveries: 1420,
    returnedOrders: 61,
    customerSatisfaction: 87.4,
    operatingCostUsd: 119300,
  },
];