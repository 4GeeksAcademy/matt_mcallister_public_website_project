export interface Service {
  title: string;
  items: string[];
}

export interface CountryCoverage {
  country: string;
  items: string[];
}

export interface Benefit {
  title: string;
  description: string;
}

export interface ProofMetric {
  label: string;
  value: string;
}

export interface QuickFact {
  label: string;
  value: string;
}

export const quickFacts: QuickFact[] = [
  { label: "Founded", value: "2009" },
  { label: "Team size", value: "130+" },
  { label: "Warehouses", value: "Los Angeles, Zaragoza" },
  { label: "Industries", value: "Fashion, Electronics, Cosmetics" },
];

export const services: Service[] = [
  {
    title: "Warehouse Management",
    items: [
      "Storage, picking and packing",
      "Real-time inventory visibility",
      "Warehouses in Los Angeles and Zaragoza",
    ],
  },
  {
    title: "Last-Mile Deliveries",
    items: [
      "Certified carrier network in both countries",
      "Unified shipment tracking",
      "Incident and returns management",
    ],
  },
  {
    title: "Reverse Logistics",
    items: [
      "Complete returns management",
      "Inspection and reconditioning workflows",
      "Integration with your sales platform",
    ],
  },
];

export const coverage: CountryCoverage[] = [
  {
    country: "United States",
    items: ["Warehouse in Los Angeles", "National coverage", "Carriers: UPS, FedEx, DHL"],
  },
  {
    country: "Spain",
    items: ["Warehouse in Zaragoza", "Peninsular and island coverage", "Carriers: MRW, SEUR, DHL"],
  },
];

export const benefits: Benefit[] = [
  {
    title: "Binational operation",
    description: "The only operator with own infrastructure in the United States and Spain.",
  },
  {
    title: "130+ professionals",
    description: "Dedicated teams in operations, customer experience, and technology.",
  },
  {
    title: "Own technology",
    description: "Total visibility into inventory and shipment events across countries.",
  },
  {
    title: "E-commerce specialization",
    description: "Built for fashion, electronics, and cosmetics brands that need scale.",
  },
];

export const proofMetrics: ProofMetric[] = [
  { label: "Service footprint", value: "2 countries" },
  { label: "Carrier network", value: "8 partners" },
  { label: "Returns share managed", value: "18% to 25%" },
  { label: "Annual revenue scale", value: "EUR 9M" },
];
