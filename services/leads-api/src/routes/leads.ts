import { Router } from "express";
import { ApiError } from "../types/errors.js";

const router = Router();

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const phoneRegex = /^\+\d[\d\s-]{6,}$/;

type LeadPayload = {
  companyName?: string;
  contactPerson?: string;
  email?: string;
  phone?: string;
  website?: string;
  country?: string;
  productType?: string;
  monthlyVolume?: string;
  has3pl?: string;
  services?: string[];
  comments?: string;
  privacy?: boolean;
};

const validateLead = (body: LeadPayload): Record<string, string> => {
  const fields: Record<string, string> = {};

  if (!body.companyName || body.companyName.trim().length < 2) {
    fields.companyName = "Company name must have at least 2 characters";
  }

  const contactWords = (body.contactPerson ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (contactWords.length < 2) {
    fields.contactPerson = "Enter first and last name of contact";
  }

  if (!body.email || !emailRegex.test(body.email.trim())) {
    fields.email = "Enter a valid corporate email (example: name@company.com)";
  }

  if (!body.phone || !phoneRegex.test(body.phone.trim())) {
    fields.phone = "Phone must include country code (example: +1 213 555 0147)";
  }

  if (body.website && body.website.trim() !== "") {
    let valid = true;
    try {
      const url = new URL(body.website.trim());
      valid = url.protocol === "http:" || url.protocol === "https:";
    } catch {
      valid = false;
    }
    if (!valid) {
      fields.website = "If you include website, it must be a valid URL";
    }
  }

  if (!body.country) {
    fields.country = "Select main operating country";
  }
  if (!body.productType) {
    fields.productType = "Select the type of product you handle";
  }
  if (!body.monthlyVolume) {
    fields.monthlyVolume = "Select estimated monthly volume";
  }
  if (!body.has3pl) {
    fields.has3pl =
      "Indicate if you currently work with another logistics provider";
  }
  if (!body.services?.length) {
    fields.services = "Select at least one service of interest";
  }
  if ((body.comments?.length ?? 0) > 500) {
    fields.comments = "Comments cannot exceed 500 characters";
  }
  if (!body.privacy) {
    fields.privacy = "You must accept the privacy policy to continue";
  }

  return fields;
};

router.post("/", (req, res, next) => {
  try {
    const fieldErrors = validateLead(req.body as LeadPayload);

    if (Object.keys(fieldErrors).length > 0) {
      throw new ApiError(
        400,
        "VALIDATION_ERROR",
        "Please review the highlighted fields and try again.",
        fieldErrors,
      );
    }

    const leadId = `lead_${Date.now()}`;

    res.status(201).json({
      success: true,
      leadId,
      message:
        "Thank you for your interest in TrackFlow! We have received your request. Our commercial team will contact you within the next 24-48 hours.",
    });
  } catch (error) {
    next(error);
  }
});

export default router;
