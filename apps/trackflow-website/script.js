const form = document.getElementById('lead-form');
const statusBox = document.getElementById('form-status');
const volumeWarning = document.getElementById('volume-warning');
const comments = document.getElementById('comments');
const commentsCounter = document.getElementById('commentsCounter');

const fields = {
  companyName: document.getElementById('companyName'),
  contactPerson: document.getElementById('contactPerson'),
  email: document.getElementById('email'),
  phone: document.getElementById('phone'),
  website: document.getElementById('website'),
  country: document.getElementById('country'),
  productType: document.getElementById('productType'),
  monthlyVolume: document.getElementById('monthlyVolume'),
  comments: comments,
  privacy: document.getElementById('privacy')
};

const errorMessages = {
  companyName: 'Company name must have at least 2 characters',
  contactPerson: 'Enter first and last name of contact',
  email: 'Enter a valid corporate email (example: name@company.com)',
  phone: 'Phone must include country code (example: +1 213 555 0147)',
  website: 'If you include website, it must be a valid URL',
  country: 'Select main operating country',
  productType: 'Select the type of product you handle',
  monthlyVolume: 'Select estimated monthly volume',
  services: 'Select at least one service of interest',
  has3pl: 'Indicate if you currently work with another logistics provider',
  comments: 'Comments cannot exceed 500 characters (X remaining)',
  privacy: 'You must accept the privacy policy to continue'
};

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const phoneRegex = /^\+\d[\d\s-]{6,}$/;

function setError(fieldName, message) {
  const errorNode = document.getElementById(`${fieldName}Error`);
  if (!errorNode) return;

  errorNode.textContent = message;

  if (fields[fieldName]) {
    fields[fieldName].classList.add('input-invalid');
    fields[fieldName].setAttribute('aria-invalid', 'true');
    fields[fieldName].setAttribute('aria-describedby', `${fieldName}Error`);
  }
}

function clearError(fieldName) {
  const errorNode = document.getElementById(`${fieldName}Error`);
  if (!errorNode) return;

  errorNode.textContent = '';

  if (fields[fieldName]) {
    fields[fieldName].classList.remove('input-invalid');
    fields[fieldName].removeAttribute('aria-invalid');
  }
}

function clearStatus() {
  statusBox.className = 'hidden rounded-md border px-4 py-3 text-sm';
  statusBox.textContent = '';
}

function showStatus(message, type) {
  if (type === 'success') {
    statusBox.className = 'rounded-md border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-900';
  } else {
    statusBox.className = 'rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900';
  }

  statusBox.innerHTML = message;
}

function getServices() {
  return Array.from(document.querySelectorAll('input[name="services"]:checked')).map((el) => el.value);
}

function get3plValue() {
  const selected = document.querySelector('input[name="has3pl"]:checked');
  return selected ? selected.value : '';
}

function updateWarningBanner() {
  const shouldWarn = fields.monthlyVolume.value === '0-100' && fields.productType.value !== '';
  volumeWarning.classList.toggle('hidden', !shouldWarn);
}

function updateCommentsCounter() {
  const remaining = 500 - comments.value.length;
  commentsCounter.textContent = `${remaining} characters remaining`;

  if (remaining < 0) {
    setError('comments', errorMessages.comments.replace('X', String(remaining)));
  } else {
    clearError('comments');
  }
}

