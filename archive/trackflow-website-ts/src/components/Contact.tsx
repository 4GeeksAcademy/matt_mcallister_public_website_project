import React from 'react';

const Contact = () => (
  <section className="py-16 bg-gray-50" id="contact">
    <div className="container mx-auto px-4 text-center">
      <h2 className="text-2xl font-bold mb-8">Contact</h2>
      <p className="mb-2">Email: <a href="mailto:comercial@trackflow.com" className="text-blue-700 underline">comercial@trackflow.com</a></p>
      <p className="mb-2">Los Angeles: <a href="tel:+12135550147" className="text-blue-700 underline">+1 213 555 0147</a></p>
      <p>Zaragoza: <a href="tel:+34976123456" className="text-blue-700 underline">+34 976 123 456</a></p>
    </div>
  </section>
);

export default Contact;
