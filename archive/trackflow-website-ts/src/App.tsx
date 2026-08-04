import React from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import Services from './components/Services';
import Coverage from './components/Coverage';
import WhyTrackFlow from './components/WhyTrackFlow';
import Contact from './components/Contact';
import LeadForm from './components/LeadForm';
import Footer from './components/Footer';

const App = () => (
  <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
    <Header />
    <main className="flex-1">
      <Hero />
      <Services />
      <Coverage />
      <WhyTrackFlow />
      <Contact />
      <LeadForm />
    </main>
    <Footer />
  </div>
);

export default App;
