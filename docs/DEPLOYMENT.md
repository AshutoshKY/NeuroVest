# Deployment Guide

## Prerequisites

*   Docker & Docker Compose
*   Git

## Quick Start (Production)

1.  **Clone the repository**
    ```bash
    git clone https://github.com/AshutoshKY/NeuroVest.git
    ```

2.  **Configure Environment**
    *   Copy `backend/.env.example` to `backend/.env`
    *   Set production secrets (DB Password, API Keys).

3.  **Run with Docker Compose**
    ```bash
    docker compose up -d --build
    ```

## CI/CD Pipeline

Deployments are managed via GitHub Actions.
*   **Push to main**: Triggers Build & Test.
*   **Release**: Triggers Deployment (Template).
