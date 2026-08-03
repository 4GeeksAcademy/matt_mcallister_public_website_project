"use client";

import { apiUrls, parseApiError } from "@/lib/api";
import { FormEvent, useMemo, useState } from "react";

type Volume = "" | "0-100" | "101-500" | "501-2000" | "2000+" | "Not sure";
type Country = "" | "United States" | "Spain" | "Both" | "Other";
type ProductType = "" | "Fashion" | "Electronics" | "Cosmetics" | "Food" | "Other";
type Has3pl = "" | "Yes" | "No" | "Evaluating options";

type FormData = {
  companyName: string;
  contactPerson: string;
  email: string;
  phone: string;
  website: string;
  country: Country;
  productType: ProductType;
  monthlyVolume: Volume;
  has3pl: Has3pl;
  services: string[];
  comments: string;
  privacy: boolean;
};

type SubmitPhase = "idle" | "loading" | "fulfilled" | "rejected";

type Status = {
  kind: "success" | "error";
  message: string;
} | null;

const initialData: FormData = {
  companyName: "",
  contactPerson: "",
  email: "",
  phone: "",
  website: "",
  country: "",
  productType: "",
  monthlyVolume: "",
  has3pl: "",
  services: [],
  comments: "",
  privacy: false,
};

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const phoneRegex = /^\+\d[\d\s-]{6,}$/;

const errorMessages = {
  companyName: "Company name must have at least 2 characters",
  contactPerson: "Enter first and last name of contact",
  email: "Enter a valid corporate email (example: name@company.com)",
  phone: "Phone must include country code (example: +1 213 555 0147)",
  website: "If you include website, it must be a valid URL",
  country: "Select main operating country",
  productType: "Select the type of product you handle",
  monthlyVolume: "Select estimated monthly volume",
  has3pl: "Indicate if you currently work with another logistics provider",
  services: "Select at least one service of interest",
  comments: "Comments cannot exceed 500 characters",
  privacy: "You must accept the privacy policy to continue",
};

const calculateLeadScore = (data: FormData) => {
  const volumeScores: Record<Exclude<Volume, "">, number> = {
    "0-100": 10,
    "101-500": 25,
    "501-2000": 40,
    "2000+": 50,
    "Not sure": 15,
  };

  const countryScores: Record<Exclude<Country, "">, number> = {
    "United States": 20,
    Spain: 20,
    Both: 30,
    Other: 10,
  };

  let score = 0;

  if (data.monthlyVolume) score += volumeScores[data.monthlyVolume];
  if (data.country) score += countryScores[data.country];
  score += data.services.length * 10;

  if (data.has3pl === "Evaluating options") score += 15;
  if (data.has3pl === "Yes") score += 10;

  if (["Fashion", "Electronics", "Cosmetics"].includes(data.productType)) {
    score += 15;
  }

  if (score >= 90) return { score, tier: "High fit", route: "Priority sales queue" };
  if (score >= 60) return { score, tier: "Medium fit", route: "Qualified nurture queue" };
  return { score, tier: "Low fit", route: "Exploratory follow-up queue" };
};

