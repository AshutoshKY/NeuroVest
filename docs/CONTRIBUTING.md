# Contributing Guide

## Development Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/AshutoshKY/NeuroVest.git
    cd NeuroVest
    ```

2.  **Install Dependencies**
    *   Backend: `cd backend && pip install -r requirements.txt`
    *   Frontend: `cd frontend && npm install --legacy-peer-deps`

3.  **Run Tests**
    *   Backend: `cd backend && python test_backend_comprehensive.py`
    *   Frontend: `cd frontend && npm run lint && npm run build`

## Pull Request Process

1.  Create a feature branch: `git checkout -b feature/my-feature`
2.  Commit changes: `git commit -m "feat: Add my feature"`
3.  Push to branch: `git push origin feature/my-feature`
4.  Open a Pull Request against `main`
