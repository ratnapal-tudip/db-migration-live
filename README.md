   # DB Migration Live - Migration & Deployment Guide

   This project contains a FastAPI service backed by MySQL, load-balanced by Nginx, designed to support zero-downtime Blue-Green deployments and Canary releases.

   ---

   ## 1. Prerequisites
   Ensure you have the following installed locally:
   * **Docker** & **Docker Compose**
   * **Flyway CLI** (for running migrations manually from your host machine - [Flyway CLI Installation Guide](https://www.red-gate.com/hub/product-learning/flyway/installing-and-upgrading-the-flyway-cli/))

   ---

   ## 2. Getting Started & Configuration

   After cloning the repository, configure your local environment files (these files are ignored by Git):

   1. **Configure Environment Variables**:
      Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```

   2. **Configure Flyway Credentials**:
      Copy `flyway.conf.example` to `flyway.conf`:
      ```bash
      cp flyway.conf.example flyway.conf
      ```

   ---

   ## 3. Database Migration

   Run migrations manually on your host machine before starting the application:

   1. **Start the Database Container**:
      Ensure MySQL is running first:
      ```bash
      docker compose up -d mysql
      ```
   2. **Apply Migrations**:
      Run the Flyway CLI:
      ```bash
      flyway migrate
      ```
      *This reads `flyway.conf` to connect to the database locally on port `3306` and runs scripts inside `./migrations`.*

   3. **Verify the Database and Migrations**:
      Log into the running MySQL container and check that the migrations applied:
      ```bash
      docker compose exec -it mysql mysql -u appuser -papppassword userservice
      ```
      Once inside the MySQL prompt, run the following SQL command to see the applied migration tables:
      ```sql
      SHOW TABLES;
      ```

   ---

   ## 4. Blue-Green Deployment Workflow (v1 from main $\rightarrow$ v2 from develop)

   This project has a **Blue** container (`app-blue`) and a **Green** container (`app-green`). Nginx acts as the front door and routes traffic based on `/nginx/conf.d/default.conf`.

   ---

   ### Step A: Deploy v1 (Initial Release from `main` branch)

   1. **Switch to the `main` branch**:
      ```bash
      git switch main
      ```
   2. **Set the Blue version tag**:
      Open `.env` and set:
      ```env
      APP_VERSION_BLUE=1.0.0
      ```
   3. **Build and start the Blue application**:
      ```bash
      docker compose up -d app-blue --build
      ```
      *This compiles the v1 code and tags the image as `db-migration-live-app:1.0.0`.*
   4. **Route Nginx traffic to Blue**:
      Open `nginx/conf.d/default.conf` and ensure the `upstream` block points to `app-blue`:
      ```nginx
      upstream app_servers {
          server app-blue:8000;
          # server app-green:8000;
      }
      ```
   5. **Start Nginx**:
      ```bash
      docker compose up -d nginx
      ```
   6. **Reload Nginx Configuration**:
      ```bash
      docker compose exec nginx nginx -s reload
      ```
   7. **Test public endpoint**:
      ```bash
      curl http://localhost/users
      ```
      *This request goes through Nginx to the `app-blue` container running `1.0.0`.*

   ---

   ### Step B: Deploy v2 (Zero-Downtime Upgrade from `develop` branch)

   While `app-blue` is serving live production traffic:

   1. **Switch to the `develop` branch**:
      ```bash
      git switch develop
      ```
   2. **Set the Green version tag**:
      Open `.env` and set:
      ```env
      APP_VERSION_GREEN=2.0.0
      ```
   3. **Run Database Migrations**:
      Run the Flyway CLI to apply database migrations for the v2 schema changes:
      ```bash
      flyway migrate
      ```
      *Since you switched to the `develop` branch, Flyway will read and apply the new migration files from `./migrations`.*
   4. **Build and start the Green application**:
      *This will build version 2.0.0 without impacting the running Blue container.*
      ```bash
      docker compose up -d app-green --build
      ```
      *This compiles the new code and tags the local image as `db-migration-live-app:2.0.0`.*
   5. **Swap Nginx traffic to Green**:
      Open `nginx/conf.d/default.conf` and update the `upstream` block:
      ```nginx
      upstream app_servers {
          # server app-blue:8000;
          server app-green:8000;
      }
      ```
   6. **Perform Zero-Downtime Reload**:
      ```bash
      docker compose exec nginx nginx -s reload
      ```
   7. **Test the v2 public endpoint**:
      ```bash
      curl http://localhost/users
      ```
      *Traffic is now immediately routed to `app-green` running `2.0.0`.*
   Nginx reloads its configuration gracefully. Existing active requests on the old container will finish safely, and all new traffic is routed to the new Green v2 container instantly.

   ---