export default function LeadForm() {
  const [formData, setFormData] = useState<FormData>(initialData);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [status, setStatus] = useState<Status>(null);
  const [submitPhase, setSubmitPhase] = useState<SubmitPhase>("idle");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const remainingChars = 500 - formData.comments.length;
  const showVolumeWarning =
    formData.monthlyVolume === "0-100" && formData.productType !== "";

  const statusClass = useMemo(() => {
    if (!status) return "";
    if (status.kind === "success") {
      return "rounded-md border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-900";
    }
    return "rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900";
  }, [status]);

  const setField = <K extends keyof FormData>(name: K, value: FormData[K]) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setStatus(null);
  };

  const toggleService = (service: string) => {
    const next = formData.services.includes(service)
      ? formData.services.filter((item) => item !== service)
      : [...formData.services, service];

    setField("services", next);
  };

  const validate = () => {
    const nextErrors: Partial<Record<keyof FormData, string>> = {};

    if (formData.companyName.trim().length < 2) {
      nextErrors.companyName = errorMessages.companyName;
    }

    const contactWords = formData.contactPerson.trim().split(/\s+/).filter(Boolean);
    if (contactWords.length < 2) {
      nextErrors.contactPerson = errorMessages.contactPerson;
    }

    if (!emailRegex.test(formData.email.trim())) {
      nextErrors.email = errorMessages.email;
    }

    if (!phoneRegex.test(formData.phone.trim())) {
      nextErrors.phone = errorMessages.phone;
    }

    if (formData.website.trim() !== "") {
      let valid = true;
      try {
        const url = new URL(formData.website.trim());
        valid = url.protocol === "http:" || url.protocol === "https:";
      } catch {
        valid = false;
        if (process.env.NODE_ENV === "development") {
          console.warn("Invalid website URL provided in lead form.");
        }
      }

      if (!valid) {
        nextErrors.website = errorMessages.website;
      }
    }

    if (!formData.country) nextErrors.country = errorMessages.country;
    if (!formData.productType) nextErrors.productType = errorMessages.productType;
    if (!formData.monthlyVolume) nextErrors.monthlyVolume = errorMessages.monthlyVolume;
    if (!formData.has3pl) nextErrors.has3pl = errorMessages.has3pl;
    if (!formData.services.length) nextErrors.services = errorMessages.services;
    if (remainingChars < 0) nextErrors.comments = errorMessages.comments;
    if (!formData.privacy) nextErrors.privacy = errorMessages.privacy;

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validate()) {
      setSubmitPhase("rejected");
      setStatus({
        kind: "error",
        message:
          "Please review the highlighted fields and try again. If you need help, contact comercial@trackflow.com.",
      });
      return;
    }

    const score = calculateLeadScore(formData);
    const payload = {
      ...formData,
      createdAt: new Date().toISOString(),
      leadScore: score.score,
      leadTier: score.tier,
      assignedRoute: score.route,
    };

    setSubmitPhase("loading");
    setIsSubmitting(true);
    setStatus(null);

    try {
      const response = await fetch(apiUrls.leads, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const message = await parseApiError(response);
        setSubmitPhase("rejected");
        setStatus({
          kind: "error",
          message: `${message} If the problem continues, contact comercial@trackflow.com.`,
        });
        return;
      }

      const body = (await response.json()) as { message?: string };

      setSubmitPhase("fulfilled");
      setStatus({
        kind: "success",
        message:
          body.message ??
          "Thank you for your interest in TrackFlow! We have received your request. Our commercial team will contact you within the next 24-48 hours.",
      });
      setFormData(initialData);
      setErrors({});
    } catch {
      setSubmitPhase("rejected");
      setStatus({
        kind: "error",
        message:
          "We could not send your request right now. Check your connection and try again, or email comercial@trackflow.com directly.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="rounded-2xl bg-white p-6 shadow-md" noValidate onSubmit={handleSubmit}>
      {submitPhase === "loading" ? (
        <div
          className="rounded-md border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900"
          role="status"
          aria-live="polite"
        >
          Sending your request…
        </div>
      ) : null}

      {status ? (
        <div className={statusClass} role="status" aria-live="polite">
          {status.message ?? "An unexpected error occurred."}
          {status.kind === "success" ? (
            <>
              {" "}
              If urgent, email{" "}
              <a className="link" href="mailto:comercial@trackflow.com">
                comercial@trackflow.com
              </a>
              .
            </>
          ) : null}
        </div>
      ) : null}

      {showVolumeWarning ? (
        <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900" role="alert">
          For volumes under 100 monthly shipments, our services might not be the most efficient solution. Are you sure you want to continue?
        </div>
      ) : null}

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <div className="md:col-span-2">
          <label className="form-label" htmlFor="companyName">Company name *</label>
          <input className={`form-input ${errors.companyName ? "input-invalid" : ""}`} id="companyName" value={formData.companyName} onChange={(e) => setField("companyName", e.target.value)} />
          <p className="form-error">{errors.companyName ?? ""}</p>
        </div>

        <div className="md:col-span-2">
          <label className="form-label" htmlFor="contactPerson">Contact person *</label>
          <input className={`form-input ${errors.contactPerson ? "input-invalid" : ""}`} id="contactPerson" value={formData.contactPerson} onChange={(e) => setField("contactPerson", e.target.value)} />
          <p className="form-error">{errors.contactPerson ?? ""}</p>
        </div>

        <div>
          <label className="form-label" htmlFor="email">Corporate email *</label>
          <input className={`form-input ${errors.email ? "input-invalid" : ""}`} id="email" type="email" value={formData.email} onChange={(e) => setField("email", e.target.value)} />
          <p className="form-error">{errors.email ?? ""}</p>
        </div>

        <div>
          <label className="form-label" htmlFor="phone">Phone *</label>
          <input className={`form-input ${errors.phone ? "input-invalid" : ""}`} id="phone" placeholder="+1 213 555 0147" value={formData.phone} onChange={(e) => setField("phone", e.target.value)} />
          <p className="form-error">{errors.phone ?? ""}</p>
        </div>

        <div className="md:col-span-2">
          <label className="form-label" htmlFor="website">Company website</label>
          <input className={`form-input ${errors.website ? "input-invalid" : ""}`} id="website" placeholder="https://example.com" value={formData.website} onChange={(e) => setField("website", e.target.value)} />
          <p className="form-error">{errors.website ?? ""}</p>
        </div>

        <div>
          <label className="form-label" htmlFor="country">Main operating country *</label>
          <select className={`form-input ${errors.country ? "input-invalid" : ""}`} id="country" value={formData.country} onChange={(e) => setField("country", e.target.value as Country)}>
            <option value="">Select one option</option>
            <option value="United States">United States</option>
            <option value="Spain">Spain</option>
            <option value="Both">Both</option>
            <option value="Other">Other</option>
          </select>
          <p className="form-error">{errors.country ?? ""}</p>
        </div>

        <div>
          <label className="form-label" htmlFor="productType">Product type *</label>
          <select className={`form-input ${errors.productType ? "input-invalid" : ""}`} id="productType" value={formData.productType} onChange={(e) => setField("productType", e.target.value as ProductType)}>
            <option value="">Select one option</option>
            <option value="Fashion">Fashion</option>
            <option value="Electronics">Electronics</option>
            <option value="Cosmetics">Cosmetics</option>
            <option value="Food">Food</option>
            <option value="Other">Other</option>
          </select>
          <p className="form-error">{errors.productType ?? ""}</p>
        </div>

        <div>
          <label className="form-label" htmlFor="monthlyVolume">Estimated monthly shipping volume *</label>
          <select className={`form-input ${errors.monthlyVolume ? "input-invalid" : ""}`} id="monthlyVolume" value={formData.monthlyVolume} onChange={(e) => setField("monthlyVolume", e.target.value as Volume)}>
            <option value="">Select one option</option>
            <option value="0-100">0-100</option>
            <option value="101-500">101-500</option>
            <option value="501-2000">501-2000</option>
            <option value="2000+">2000+</option>
            <option value="Not sure">Not sure</option>
          </select>
          <p className="form-error">{errors.monthlyVolume ?? ""}</p>
        </div>

        <fieldset>
          <legend className="form-label">Do you currently work with another 3PL? *</legend>
          <div className="mt-2 flex flex-wrap gap-4 text-sm">
            {(["Yes", "No", "Evaluating options"] as Has3pl[]).map((value) => (
              <label key={value}>
                <input className="mr-2" checked={formData.has3pl === value} onChange={() => setField("has3pl", value)} type="radio" name="has3pl" />
                {value}
              </label>
            ))}
          </div>
          <p className="form-error">{errors.has3pl ?? ""}</p>
        </fieldset>

        <fieldset className="md:col-span-2">
          <legend className="form-label">Services of interest * (select one or more)</legend>
          <div className="mt-2 grid gap-2 text-sm sm:grid-cols-3">
            {["Warehousing", "Last mile", "Reverse logistics"].map((service) => (
              <label key={service}>
                <input className="mr-2" type="checkbox" checked={formData.services.includes(service)} onChange={() => toggleService(service)} />
                {service}
              </label>
            ))}
          </div>
          <p className="form-error">{errors.services ?? ""}</p>
        </fieldset>

        <div className="md:col-span-2">
          <label className="form-label" htmlFor="comments">Comments or specific needs</label>
          <textarea className={`form-input ${errors.comments ? "input-invalid" : ""}`} id="comments" rows={4} maxLength={550} value={formData.comments} onChange={(e) => setField("comments", e.target.value)} />
          <div className="mt-1 flex justify-between text-xs text-ink/70">
            <p className="form-error">{errors.comments ?? ""}</p>
            <p>{remainingChars} characters remaining</p>
          </div>
        </div>

        <div className="md:col-span-2">
          <label className="inline-flex items-start gap-3 text-sm">
            <input className="mt-1" type="checkbox" checked={formData.privacy} onChange={(e) => setField("privacy", e.target.checked)} />
            <span>I accept the privacy policy *</span>
          </label>
          <p className="form-error">{errors.privacy ?? ""}</p>
        </div>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-8 rounded-md bg-ocean px-6 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-ocean/50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Sending…" : "Submit request"}
      </button>
    </form>
  );
}
