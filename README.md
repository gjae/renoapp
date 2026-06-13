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

**Production vs Development:** During development, the frontend runs dynamically alongside the backend. For production, RenoApp compiles all assets to serve a unified Single Page Application (SPA). The backend and frontend will communicate strictly via an API architecture, with planned support for real-time communication using WebSockets.

### Metadata Resolution (Fetcher Strategy)
Before an application can be installed, its metadata (`__app__.json` or equivalent payload) must be parsed to understand its dependencies, frontend requirements, and installation scripts. RenoApp uses a **Strategy Pattern** via a `Fetcher` hierarchy to accomplish this cleanly:

- `DictFetcher`: Extracts metadata from a local Python dictionary or internal API request.
- `UrlFetcher`: Downloads the JSON metadata securely from a remote repository via HTTP requests.

The `InstallAppPayload` dataclass acts as the universal language for RenoApp. It uses a fault-tolerant parsing mechanism (`from_dict`) that maps community aliases (e.g., `"depends_on"` to `"dependencies"`) and dynamically filters out unexpected keys, ensuring *forward-compatibility* with future metadata schemas.

```mermaid
graph TD
    classDef payload fill:#2d3748,stroke:#4a5568,color:#fff;
    classDef fetcher fill:#3182ce,stroke:#2b6cb0,color:#fff;
    
    SourceDict[Local Dict Payload] --> DictFetcher((DictFetcher)):::fetcher
    SourceURL[Remote GitHub/Repo URL] --> UrlFetcher((UrlFetcher)):::fetcher
    
    DictFetcher --> |"Raw Data"| DataFilter{{"Data Filter (Alias Mapping & Pruning)"}}
    UrlFetcher --> |"Raw JSON"| DataFilter
    
    DataFilter --> |"Clean Data"| Payload["InstallAppPayload (Dataclass)"]:::payload
    Payload --> Resolver["DAG Resolver"]
```

### Appman (Orchestration Pipeline)
RenoApp includes a robust, transaction-like orchestrator called `Appman` (App Manager). It is designed to safely execute the installation lifecycle of each micro-app.

The installation pipeline follows a strict sequence:
1. `generate_app`: Downloads or clones the app securely using memory-safe chunked streams.
2. `update_settings`: Updates internal settings and the frontend app registry.
3. `install_requirements`: Installs isolated Python packages using the high-performance `uv pip` strategy.
4. `copy_front`: Extracts and copies frontend React components.
5. `run_migrations`: Applies database migrations.
6. `run_post_install_tasks`: Executes custom shell scripts or initialization commands defined by the app in its `post_install_tasks` array.
7. `restart_server`: Reloads the environment to reflect the new app.

**Rollback Mechanism:** `Appman` implements a Command Pattern with an automated LIFO (Last-In, First-Out) stack. If any step fails, it triggers a `rollback()` method that iterates through the stack in reverse, cleanly undoing the executed tasks (e.g., reverting migrations, deleting copied files) to ensure the system's integrity remains uncompromised.

### Dependency Resolver
To support the `depends_on` manifest properties, RenoApp features a recursive `Resolver`. Since application dependencies form a **Directed Acyclic Graph (DAG)**, the resolver uses a Post-Order Depth-First Search (DFS) or Topological Sort to determine the exact installation order.

1. **Resolution:** It recursively traverses all missing dependencies, detecting and preventing circular dependencies.
2. **Flattening:** It flattens the graph into a strictly ordered execution stack, guaranteeing that "Leaf" applications (those with no dependencies) are installed before the "Root" applications that depend on them.
3. **Execution:** The `walk()` generator yields pre-configured `Appman` instances in the correct topological order. This architectural separation opens the door for future optimizations, such as parallelizing the download phase of the apps before executing their database migrations sequentially.

```mermaid
graph TD
    Resolver[Dependency Resolver]
    
    subgraph "DAG Resolution"
        AppB[App: Billing] -. depends_on .-> AppS[App: Sales]
        AppS -. depends_on .-> AppC[App: Contacts]
    end
    
    Resolver -->|1. Parses| AppB
    
    subgraph "Execution Stack (walk)"
        direction LR
        ExeC[1. Install Contacts] --> ExeS[2. Install Sales] --> ExeB[3. Install Billing]
    end
    
    Resolver -->|2. Yields Appman| ExeC
```
### Centralized API Router (Django Ninja)
RenoApp utilizes `django-ninja-extra` to provide a robust, asynchronous, and Pydantic-validated REST API. Instead of having each micro-app instantiate its own isolated API (which would fragment the OpenAPI/Swagger documentation), RenoApp features an **API Façade/Alias** in `reno.router`.

Apps simply import `Router` from `reno.router` to define their endpoints, or `api_controller` and `route` if they prefer Class-Based Views (CBV) for better organization. During startup, the Orchestrator's `urls.py` automatically discovers all `views.py` across installed apps. It mounts standard routers and dynamically registers any controller classes defined in a `controllers` array into a single, unified Central API exposed at `/api/docs`.

### Developer Tools
- `uv run python manage.py show_urls`: Prints a real-time, alphabetized tabular map of all URLs currently registered in the dynamic system, color-highlighting API routes for enhanced Developer Experience (DX).

### Testing
RenoApp employs a strict testing methodology using `pytest`. The architecture is designed to allow business logic and orchestration algorithms to be tested in isolation.

To run the test suite locally:
```bash
uv run pytest -v
```

Specifically, the `Resolver` module includes comprehensive tests (using a `DictAppFinder` mock) to validate the Directed Acyclic Graph logic:
- **Linear Graphs:** Ensures standard sequential dependencies are resolved correctly.
- **Diamond Graphs:** Validates deduplication (e.g. if A depends on B and C, and both depend on D, D is only installed once).
- **Circular Dependencies:** Confirms that infinite loops are detected and blocked before execution.

## License
This project is open-source and free to use, modify, and distribute under the **MIT License**. 

> **IMPORTANT:** You are free to use this system commercially and privately, but you are **obligated to provide attribution and credit** to the original author(s) by maintaining the original license and copyright notices in all copies or substantial portions of the software.
