# DualGauge Dashboard

Interactive dashboard for visualizing DualGauge benchmark results — joint security-functionality benchmarking of specification-only code generation by LLMs and coding agents.

**Live site:** [srestlabub.github.io/DualGauge](https://srestlabub.github.io/DualGauge/)

## Tech Stack

- **Next.js 15** (App Router, static export)
- **React 19** with TypeScript
- **Tailwind CSS 4** for styling
- **Framer Motion** for scroll animations
- **React Query** for data management
- **react-icons** for iconography

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page — overview, motivation, benchmark details, system architecture, metrics, and key findings |
| `/leaderboard` | Interactive model leaderboard with filtering, sorting, and per-model detail modals |

## Project Structure

```
src/
├── app/              # Next.js pages and layout
│   ├── page.tsx      # Home page
│   ├── layout.tsx    # Root layout with theme persistence
│   └── leaderboard/  # Leaderboard page
├── components/       # React components (Navbar, HeroSection, MetricsSection, etc.)
├── data/             # Static model benchmark data (13 models, 3 languages)
├── types/            # TypeScript interfaces
├── hooks/            # Custom hooks (useActiveSection)
└── utils/            # Utility functions
```

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard locally.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server |
| `npm run dev:turbo` | Start dev server with Turbopack |
| `npm run build` | Production build (static export to `dist/`) |
| `npm run lint` | Run ESLint |

## Deployment

The site is deployed as a static export to GitHub Pages via the `docs/` folder.

```bash
npm run build
```

The `postbuild` script automatically copies `dist/` to `../docs/` and adds a `.nojekyll` file (required so GitHub Pages serves the `_next/` directory). Commit and push `docs/` to deploy.

## Data

Benchmark data is embedded in `src/data/models.ts` — 13 models (10 LLMs + 3 agentic systems) with per-language metrics (Python, C++, JavaScript) including pass@1, secure@1, secure-pass@1, PR, and SPR.
