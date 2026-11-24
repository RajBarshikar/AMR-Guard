<p align="center">
  <img src="https://img.shields.io/badge/AMR--Guard-v1.0-0d9488?style=for-the-badge&logo=shieldsdotio&logoColor=white" alt="Version" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PWA-Offline_First-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white" alt="PWA" />
  <img src="https://img.shields.io/badge/TailwindCSS-4.0-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind" />
</p>

<h1 align="center">🛡️ AMR-Guard</h1>
<h3 align="center"><em>Secure Disposal. Stronger Medicine.</em></h3>

<p align="center">
  A mobile-first Progressive Web App empowering Indian citizens to fight<br/>
  <strong>Antimicrobial Resistance (AMR)</strong> through safe medication disposal — no login required.
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-the-problem">The Problem</a> •
  <a href="#%EF%B8%8F-tech-stack">Tech Stack</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 🔴 The Problem

> **700,000+ deaths** occur annually due to drug-resistant infections. By 2050, AMR could claim **10 million lives per year** — more than cancer.

India is the world's largest consumer of antibiotics. Yet there is **no scalable system** for safe disposal of unused or expired medications. When antibiotics are flushed down toilets or thrown in dustbins, they enter rivers, soil, and groundwater — breeding **superbugs** that resist all known medicines.

**AMR-Guard bridges this gap** by putting the power of safe disposal directly in the hands of 1.4 billion citizens.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📸 **Snap & Report** | Scan any medication strip using your phone camera — AI-powered detection identifies the drug, type, and class |
| ☣️ **Eco-Hazard Score** | Every medication receives a 1–10 environmental hazard rating with persistence info |
| 🗺️ **SafeDrop Map** | Find the nearest SafeDrop Pharmacy or Government Health Center with one-tap Google Maps directions |
| 🏆 **Maha-Leaderboard** | City-wise safe disposal competition driving engagement across Maharashtra |
| 🎖️ **Guardian Tiers** | Gamified progression: **Scout** → **Sentinel** → **AMR-Guardian** |
| 📚 **Knowledge Capsules** | Bite-sized AMR education: what it is, why it matters, how you help |
| 🔐 **Anonymous Tracking** | Device-token based — zero personal data, no Aadhaar, no phone number |
| 📱 **QR Disposal Verification** | Pharmacy-verifiable QR codes creating an auditable disposal chain |
| 🌐 **Bilingual** | English + Marathi (Phase 1), expandable to all 22 scheduled languages |
| 📴 **Offline-First** | Scans queue in IndexedDB and auto-sync when connectivity returns |
| 🌙 **Dark Mode** | Full theme support — light and dark — with smooth transitions |

---

## 🛠️ Tech Stack

### Frontend
```
React 19          →  UI framework
Vite 6            →  Build tool (HMR + lightning builds)
TailwindCSS 4     →  Utility-first CSS
vite-plugin-pwa   →  Service workers + offline caching
Leaflet           →  Interactive maps (OSM + CartoDB dark tiles)
IndexedDB (idb)   →  Offline scan queue + history
React Router 7    →  Client-side routing
```

### Backend
```
FastAPI            →  High-performance Python API
Uvicorn            →  ASGI server
Python-Multipart   →  Image upload handling
```

### Design
```
Mobile-first       →  390px primary breakpoint
Glassmorphism      →  Frosted glass nav + overlays
CSS Variables      →  Theme-aware design tokens
Inter (Google)     →  Premium typography
Custom SVG Icons   →  26+ hand-crafted icons (no icon library dependency)
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** ≥ 18
- **Python** ≥ 3.9
- **npm** or **yarn**

### 1. Clone & Install

```bash
git clone https://github.com/your-org/amr-guard.git
cd amr-guard
```

### 2. Start the Backend

```bash
cd backend
pip install fastapi uvicorn python-multipart
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be live at `http://localhost:8000`

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be live at `http://localhost:5173`

> **Note:** Vite proxies `/api` requests to the backend automatically.

### 4. Build for Production

```bash
cd frontend
npm run build
```

Output goes to `frontend/dist/` — ready for deployment.

---

## 🏗 Architecture