function validateForm() {
  let isValid = true;
  clearStatus();

  Object.keys(fields).forEach((name) => clearError(name));
  clearError('services');
  clearError('has3pl');

  if (fields.companyName.value.trim().length < 2) {
    setError('companyName', errorMessages.companyName);
    isValid = false;
  }

  const contactWords = fields.contactPerson.value.trim().split(/\s+/).filter(Boolean);
  if (contactWords.length < 2) {
    setError('contactPerson', errorMessages.contactPerson);
    isValid = false;
  }

  if (!emailRegex.test(fields.email.value.trim())) {
    setError('email', errorMessages.email);
    isValid = false;
  }

  if (!phoneRegex.test(fields.phone.value.trim())) {
    setError('phone', errorMessages.phone);
    isValid = false;
  }

  if (fields.website.value.trim() !== '') {
    const url = fields.website.value.trim();
    const startsWithProtocol = url.startsWith('http://') || url.startsWith('https://');
    let urlIsValid = true;

    try {
      // URL constructor ensures value is syntactically valid.
      new URL(url);
    } catch {
      urlIsValid = false;
    }

    if (!startsWithProtocol || !urlIsValid) {
      setError('website', errorMessages.website);
      isValid = false;
    }
  }

  if (!fields.country.value) {
    setError('country', errorMessages.country);
    isValid = false;
  }

  if (!fields.productType.value) {
    setError('productType', errorMessages.productType);
    isValid = false;
  }

  if (!fields.monthlyVolume.value) {
    setError('monthlyVolume', errorMessages.monthlyVolume);
    isValid = false;
  }

  if (getServices().length === 0) {
    setError('services', errorMessages.services);
    isValid = false;
  }

  if (!get3plValue()) {
    setError('has3pl', errorMessages.has3pl);
    isValid = false;
  }

  const remaining = 500 - fields.comments.value.length;
  if (remaining < 0) {
    setError('comments', errorMessages.comments.replace('X', String(remaining)));
    isValid = false;
  }

  if (!fields.privacy.checked) {
    setError('privacy', errorMessages.privacy);
    isValid = false;
  }

  return isValid;
}

function calculateLeadScore(data) {
  let score = 0;

  const volumeScores = {
    '0-100': 10,
    '101-500': 25,
    '501-2000': 40,
    '2000+': 50,
    'Not sure': 15
  };

  const countryScores = {
    'United States': 20,
    Spain: 20,
    Both: 30,
    Other: 10
  };

  score += volumeScores[data.monthlyVolume] || 0;
  score += countryScores[data.country] || 0;
  score += data.services.length * 10;

  if (data.has3pl === 'Evaluating options') score += 15;
  if (data.has3pl === 'Yes') score += 10;

  if (['Fashion', 'Electronics', 'Cosmetics'].includes(data.productType)) {
    score += 15;
  }

  if (score >= 90) return { score, tier: 'High fit', route: 'Priority sales queue' };
  if (score >= 60) return { score, tier: 'Medium fit', route: 'Qualified nurture queue' };
  return { score, tier: 'Low fit', route: 'Exploratory follow-up queue' };
}

function buildPayload() {
  const services = getServices();
  const payload = {
    companyName: fields.companyName.value.trim(),
    contactPerson: fields.contactPerson.value.trim(),
    email: fields.email.value.trim(),
    phone: fields.phone.value.trim(),
    website: fields.website.value.trim(),
    country: fields.country.value,
    productType: fields.productType.value,
    monthlyVolume: fields.monthlyVolume.value,
    services,
    has3pl: get3plValue(),
    comments: fields.comments.value.trim(),
    privacyAccepted: fields.privacy.checked,
    createdAt: new Date().toISOString()
  };

  const score = calculateLeadScore(payload);

  return {
    ...payload,
    leadScore: score.score,
    leadTier: score.tier,
    assignedRoute: score.route
  };
}

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const isValid = validateForm();
  updateWarningBanner();

  if (!isValid) {
    showStatus('Please review the highlighted fields and try again.', 'error');
    return;
  }

  const payload = buildPayload();
  console.log('TrackFlow lead payload:', payload);

  showStatus(
    `
    <strong>Thank you for your interest in TrackFlow!</strong><br />
    We have received your request. Our commercial team will review your information and contact you within the next 24-48 hours to schedule a call and learn about your logistics needs in detail.<br />
    If you have any urgent inquiry, write to us directly at <a href="mailto:comercial@trackflow.com" class="link">comercial@trackflow.com</a>
    `,
    'success'
  );

  form.reset();
  updateCommentsCounter();
  updateWarningBanner();
});

['monthlyVolume', 'productType'].forEach((name) => {
  fields[name].addEventListener('change', updateWarningBanner);
});

comments.addEventListener('input', updateCommentsCounter);

Object.keys(fields).forEach((name) => {
  const field = fields[name];
  if (!field || field.type === 'checkbox' || field.type === 'radio') return;
  field.addEventListener('input', () => {
    clearError(name);
    clearStatus();
  });
});

Array.from(document.querySelectorAll('input[name="services"], input[name="has3pl"], #privacy')).forEach((el) => {
  el.addEventListener('change', () => {
    clearError('services');
    clearError('has3pl');
    clearError('privacy');
    clearStatus();
  });
});

updateCommentsCounter();
updateWarningBanner();
