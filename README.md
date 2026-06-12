# RenoApp (Core Orchestrator)

## Introduction
RenoApp is a base framework built on top of Django designed to act as a central application orchestrator. Instead of developing monolithic features directly within the core, this project allows multiple applications (micro-apps or plugins) to be integrated dynamically and automatically.

## Objective
The main objective of RenoApp is to emulate a modular architecture similar to robust ERPs (like Odoo), but offering a **friendly and modern Developer Experience (DX)**.

Each application within the RenoApp ecosystem:
- Is developed as an independent repository or module.
- Is dynamically discovered and installed when placed in the `apps/` directory.
- Configures itself through an `__app__.json` manifest that defines its routes, dependencies, and settings.
- Remains completely isolated and decoupled from the central codebase.

This design allows development teams to rapidly scale features without modifying the core, reducing bottlenecks and facilitating long-term maintenance.

## Technical Architecture

### Dependency Management
External dependencies are resolved via independent `requirements.txt` files per app. A custom `install_app [app_name]:[version]` command handles the installation pipeline:
1. Clones the independent app repository into the `apps/` directory.
2. Installs the isolated Python requirements.
3. Resolves the internal dependency graph based on the `depends_on` array inside the `__app__.json` manifest.

```mermaid
graph TD
    Core[RenoApp Core Orchestrator]
    
    subgraph "Independent Repositories"
        AppUsers[App: Users]
        AppSales[App: Sales]
        AppBilling[App: Billing]
    end

    Core -->|install_app| AppUsers
    Core -->|install_app| AppSales
    Core -->|install_app| AppBilling
    
    AppSales -. depends_on .-> AppUsers
    AppBilling -. depends_on .-> AppSales
```

### Frontend Integration
Each app is responsible for generating its own frontend assets (e.g., React components). During the `install_app` pipeline, the orchestrator handles the integration automatically:
1. Copies the app's frontend views into a dedicated `frontend/src/apps/` directory within the core.
2. Dynamically rewrites a central registry file (e.g., `apps.config.js`) to inject the newly installed app. This registry contains metadata such as the app's icon, description, and base routing path.
3. Provides a base template to manage the global design and layout.
4. Compiles the final assets.

This ensures each app only worries about its specific UI section, while the Core orchestrates a seamless Single Page Application (SPA) experience.

### Appman (Orchestration Pipeline)
RenoApp includes a robust, transaction-like orchestrator called `Appman` (App Manager). It is designed to safely execute the installation lifecycle of each micro-app.

The installation pipeline follows a strict sequence:
1. `check_reno_dependencies`: Validates the DAG of dependencies to ensure a safe installation order.
2. `generate_app`: Downloads or clones the app.
3. `update_settings`: Updates internal settings and the frontend app registry.
4. `install_requirements`: Installs isolated Python packages.
5. `copy_front`: Extracts and copies frontend React components.
6. `run_migrations`: Applies database migrations.
7. `run_post_install_tasks`: Executes custom shell scripts or initialization commands defined by the app in its `post_install_tasks` array.
8. `restart_server`: Reloads the environment to reflect the new app.

**Rollback Mechanism:** `Appman` implements a Command Pattern with an automated LIFO (Last-In, First-Out) stack. If any step fails, it triggers a `rollback()` method that iterates through the stack in reverse, cleanly undoing the executed tasks (e.g., reverting migrations, deleting copied files) to ensure the system's integrity remains uncompromised.

## License
This project is open-source and free to use, modify, and distribute under the **MIT License**. 

> **IMPORTANT:** You are free to use this system commercially and privately, but you are **obligated to provide attribution and credit** to the original author(s) by maintaining the original license and copyright notices in all copies or substantial portions of the software.
