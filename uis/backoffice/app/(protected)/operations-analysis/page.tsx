import {
  buildOperationsAnalysis,
  demoCarriers,
  demoProducts,
  demoShipments,
} from "../../../../../packages/trackflow-core/src/index";

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

export default function OperationsAnalysisPage() {
  const analysis = buildOperationsAnalysis(
    demoProducts,
    demoShipments,
    demoCarriers,
  );

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10 md:px-10">
      <header className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">
          Milestone 2 · Programming fundamentals
        </p>
        <h1 className="text-3xl font-semibold md:text-4xl">
          Carrier &amp; Inventory Analysis
        </h1>
        <p className="max-w-3xl text-slate-300">
          A live operations view calculated from TrackFlow&apos;s canonical
          TypeScript business logic for Los Angeles and Zaragoza.
        </p>
      </header>

      <section
        aria-labelledby="inventory-overview"
        className="flex flex-col gap-4"
      >
        <h2 id="inventory-overview" className="text-xl font-semibold">
          Inventory overview
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Products" value={analysis.inventory.productCount.toString()} />
          <Metric label="Units in stock" value={analysis.inventory.totalUnits.toLocaleString()} />
          <Metric label="Inventory value" value={usd.format(analysis.inventory.totalValueUsd)} />
          <Metric
            label="Low-stock alerts"
            value={analysis.inventory.lowStockProducts.length.toString()}
            accent={analysis.inventory.lowStockProducts.length > 0}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {analysis.inventory.warehouses.map((warehouse) => (
            <article
              key={warehouse.warehouse}
              className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
            >
              <h3 className="font-semibold text-slate-100">{warehouse.warehouse}</h3>
              <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
                <Stat label="Products" value={warehouse.productCount.toString()} />
                <Stat label="Units" value={warehouse.stockUnits.toLocaleString()} />
                <Stat label="Value" value={usd.format(warehouse.inventoryValueUsd)} />
              </dl>
            </article>
          ))}
        </div>

        {analysis.inventory.lowStockProducts.map((product) => (
          <article
            key={product.sku}
            className="rounded-xl border border-amber-700/70 bg-amber-950/30 p-4"
          >
            <p className="font-medium text-amber-100">
              Reorder {product.name}
            </p>
            <p className="mt-1 text-sm text-amber-200/80">
              {product.warehouse} · {product.stockQuantity} units available ·
              threshold {product.minStockThreshold}
            </p>
          </article>
        ))}
      </section>

      <section
        aria-labelledby="carrier-recommendations"
        className="flex flex-col gap-4"
      >
        <div>
          <h2 id="carrier-recommendations" className="text-xl font-semibold">
            Carrier recommendations
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Lowest-cost carrier among options scoring at least 50 for the shipment.
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {analysis.carriers.recommendations.map((recommendation) => (
            <article
              key={recommendation.shipmentId}
              className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    {recommendation.shipmentId}
                  </p>
                  <h3 className="mt-1 font-semibold">{recommendation.productName}</h3>
                  <p className="mt-1 text-sm text-slate-400">
                    {recommendation.destination} · {recommendation.priority}
                  </p>
                </div>
                <span className="rounded-full bg-cyan-500/15 px-3 py-1 text-sm text-cyan-200">
                  {recommendation.carrierName ?? "Review needed"}
                </span>
              </div>
              {recommendation.carrierName ? (
                <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
                  <Stat label="Suitability score" value={`${recommendation.score}/100`} />
                  <Stat label="Estimated cost" value={usd.format(recommendation.costUsd ?? 0)} />
                </dl>
              ) : (
                <p className="mt-5 text-sm text-amber-200">
                  {recommendation.reason}
                </p>
              )}
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="carrier-reliability" className="flex flex-col gap-4">
        <h2 id="carrier-reliability" className="text-xl font-semibold">
          Carrier reliability
        </h2>
        <div className="overflow-hidden rounded-2xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="px-4 py-3 font-medium">Carrier</th>
                <th className="px-4 py-3 font-medium">On-time rate</th>
                <th className="px-4 py-3 font-medium">Average delivery</th>
              </tr>
            </thead>
            <tbody className="bg-slate-900">
              {analysis.carriers.reliability.map((carrier) => (
                <tr key={carrier.id} className="border-t border-slate-800">
                  <td className="px-4 py-3 font-medium">{carrier.name}</td>
                  <td className="px-4 py-3">{carrier.onTimeRate}%</td>
                  <td className="px-4 py-3">{carrier.averageDeliveryDays} days</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function Metric({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${accent ? "text-amber-300" : ""}`}>
        {value}
      </p>
    </article>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 font-medium text-slate-200">{value}</dd>
    </div>
  );
}
