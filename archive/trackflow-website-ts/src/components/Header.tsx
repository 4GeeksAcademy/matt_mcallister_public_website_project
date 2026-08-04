import React from 'react';

const Header = () => (
  <header className="bg-white shadow">
    <div className="container mx-auto px-4 py-4 flex items-center justify-between">
      <span className="font-bold text-xl text-blue-700">TrackFlow</span>
      <nav aria-label="Main navigation">
        <ul className="flex gap-6 text-gray-700">
          <li><a href="#home" className="hover:text-blue-700">Home</a></li>
          <li><a href="#services" className="hover:text-blue-700">Services</a></li>
          <li><a href="#coverage" className="hover:text-blue-700">Coverage</a></li>
          <li><a href="#contact" className="hover:text-blue-700">Contact</a></li>
        </ul>
      </nav>
    </div>
  </header>
);

export default Header;
