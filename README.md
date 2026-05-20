# Talk Sensor

**Talk Sensor** is an AI-driven, automated quality assurance pipeline for coffee shops. It analyzes audio recordings of barista-customer interactions, slices them into manageable clips, and scores them based on service standards.

---

## 📂 Project Documentation

We maintain a central `docs/` folder with detailed information about the project:

- 📑 **[PRD (Product Requirements Document)](file:///e:/talk/docs/PRD.md)**: Vision, features, and roadmap.
- 🏗️ **[Architecture Overview](file:///e:/talk/docs/ARCHITECTURE.md)**: System design and data flow.
- ⚙️ **[Setup Guide](file:///e:/talk/docs/SETUP.md)**: How to configure the pipeline and dashboard.
- 🤖 **[AI Prompts & Logic](file:///e:/talk/docs/PROMPTS.md)**: Detailed breakdown of the Gemini instructions.

---

## 🚀 Quick Structure

- **`pipeline/`**: Python orchestrator that fetches, analyzes, and slices audio recordings.
- **`dashboard/`**: Next.js PWA to view and analyze metrics across different shop locations.
- **`docs/`**: Central hub for all technical and product documentation.

---

## 🛠️ Main Tech Stack

| Component | Technology |
| :--- | :--- |
| **Logic** | Python 3.9+ |
| **Interface** | Next.js (TypeScript) |
| **AI Engine** | Google Gemini 1.5 Flash |
| **Infrastructure** | Supabase (PostgreSQL + Storage) |
| **Communication** | Yandex Disk API |
| **Processing** | FFmpeg |

---

## ⚡ Quick Start

1.  Copy `.env.example` to `.env`.
2.  Follow the **[Setup Guide](file:///e:/talk/docs/SETUP.md)**.
3.  Upload an audio file to your Yandex Disk target folder.
4.  Run `python pipeline/main.py`.
