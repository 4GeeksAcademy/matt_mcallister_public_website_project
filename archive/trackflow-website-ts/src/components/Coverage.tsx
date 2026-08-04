import React from 'react';

const Coverage = () => (
  <section className="py-16 bg-gray-50" id="coverage">
    <div className="container mx-auto px-4">
      <h2 className="text-2xl font-bold mb-8 text-center">Coverage</h2>
      <div className="grid md:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded shadow">
          <h3 className="font-semibold text-lg mb-2">United States</h3>
          <ul className="list-disc list-inside text-gray-700">
            <li>Warehouse in Los Angeles</li>
            <li>National coverage</li>
            <li>Carriers: UPS, FedEx, DHL</li>
          </ul>
        </div>
        <div className="bg-white p-6 rounded shadow">
          <h3 className="font-semibold text-lg mb-2">Spain</h3>
          <ul className="list-disc list-inside text-gray-700">
            <li>Warehouse in Zaragoza</li>
            <li>Peninsular and island coverage</li>
            <li>Carriers: MRW, SEUR, DHL</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
);

export default Coverage;