```
amr-guard/
├── backend/
│   ├── main.py                    # FastAPI app + CORS
│   └── routes/
│       └── medication.py          # /analyze, /nearest-bins, /leaderboard, /device-token
│
├── frontend/
│   ├── index.html                 # Entry point
│   ├── vite.config.js             # Vite + PWA + proxy config
│   └── src/
│       ├── main.jsx               # React root
│       ├── App.jsx                # Router + onboarding gate
│       ├── index.css              # Design system (themes, cards, animations)
│       ├── components/
│       │   ├── Layout.jsx         # Main shell (content + bottom nav)
│       │   ├── BottomNav.jsx      # 5-tab navigation (Home, Map, Scan, About, Guardian)
│       │   └── Icons.jsx          # 26+ custom SVG icons
│       ├── contexts/
│       │   ├── LanguageContext.jsx # i18n (English + Marathi)
│       │   └── ThemeContext.jsx    # Light/Dark mode
│       ├── pages/
│       │   ├── Welcome.jsx        # Onboarding + language selection
│       │   ├── Home.jsx           # Dashboard: stats, actions, knowledge, leaderboard
│       │   ├── Scanner.jsx        # Camera → AI analysis → Eco-Hazard result
│       │   ├── MapView.jsx        # Leaflet map with SafeDrop locations
│       │   ├── About.jsx          # AMR education + disposal tips
│       │   └── Profile.jsx        # Guardian tiers, QR code, device token
│       └── utils/
│           ├── api.js             # API client helpers
│           └── offlineQueue.js    # IndexedDB scan queue
│
└── README.md
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze-medication` | Upload medication image → returns drug info, Eco-Hazard score, disposal advice |
| `GET` | `/api/v1/nearest-bins?lat=&lng=` | Returns nearby SafeDrop Pharmacies + Govt Health Centers |
| `GET` | `/api/v1/leaderboard` | City-wise disposal rankings (Maha-Leaderboard) |
| `GET` | `/api/v1/device-token` | Generate anonymous device identifier |

### Sample Response — `/analyze-medication`

```json
{
  "drug_name": "Amoxicillin",
  "drug_type": "Capsule",
  "drug_class": "Penicillin",
  "is_antibiotic": true,
  "confidence": 0.94,
  "expiry_status": "expiring_soon",
  "expiry_label": "Expiring Soon (within 30 days)",
  "eco_hazard_score": 8,
  "eco_hazard_info": "Persists in water systems for 60+ days. Strongly promotes resistance gene transfer.",
  "disposal_recommendation": "Do NOT flush. Return to a SafeDrop Pharmacy for incineration."
}
```

---

## 🗺 Roadmap

- [x] **Phase 1 — MVP** (Maharashtra)
  - [x] Medication scanning with AI detection
  - [x] Eco-Hazard scoring (1–10)
  - [x] SafeDrop Pharmacy map with directions
  - [x] Guardian Tier system (Scout/Sentinel/AMR-Guardian)
  - [x] Maha-Leaderboard (city-wise competition)
  - [x] Bilingual support (English + Marathi)
  - [x] Offline-first with IndexedDB queue
  - [x] QR code disposal verification
  - [x] Anonymous device-token tracking

- [ ] **Phase 2 — Scale**
  - [ ] Replace mock ML with YOLOX + OCR inference
  - [ ] Add Hindi, Tamil, Telugu, Kannada, Bengali
  - [ ] Real pharmacy database integration (CDSCO)
  - [ ] Push notifications for expiry reminders
  - [ ] Pharmacy-side verification dashboard

- [ ] **Phase 3 — National**
  - [ ] All 22 scheduled languages
  - [ ] Government reporting dashboard
  - [ ] District-level AMR heatmaps
  - [ ] Integration with National Health Stack (ABDM)
  - [ ] iOS & Android app store wrappers (TWA)

---

## 🤝 Contributing

We welcome contributions! Whether it's:
- 🐛 Bug reports
- 💡 Feature suggestions
- 🌐 Translation help (especially Indian regional languages)
- 🧪 Testing on different devices

Please open an issue or submit a pull request.

---

## 📄 License

This project is built for public health impact. Licensed under [MIT](LICENSE).

---

<p align="center">
  <strong>Every strip you safely dispose makes India stronger against superbugs.</strong><br/>
  <em>Be the change. Scan. Drop. Protect.</em>
</p>

<p align="center">
  Built with ❤️ for India's fight against AMR
</p>
