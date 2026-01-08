# Role-Based Authentication System (Foundation Project)

A beginner-friendly, secure authentication system built with:

- Python
- Streamlit (UI)
- MongoDB (database) via `pymongo`
- `bcrypt` for password hashing
- Streamlit `session_state` for sessions

This is **Phase 1** (authentication only). The backend is modular so you can add optimization modules later.

Phase 2 extends the app into a planning tool foundation:
- Admin user management (roles + enable/disable)
- Plant Management
- Demand Management
- Transport Configuration
- Inventory Policies

## Folder Structure

```
auth-system/
│
├── app.py
│
├── ui/
│   ├── login.py
│   ├── signup.py
│   └── dashboards.py
│   ├── plant_page.py
│   ├── demand_page.py
│   ├── transport_page.py
│   └── inventory_page.py
│
├── backend/
│   ├── __init__.py
│   │
│   ├── database/
│   │   ├── mongo.py
│   │   └── user_repository.py
│   │
│   ├── auth/
│   │   ├── password.py
│   │   ├── auth_service.py
│   │   └── session.py
│   │
│   ├── user/
│   │   └── user_service.py
│   │
│   ├── plant/
│   │   ├── plant_repository.py
│   │   └── plant_service.py
│   │
│   ├── demand/
│   │   ├── demand_repository.py
│   │   └── demand_service.py
│   │
│   ├── transport/
│   │   ├── transport_repository.py
│   │   └── transport_service.py
│   │
│   ├── inventory/
│   │   ├── inventory_repository.py
│   │   └── inventory_service.py
│   │
│   └── middleware/
│       └── role_guard.py
│
├── utils/
│   ├── config.py
│   └── validators.py
│
├── requirements.txt
├── README.md
└── .env.example
```

## How Signup Works

- The user fills the Signup form (name, email, password, role)
- `utils/validators.py` validates inputs
- `backend/auth/password.py` hashes the password using bcrypt
- `backend/database/user_repository.py` writes a new user document into MongoDB
- Email is protected from duplicates using a **unique index** in MongoDB

## How Login Works

- The user fills email + password
- We find the user by email in MongoDB
- We verify the password using bcrypt
- If correct, we store the user info inside `st.session_state` (session)

## How Roles Work

- Each user has exactly one role: `Admin`, `Planner`, or `Viewer`
- After login, `ui/dashboards.py` shows a different dashboard based on role
- If not logged in, `backend/middleware/role_guard.py` blocks access

## Phase 2 Role Permissions (Summary)

- Admin
  - Manage users (change role, enable/disable)
  - Full access to all modules
- Planner
  - Can add/edit Plants, Demands, Transport, Inventory Policies
  - Cannot manage users
  - Cannot delete plants/routes (admin-only in this foundation)
- Viewer
  - Read-only access to all data tables

## MongoDB Setup (Beginner Guide)

### Option A: Local MongoDB (recommended for learning)

1. Install MongoDB Community Server
2. Start the MongoDB service
3. Confirm it is running on:

- `mongodb://localhost:27017`

### Option B: MongoDB Atlas (cloud)

1. Create a free MongoDB Atlas cluster
2. Create a database user
3. Whitelist your IP
4. Copy your connection string and put it in `.env` as `MONGO_URI`

## MongoDB Collections (Phase 2)

This app uses one database (default: `auth_system`) and these collections:

- `users`
  - Fields: `name`, `email`, `password_hash`, `role`, `is_active`, `created_at`
  - Index: unique `email`

- `plants`
  - Fields: `name`, `plant_type`, `location`, `storage_capacity`, `safety_stock`, `initial_inventory`, `is_active`, `created_at`
  - Index: unique `name` (prevents duplicates)

- `demands`
  - Fields: `plant_id`, `plant_name`, `month` (YYYY-MM), `demand_quantity`, `demand_type`, `created_at`
  - Index: unique (`plant_id`, `month`, `demand_type`)

- `transport_routes`
  - Fields: `from_plant_id`, `from_plant_name`, `to_plant_id`, `to_plant_name`, `transport_mode`, `cost_per_trip`, `capacity_per_trip`, `sbq`, `is_enabled`, `created_at`
  - Index: unique (`from_plant_id`, `to_plant_id`, `transport_mode`)

- `inventory_policies`
  - Fields: `plant_id`, `plant_name`, `safety_stock`, `max_inventory`, `holding_cost_per_month`, `created_at`
  - Index: unique `plant_id` (one policy per plant)

