# AgriHelp 🌾

AgriHelp is a Django-based web application built to help farmers manage their land, track crop cycles, log expenses and yields, and discover government schemes they're eligible for — with the help of AI.

## Features

- **Farmer Profiles** — Register farmers with a unique farmer code, land area, state, district, and category (General/SC/ST/OBC), with support for tracking Kisan Credit Card (KCC) status.
- **Crop Cycle Management** — Track active and harvested crops per farmer, with automatic validation to prevent allocating more land than a farmer owns.
- **Expense Tracking** — Log expenses per crop cycle, with support for uploading receipt images.
- **Yield & Income Tracking** — Record quantity produced, selling price, and sale receipts for each harvested crop.
- **AI-Powered Scheme Recommendations** — Uses Google's Gemini AI to suggest relevant government agricultural schemes based on a farmer's profile, complete with eligibility criteria, benefits, and reference links.
- **PDF Reports** — Generate PDF documents (e.g. reports/receipts) via `xhtml2pdf`.
- **Progressive Web App (PWA)** — Installable on mobile and desktop for offline-friendly access.
- **Multi-language Support** — Localization support via Django's `locale` framework.

## Tech Stack

- **Backend:** Django 5.2.5
- **Database:** MySQL (`mysqlclient`)
- **AI:** Google Generative AI (Gemini)
- **PDF Generation:** xhtml2pdf
- **PWA:** django-pwa
- **Other:** Pillow (image handling), python-dotenv, Gunicorn, Whitenoise

## Getting Started

### Prerequisites

- Python 3.x
- MySQL server
- A Google Gemini API key

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/AbhishekPandey-10/AgriHelp.git
   cd AgriHelp
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables

   Copy `.env.example` to `.env` and fill in the required values (database credentials, Gemini API key, Django secret key, etc.)
   ```bash
   cp .env.example .env
   ```

5. Apply migrations
   ```bash
   python manage.py migrate
   ```

6. Run the development server
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
AgriHelp/
├── config/            # Project configuration
├── core/               # Core app logic
├── locale/             # Translations
├── staticfiles/        # Static assets
├── models.py            # Farmer, CropCycle, Expense, Yield, SchemeRecommendation models
├── views.py              # Application views
├── forms.py               # Django forms
├── admin.py                # Admin panel configuration
├── gemini_service.py        # Gemini AI integration for scheme recommendations
├── requirements.txt          # Python dependencies
└── manage.py                  # Django management script
```

## Contributors

AgriHelp was built in collaboration with:

- **Abhishek Pandey** ([@AbhishekPandey-10](https://github.com/AbhishekPandey-10))
- **Raktima Sengupta**
- **Minal Nain**
