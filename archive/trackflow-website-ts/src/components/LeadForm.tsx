import React, { useState } from 'react';


const initialState = {
  companyName: '',
  contactPerson: '',
  email: '',
  phone: '',
  website: '',
  country: '',
  productType: '',
  volume: '',
  services: [] as string[],
  current3PL: '',
  comments: '',
  privacy: false,
};

type State = typeof initialState;
type ErrorState = Partial<Record<keyof State, string>>;

const serviceOptions = [
  'Warehousing',
  'Last mile',
  'Reverse logistics',
];
const countryOptions = [
  'United States',
  'Spain',
  'Both',
  'Other',
];
const productOptions = [
  'Fashion',
  'Electronics',
  'Cosmetics',
  'Food',
  'Other',
];
const volumeOptions = [
  '0-100',
  '101-500',
  '501-2000',
  '2000+',
  'Not sure',
];

const LeadForm = () => {
  const [form, setForm] = React.useState<State>(initialState);
  const [errors, setErrors] = React.useState<ErrorState>({});
  const [submitted, setSubmitted] = React.useState(false);
  const [showWarning, setShowWarning] = React.useState(false);

  const validate = (f: State): ErrorState => {
    const e: ErrorState = {};
    if (f.companyName.trim().length < 2) e.companyName = 'Company name must have at least 2 characters';
    if (!/^\w+\s+\w+/.test(f.contactPerson.trim())) e.contactPerson = 'Enter first and last name of contact';
    if (!/^\S+@\S+\.\S+$/.test(f.email.trim())) e.email = 'Enter a valid corporate email (example: <name@company.com>)';
    if (!/^\+\d+\s?.+/.test(f.phone.trim())) e.phone = 'Phone must include country code (example: +1 213 555 0147)';
    if (f.website && !/^https?:\/\//.test(f.website.trim())) e.website = 'If you include website, it must be a valid URL';
    if (!f.country) e.country = 'Select main operating country';
    if (!f.productType) e.productType = 'Select the type of product you handle';
    if (!f.volume) e.volume = 'Select estimated monthly volume';
    if (!f.services.length) e.services = 'Select at least one service of interest';
    if (!f.current3PL) e.current3PL = 'Indicate if you currently work with another logistics provider';
    if (f.comments.length > 500) e.comments = `Comments cannot exceed 500 characters (${500 - f.comments.length} remaining)`;
    if (!f.privacy) e.privacy = 'You must accept the privacy policy to continue';
    return e;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' && name === 'privacy' ? checked : type === 'checkbox' ? checked
        ? [...(prev.services as string[]), value]
        : (prev.services as string[]).filter((s) => s !== value)
        : value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const eObj = validate(form);
    setErrors(eObj);
    if (Object.keys(eObj).length === 0) {
      setSubmitted(true);
    }
  };

  React.useEffect(() => {
    setShowWarning(form.volume === '0-100' && !!form.productType);
  }, [form.volume, form.productType]);

  if (submitted) {
    return (
      <section className="py-16 bg-white" id="leadform">
        <div className="container mx-auto px-4 max-w-2xl text-center">
          <h2 className="text-2xl font-bold mb-4 text-green-700">Thank you for your interest in TrackFlow!</h2>
          <p className="mb-4">We have received your request. Our commercial team will review your information and contact you within the next 24-48 hours to schedule a call and learn about your logistics needs in detail.</p>
          <p>If you have any urgent inquiry, write to us directly at <a href="mailto:comercial@trackflow.com" className="text-blue-700 underline">comercial@trackflow.com</a></p>
        </div>
      </section>
    );
  }

  return (
    <section className="py-16 bg-white" id="leadform">
      <div className="container mx-auto px-4 max-w-2xl">
        <h2 className="text-2xl font-bold mb-8 text-center">Request Information</h2>
        <form className="space-y-6" aria-label="Information request form" onSubmit={handleSubmit} noValidate>
          <div>
            <label htmlFor="companyName" className="block font-semibold">Company name *</label>
            <input id="companyName" name="companyName" type="text" className="input" value={form.companyName} onChange={handleChange} required minLength={2} aria-invalid={!!errors.companyName} aria-describedby="companyName-error" />
            {errors.companyName && <div className="text-red-600 text-sm" id="companyName-error">{errors.companyName}</div>}
          </div>
          <div>
            <label htmlFor="contactPerson" className="block font-semibold">Contact person *</label>
            <input id="contactPerson" name="contactPerson" type="text" className="input" value={form.contactPerson} onChange={handleChange} required aria-invalid={!!errors.contactPerson} aria-describedby="contactPerson-error" />
            {errors.contactPerson && <div className="text-red-600 text-sm" id="contactPerson-error">{errors.contactPerson}</div>}
          </div>
          <div>
            <label htmlFor="email" className="block font-semibold">Corporate email *</label>
            <input id="email" name="email" type="email" className="input" value={form.email} onChange={handleChange} required aria-invalid={!!errors.email} aria-describedby="email-error" />
            {errors.email && <div className="text-red-600 text-sm" id="email-error">{errors.email}</div>}
          </div>
          <div>
            <label htmlFor="phone" className="block font-semibold">Phone *</label>
            <input id="phone" name="phone" type="tel" className="input" value={form.phone} onChange={handleChange} required aria-invalid={!!errors.phone} aria-describedby="phone-error" />
            {errors.phone && <div className="text-red-600 text-sm" id="phone-error">{errors.phone}</div>}
          </div>
          <div>
            <label htmlFor="website" className="block font-semibold">Company website</label>
            <input id="website" name="website" type="url" className="input" value={form.website} onChange={handleChange} aria-invalid={!!errors.website} aria-describedby="website-error" />
            {errors.website && <div className="text-red-600 text-sm" id="website-error">{errors.website}</div>}
          </div>
          <div>
            <label htmlFor="country" className="block font-semibold">Main operating country *</label>
            <select id="country" name="country" className="input" value={form.country} onChange={handleChange} required aria-invalid={!!errors.country} aria-describedby="country-error">
              <option value="">Select...</option>
              {countryOptions.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            {errors.country && <div className="text-red-600 text-sm" id="country-error">{errors.country}</div>}
          </div>
          <div>
            <label htmlFor="productType" className="block font-semibold">Product type *</label>
            <select id="productType" name="productType" className="input" value={form.productType} onChange={handleChange} required aria-invalid={!!errors.productType} aria-describedby="productType-error">
              <option value="">Select...</option>
              {productOptions.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
            {errors.productType && <div className="text-red-600 text-sm" id="productType-error">{errors.productType}</div>}
          </div>
          <div>
            <label htmlFor="volume" className="block font-semibold">Estimated monthly shipping volume *</label>
            <select id="volume" name="volume" className="input" value={form.volume} onChange={handleChange} required aria-invalid={!!errors.volume} aria-describedby="volume-error">
              <option value="">Select...</option>
              {volumeOptions.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
            {errors.volume && <div className="text-red-600 text-sm" id="volume-error">{errors.volume}</div>}
          </div>
          {showWarning && (
            <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-2" role="alert">
              For volumes under 100 monthly shipments, our services might not be the most efficient solution. Are you sure you want to continue?
            </div>
          )}
          <div>
            <span className="block font-semibold mb-2">Services of interest *</span>
            <div className="flex flex-wrap gap-4">
              {serviceOptions.map((s) => (
                <label key={s} className="inline-flex items-center">
                  <input type="checkbox" name="services" value={s} checked={form.services.includes(s)} onChange={handleChange} className="mr-2" />
                  {s}
                </label>
              ))}
            </div>
            {errors.services && <div className="text-red-600 text-sm">{errors.services}</div>}
          </div>
          <div>
            <span className="block font-semibold mb-2">Do you currently work with another 3PL? *</span>
            <div className="flex gap-6">
              {['Yes', 'No', 'Evaluating options'].map((opt) => (
                <label key={opt} className="inline-flex items-center">
                  <input type="radio" name="current3PL" value={opt} checked={form.current3PL === opt} onChange={handleChange} className="mr-2" />
                  {opt}
                </label>
              ))}
            </div>
            {errors.current3PL && <div className="text-red-600 text-sm">{errors.current3PL}</div>}
          </div>
          <div>
            <label htmlFor="comments" className="block font-semibold">Comments or specific needs</label>
            <textarea id="comments" name="comments" className="input" value={form.comments} onChange={handleChange} maxLength={500} rows={4} aria-invalid={!!errors.comments} aria-describedby="comments-error comments-counter" />
            <div className="flex justify-between text-xs text-gray-500">
              <span id="comments-counter">{500 - form.comments.length} characters remaining</span>
              {errors.comments && <span className="text-red-600" id="comments-error">{errors.comments}</span>}
            </div>
          </div>
          <div className="flex items-center">
            <input id="privacy" name="privacy" type="checkbox" checked={form.privacy} onChange={handleChange} className="mr-2" required aria-invalid={!!errors.privacy} aria-describedby="privacy-error" />
            <label htmlFor="privacy" className="font-semibold">I accept the privacy policy *</label>
          </div>
          {errors.privacy && <div className="text-red-600 text-sm" id="privacy-error">{errors.privacy}</div>}
          <button type="submit" className="w-full bg-blue-700 text-white py-3 rounded font-bold hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 transition">Submit</button>
        </form>
      </div>
    </section>
  );
};

export default LeadForm;