## Running the App (Step-by-Step)

1. Open a terminal.
2. Go into the project folder:

   - `auth-system/`

3. Create a virtual environment:

   - Windows (PowerShell): `python -m venv .venv`

4. Activate it:

   - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`

5. Install dependencies:

   - `pip install -r requirements.txt`

6. Create your `.env` file:

   - Copy `.env.example` to `.env`

7. Run Streamlit:

   - `streamlit run app.py`

8. Open the URL shown in the terminal.

## Testing Phase 2 (Step-by-Step)

### 1) Admin user management

1. Signup an Admin account and login.
2. Open `Dashboard`.
3. Verify summary cards: Total/Active/Inactive users.
4. In `User management`:
   - Select a user
   - Change role to Planner/Viewer
   - Disable the account
5. Try logging in as the disabled user: login should be blocked.

### 2) Plant Management

1. Login as Admin or Planner.
2. Open `Plants`.
3. Add a plant.
4. Edit the plant.
5. Login as Viewer and confirm it is read-only.
6. Login as Admin and delete a plant (admin-only).

### 3) Demand Management

1. Ensure at least 1 plant exists.
2. Login as Admin or Planner.
3. Open `Demands`.
4. Add demand for month like `2026-01`.
5. Try adding the exact same (plant, month, demand_type): it should be rejected as duplicate.
6. Login as Viewer and confirm it is read-only.

### 4) Transport Configuration

1. Ensure at least 2 plants exist.
2. Login as Admin or Planner.
3. Open `Transport`.
4. Create a route.
5. Try SBQ > capacity: it should show an error.
6. Login as Admin:
   - Enable/Disable the route
   - Delete the route (admin-only)

### 5) Inventory Policies

1. Ensure at least 1 plant exists.
2. Login as Admin or Planner.
3. Open `Inventory Policies`.
4. Create a policy.
5. Try creating a second policy for the same plant: it should be rejected.
6. Try max_inventory < safety_stock: it should show an error.
7. Login as Viewer and confirm it is read-only.

---

# Phase 3: Optimization Engine (Pyomo + Gurobi)

Phase 3 adds a deterministic multi-period optimization engine.

## What the optimization does (high level)

It decides, for each month:

- How much to **produce** at each clinker plant
- How much to **ship** between plants
- Which **transport mode** to use
- How many **integer trips** are needed on each route
- What the **inventory level** should be at each plant

And it minimizes total cost:

- Production cost
- Transport cost
- Inventory holding cost

## New Navigation Items

After login you will see:

- `Run Optimization`
- `Optimization Results`

## Roles (Phase 3)

- Admin
  - Can run optimization
  - Can view all results
- Planner
  - Can run optimization
  - Can view all results
- Viewer
  - Cannot run optimization
  - Can view results (read-only)

## Data required for optimization

### 1) Plants

For each **Clinker Plant**, you must set these optional Phase-3 fields:

- `production_capacity` (per month)
- `production_cost` (per unit)

You can set them in `Plants` page (they are optional fields).

### 2) Demands

Optimization currently uses **Fixed** demand only.

### 3) Transport routes

Routes must exist and be enabled, otherwise the model may be infeasible.

### 4) Inventory policy

If an inventory policy does not exist for a plant, the optimizer will default to:

- `safety_stock` from plant
- `max_inventory` = plant storage capacity
- `holding_cost` = 0

## Constraint explanations (real-world meaning)

These constraints are implemented in `backend/optimization/constraints.py`.

1. **Production capacity**
   - You cannot produce more than the monthly plant capacity.

2. **Inventory balance (multi-period)**
   - Inventory this month = last month inventory + production + inbound shipments - outbound shipments - demand.

3. **Safety stock**
   - Inventory must stay above minimum safety stock to prevent stockouts.

4. **Max inventory**
   - Inventory cannot exceed max storage capacity.

5. **Trip capacity**
   - Shipped quantity cannot exceed trips × capacity per trip.

6. **SBQ (minimum shipment batch)**
   - If trips happen, the total shipped must be at least trips × SBQ.

7. **Route enabled**
   - If a route is disabled, shipments and trips are forced to 0.

8. **Mode selection**
   - For a given From→To in a month, you can select at most one mode.
   - Trips are linked to mode selection using a big-M constraint.

## Solver setup

### Gurobi (recommended)

To use Gurobi:

1. Install Gurobi
2. Ensure you have a valid license
3. Ensure `gurobi` is available to Pyomo on your machine

If Gurobi is not available, you can choose **CBC** in the UI.

### CBC (fallback)

CBC must be installed and accessible in your PATH. If it is not installed, Pyomo will report it as not available.

## How to run optimization (step-by-step)

1. Login as Admin or Planner.
2. Open `Plants`:
   - For each Clinker Plant, set `Production capacity per month` and `Production cost per unit`.
3. Ensure `Demands` exist for the months you want.
4. Ensure `Transport` routes exist and are enabled.
5. Open `Run Optimization`.
6. Select months.
7. Choose solver (Gurobi or CBC).
8. Click `Run Optimization`.
9. Open `Optimization Results` to view tables, charts, and export Excel.

## Example output interpretation

- **Production plan**
  - If a clinker plant shows production in a month, it means the optimizer chose to produce there instead of shipping from elsewhere.

- **Transport plan**
  - Trips are integers.
  - Shipment quantity is linked to trips by capacity and SBQ.

- **Inventory levels**
  - If inventory is near safety stock, the plan is lean.
  - If inventory is high, the plan might be producing/shipping early (possibly because transport is cheaper earlier or demand spikes later).

---

# Phase 4: Demand Uncertainty (Scenarios, Stochastic, Robust)

Phase 4 extends the optimization system to handle demand uncertainty.

## Why uncertainty matters (business terms)

In real markets, demand is not perfectly known:

- Orders may be lower than forecast (downside risk)
- Orders may be higher than forecast (stockout risk)

If you optimize with a single deterministic demand number, the plan may look cheap, but it can become infeasible or risky when demand changes.

Phase 4 lets planners explore the **cost vs safety** trade-off:

- **Cheaper** plans often carry less buffer
- **Safer** plans often increase production/shipments or inventory

## Key concepts (beginner-friendly)

### Deterministic (Phase 3)

- Uses a single demand input (your existing `Fixed` demand records)
- Optimizes for that exact demand
- Fast and easy to explain
- Can be risky if actual demand deviates

### Scenario-based uncertainty

We represent uncertainty using a few demand scenarios:

- `Low`
- `Normal`
- `High`

Each scenario has:

- **Probability** (must sum to 1)
- **Demand multiplier** applied to base demand
  - Example: `1.10` means demand is 10% higher than the base

### Stochastic optimization (Expected Cost)

Business meaning:

- We choose one **shared production + transport plan** (commitment)
- Demand can be Low/Normal/High
- Inventory is computed per scenario (same plan, different outcomes)
- Objective minimizes **expected cost** (probability-weighted)

When to use:

- You believe the probabilities are realistic
- You want a balanced plan that performs well on average

### Robust optimization (Worst Case)

Business meaning:

- We choose one **shared production + transport plan**
- The plan must remain feasible in **every** scenario
- Objective focuses on protecting against the **worst-case scenario**

When to use:

- You want maximum safety
- You don’t fully trust scenario probabilities
- Stockouts are extremely expensive and must be avoided

## What is shared vs scenario-specific in the model

- **Shared (here-and-now)** decisions:
  - production by plant-month
  - shipments by route-month
  - trips by route-month
  - mode selection

- **Scenario-specific (recourse)** state:
  - inventory by plant-month-scenario

This structure reflects real operations:
you commit to production/logistics plans, but actual inventory depends on realized demand.

## New UI pages

### 1) Demand Uncertainty Settings

Sidebar: `Demand Uncertainty Settings`

What you can do:

- Enable/disable uncertainty
- Set probabilities for Low/Normal/High
- Set demand multipliers

Validation rules:

- Probabilities must sum to 1
- Multipliers must be non-negative

Role access:

- Admin & Planner: edit + save
- Viewer: view only

### 2) Scenario Comparison

Sidebar: `Scenario Comparison`

What it shows:

- Total cost comparison across runs (deterministic vs stochastic vs robust)
- Inventory buffer comparison (inventory - safety stock)
- A table of recent successful runs with their type and summary metrics

## How to run Phase 4 (step-by-step)

1. Login as Admin or Planner.
2. Go to `Demand Uncertainty Settings`.
3. Enable uncertainty.
4. Confirm probabilities sum to 1.
5. Go to `Run Optimization`.
6. Select months.
7. Choose optimization mode:
   - `Deterministic`
   - `Stochastic (Expected Cost)`
   - `Robust (Worst Case)`
8. Run the model.
9. Open `Optimization Results`:
   - You will see optimization type + scenario definitions
   - Inventory chart supports selecting scenario (for stochastic/robust)
10. Open `Scenario Comparison` to compare run types.

## How to interpret results (cost vs risk)

- **Deterministic**
  - Often lowest cost
  - Buffer may be smaller
  - Can be less safe if demand spikes

- **Stochastic**
  - Cost usually higher than deterministic
  - Buffer is sized for expected outcomes
  - Good balance when probabilities are trusted

- **Robust**
  - Often highest cost
  - Buffer tends to be larger
  - Protects against high-demand scenario

If robust cost is much higher than stochastic:

- It indicates high-demand scenario is hard to cover with existing capacity/transport
- Consider:
  - increasing production capacity
  - adding/enabling routes
  - increasing max inventory
  - adjusting safety stock policy

---

# Phase 5: Advanced Analytics & KPIs (Management Insights)

Phase 5 adds an analytics layer that turns optimization outputs into management-ready KPIs.

Important:

- **No optimization logic is changed.**
- Analytics reads:
  - stored optimization run outputs (`production_rows`, `transport_rows`, `inventory_rows`)
  - master data (plants, routes, inventory policies, demands)
- Analytics writes back to the same run document under `analytics`.

## Why this matters (business terms)

Optimization gives a plan, but management needs answers to questions like:

- What did it cost?
- Which assets are the bottlenecks?
- Are we carrying too much inventory?
- Which plants/routes drive most of the spend?

This phase makes the system feel enterprise-grade by adding explainable, repeatable metrics.

## New UI pages

- `Management Insights Dashboard`
  - KPI cards
  - Cost breakdown
  - Utilization charts
  - Bottleneck flags
  - Cost driver tables

- `Run Comparison`
  - Compare KPIs between two runs (deterministic vs stochastic vs robust)

Role access:

- Admin: full access (can compute/refresh analytics)
- Planner: view only
- Viewer: view only

## KPI glossary (what it means and how to interpret)

### 1) Total cost

Meaning:
- Total optimization objective value (production + transport + holding).

Interpretation:
- Lower is better, but only if service level and risk are acceptable.

### 2) Cost split (Production / Transport / Holding)

Meaning:
- Where money is spent.

Interpretation:
- High transport share can indicate network inefficiency.
- High holding share can indicate excess inventory buffers.

### 3) Cost per ton

Meaning:
- Total cost divided by total demand (tons).

Why management cares:
- Easy benchmark across months and scenarios.

Interpretation:
- Compare across runs to quantify the “cost of safety” (robust vs deterministic).

### 4) Service level (%)

Meaning:
- Percentage of demand fulfilled.

Important note:
- In this system, demand satisfaction is enforced as a hard constraint.
- So a successful solve implies 100% service level.

Interpretation:
- If a run fails, it indicates infeasibility (insufficient capacity/routes/storage).

### 5) Average inventory level

Meaning:
- Average inventory across plants and months.
- For stochastic/robust runs, inventory can be scenario-specific; the dashboard uses a consistent average.

Interpretation:
- Higher average inventory usually means higher safety buffer, but higher holding cost.

### 6) Inventory turnover ratio

Meaning:
- Total demand / average inventory.

Interpretation:
- High turnover: inventory is used efficiently.
- Very low turnover: potential overstock.

### 7) Average inventory buffer

Meaning:
- Average (inventory − safety_stock).

Interpretation:
- Higher buffer reduces risk of stockouts.
- Lower buffer reduces inventory cost but increases risk.

## Utilization analytics

### Production capacity utilization (%)

- Computed as total production / (capacity × number of months).
- High utilization (e.g., >90%) indicates a production bottleneck.

### Transport utilization (%)

- Computed as shipped / (trips × capacity_per_trip) per route-month.
- High utilization indicates limited transport headroom.

### Storage utilization (%)

- Computed as avg inventory / max inventory.
- High utilization indicates storage risk (limited space).

## Bottleneck flags

The dashboard flags bottlenecks when:

- Plants are near max production capacity
- Routes are near full capacity
- Inventory hits safety stock (buffer ~ 0)

These flags help management quickly focus on constraints that limit growth.

## Cost driver analytics

The dashboard reports:

- Top 3 cost-driving plants (production cost)
- Top 3 expensive routes (transport cost)
- Transport cost by mode

## How to use Phase 5 (step-by-step)

1. Run optimization normally (Phase 3 or Phase 4).
2. Open `Management Insights Dashboard`.
3. Select a successful run.
4. If KPIs are missing:
   - Admin clicks `Compute / Refresh analytics for this run`
5. Review:
   - KPI cards
   - Utilization charts
   - Bottleneck flags
   - Cost drivers
6. Open `Run Comparison`.
7. Select Run A and Run B.
8. Review KPI deltas to justify decisions.

---

# Phase 6: Production Readiness (Stability, Safety, Performance)

Phase 6 focuses on making the system stable and safe for real-world use.

Important:

- No new business features are added.
- Optimization logic is unchanged.
- The goal is better reliability, logging, and safer failure behavior.

## What changed (high level)

1. **Caching for performance**
   - Plants and routes are cached using Streamlit cache.
   - This reduces repeated MongoDB reads during Streamlit reruns.

2. **Solver safety + fallback**
   - If Gurobi is requested but unavailable, the system auto-falls back to CBC.
   - Solver runtime is captured.
   - Optional solver logs are written to a log file.

3. **Centralized error handling**
   - Pages are wrapped so users see friendly messages.
   - Full stack traces go only to log files.

4. **Structured logging + audit trails**
   - Logs go to a rotating file in `LOG_DIR`.
   - Audit events can also be stored in MongoDB (`audit_logs`).

5. **Session timeout (security hardening)**
   - Sessions expire after inactivity (default 60 minutes).

6. **Startup health checks**
   - App checks MongoDB connectivity and solver availability at startup.

7. **Backup & restore utilities (basic)**
   - Export collections to JSON and restore from JSON.

## Folder structure additions

New modules:

- `backend/core/`
  - `config_manager.py`
  - `logger.py`
  - `error_handler.py`
  - `cache.py`

- `backend/utils/`
  - `health_check.py`
  - `backup.py`

## Logging (simple explanation)

### File logs

- File: `logs/app.log` (by default)
- Contains:
  - errors with stack traces
  - warnings
  - audit events (as structured JSON strings)

### Audit logs (MongoDB)

Collection: `audit_logs`

Examples of events:

- `login_success`
- `login_failed`
- `logout`
- `optimization_success`
- `optimization_failed`

Why management/admins care:

- traceability (“who did what and when”)
- compliance readiness

## Error handling (what users see vs what admins see)

User-facing:

- Friendly message (no technical stack trace)

Admin-facing:

- Full error details in log file (`logs/app.log`)

This prevents accidental exposure of internal system details.

## Solver fallback behavior

- If you request **Gurobi** but it is not available:
  - the solver automatically switches to **CBC**
  - the UI shows a warning

If neither solver is available:

- Optimization runs will fail gracefully
- Startup checks show a warning

## Backup & recovery (basic)

The module `backend/utils/backup.py` provides two helper functions:

- `export_collections_to_json(output_dir, collections)`
- `restore_collection_from_json(collection_name, json_path, drop_first=False)`

Recommended collections to back up:

- `users`
- `plants`
- `demands`
- `transport_routes`
- `inventory_policies`
- `optimization_results`
- `audit_logs`

## Deployment checklist

### Local run

1. Set environment variables in `.env` (copy `.env.example`).
2. Install Python dependencies:
   - `pip install -r requirements.txt`
3. Ensure MongoDB is running and reachable.
4. Run:
   - `streamlit run app.py`

### Cloud VM run (basic guidance)

1. Install Python and system dependencies on the VM.
2. Install and configure MongoDB OR point to a managed MongoDB.
3. Install a solver:
   - Gurobi (licensed) or CBC
4. Configure `.env` (do not commit secrets).
5. Run Streamlit behind a process manager (example: systemd).
6. Open firewall port for Streamlit (default 8501) or reverse proxy via Nginx.

## Monitoring checklist

- Check `logs/app.log` for errors and warnings.
- Review `audit_logs` collection for suspicious or unexpected activity.
- Watch solver availability warnings.
- Track run history in `optimization_results`.

## Notes

- Passwords are never stored in plain text.
- This project is a foundation. In Phase 2 you can add more modules and pages.
