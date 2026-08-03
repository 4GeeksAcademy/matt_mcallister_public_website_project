import React from 'react';

const Services = () => (
  <section className="py-16 bg-white" id="services">
    <div className="container mx-auto px-4">
      <h2 className="text-2xl font-bold mb-8 text-center">Our Services</h2>
      <div className="grid md:grid-cols-3 gap-8">
        <div className="bg-blue-100 p-6 rounded shadow">
          <h3 className="font-semibold text-lg mb-2">Warehouse Management</h3>
          <ul className="list-disc list-inside text-gray-700">
            <li>Storage, picking and packing</li>
            <li>Real-time inventory</li>
            <li>Warehouses in Los Angeles and Zaragoza</li>
          </ul>
        </div>
        <div className="bg-blue-100 p-6 rounded shadow">
          <h3 className="font-semibold text-lg mb-2">Last-Mile Deliveries</h3>
          <ul className="list-disc list-inside text-gray-700">
            <li>Certified carrier network in both countries</li>
            <li>Unified shipment tracking</li>
            <li>Incident and returns management</li>
          </ul>
        </div>
        <div className="bg-blue-100 p-6 rounded shadow">
          <h3 className="font-semibold text-lg mb-2">Reverse Logistics</h3>
          <ul className="list-disc list-inside text-gray-700">
            <li>Complete returns management</li>
            <li>Inspection and reconditioning</li>
            <li>Integration with your sales platform</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
);

export default Services;
