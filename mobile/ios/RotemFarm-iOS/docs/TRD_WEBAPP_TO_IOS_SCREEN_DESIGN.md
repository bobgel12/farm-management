# Technical Requirements Document (TRD)

## Project

Web App Feature Parity -> iOS Screen Design Expansion

## Purpose

This document defines the iOS screen requirements needed to represent all major features already available in the web app. It is written to be used as context input for Claude AI to design additional iOS screens and flows.

## Context

- Existing web app has broad feature coverage across farms, houses, monitoring, tasks, workers, organizations, flocks, analytics, reporting, rotem, and account/security.
- Current iOS app already implements a core subset (home, houses, alerts, reports, profile, and several detail flows).
- Goal: design missing iOS screens so product coverage aligns with web app capabilities.

## Source of truth

- Web routes and feature entry points: `frontend/src/App.tsx`
- Existing iOS implementation overview: `mobile/ios/RotemFarm-iOS/README.md`

## Product objective

Design a complete and coherent iOS information architecture and screen set that:

- Covers all existing web features.
- Respects iOS patterns (tab + stack navigation, sheets for create/edit, pull-to-refresh, inline validation).
- Preserves farm operations workflows for field users and managers.

## User roles (functional)

- Farm Manager: manages farms/houses, workers, programs, reporting, organization settings.
- Operator/Worker: views assigned tasks, house conditions, alerts, and updates execution status.
- Org Admin/Owner: manages organizations, members, invites, security-sensitive settings.

## Feature inventory from web app

### Authentication & Access

- Login
- Forgot password
- Reset password
- Accept organization invite

### Dashboard & Navigation

- Main dashboard
- Global protected app shell

### Farms & Houses

- Farms list
- Farm dashboard
- House detail page
- House-specific detail path variants

### Monitoring

- Farm houses monitoring
- House monitoring dashboard
- House comparison dashboard (cross-house metrics)

### Tasks & Programs

- House task list
- Global task management
- Program management

### Workforce

- Workers list (global and farm scoped)

### Communication & Security

- Email manager
- Security settings

### Flocks

- Flock list
- Create/edit flock
- Flock detail
- Add performance record

### Organizations

- Organization list
- Organization create/edit
- Organization settings

### Analytics & Reporting

- BI dashboard
- Reports list

### Rotem

- Rotem dashboard
- Rotem farm detail

## Current iOS coverage snapshot

Already present in iOS (per current README):

- Auth gateway (Sign in with Apple stub)
- Dashboard/Home
- Houses list/detail/history
- Alerts inbox + alert detail
- Reports tab (high-level KPI/trend)
- Flocks sub-flow (list + growth curve)
- Profile/settings basics (team + pair controller)

Partially covered:

- Monitoring and resource detail views exist but not mapped 1:1 to all web monitoring surfaces.

Missing or needs expansion:

- Organizations management flows
- Worker management suite
- Program management suite
- Task management parity (especially per-house operations + assignment UX)
- BI analytics screens
- Email management
- Security settings parity
- Full Rotem management depth
- Invite acceptance / password reset UX parity (if iOS supports full auth recovery)

## iOS design principles for parity

- Keep 5-tab base navigation, add deeper feature areas through nested stacks and contextual entry points.
- Prefer action sheets/full-screen sheets for create/edit flows.
- Preserve web intent, not web layout: optimize for thumb-first mobile interaction.
- Every list screen must support loading, empty, error, and pull-to-refresh states.
- Every create/edit form must support validation states and destructive action confirmation.

## Required iOS screen modules (design scope)

### 1) Auth & Access module

- Login (credential + Apple sign-in variants if applicable)
- Forgot password request
- Reset password
- Accept invite (token-based deep link entry)

### 2) Farm Operations module

- Farms list
- Farm dashboard overview
- Farm houses monitoring
- House comparison dashboard
- House detail root with section tabs:
  - Overview
  - Monitoring
  - Tasks
  - Flock
  - Mortality
  - Issues/alerts
  - Devices/messages (if enabled by backend capability)

### 3) Tasks & Programs module

- Task inbox (global)
- House-scoped task list
- Task detail (status update, assignee, due time, notes)
- Program manager list
- Program create/edit flow
- Program-to-house assignment screen

### 4) Workforce module

- Worker list
- Worker detail
- Create/edit worker
- Assign workers to farms/houses

### 5) Flocks module (expansion)

- Existing list/detail/edit retained
- Performance record create/edit history
- Cross-flock comparison mini-dashboard

### 6) Organizations module

- Organization list/switcher
- Create organization
- Edit organization
- Member list
- Invite member
- Edit member role
- Organization settings

### 7) Analytics & Reports module

- BI dashboard (filters: farm, house, date range)
- KPI cards + trend charts + benchmark comparisons
- Reports list
- Report detail with export/share actions

### 8) Rotem module (advanced monitoring)

- Rotem dashboard (multi-farm health summary)
- Rotem farm detail
- Sensor trends (realtime + historical)
- Controller/device status panels
- AI/ML insight cards (if backend provides)

### 9) Admin utilities module

- Email manager (templates/status/send test)
- Security settings (password change, session/device list, critical action confirmations)

## Navigation architecture requirement

- Primary tabs (recommended):
  - Home
  - Operations (farms/houses/tasks)
  - Alerts
  - Analytics
  - Profile
- Secondary navigation:
  - Organizations, workers, programs, and admin settings accessible from Profile and contextual shortcuts.
- Global elements:
  - Organization switcher in top-level context.
  - Farm selector chip/filter on operations and analytics surfaces.
  - Universal alert badge.

## Standard screen contract (for all new screens)

Each designed screen must include:

- Objective (what user accomplishes)
- Inputs (filters, form fields, selectors)
- Data dependencies (API entities/endpoints)
- UI states: loading/empty/error/offline/success
- Primary and secondary actions
- Navigation entry and exit paths
- Permission constraints by role

## Data contract expectations for design

Claude should design components assuming typed models for:

- Farm, House, Worker, Task, Program, Flock, Organization, Member, Report, Alert, SensorSeries, DeviceStatus.

For each screen, include:

- Required fields
- Optional fields
- Sort/filter dimensions
- Pagination behavior for large datasets

## Non-functional UX requirements

- iOS 17+ SwiftUI-first patterns
- Accessibility:
  - Dynamic type support
  - VoiceOver labels for cards/charts/actions
  - Minimum tap target sizing
- Performance:
  - Initial list render under 1.5s on average data size (design target)
  - Skeletons for data-heavy dashboards
- Offline-aware:
  - Visible stale/offline indicators
  - Retry actions

## Deliverables expected from Claude AI

Claude output should provide:

- Complete screen inventory by module
- Information architecture (tab + stack map)
- User flow diagrams (happy path + critical edge cases)
- Low-to-mid fidelity UI specs per screen
- Component reuse map (cards, tables, charts, forms)
- State matrix (loading/empty/error/offline/permission denied)
- Prioritized implementation roadmap (P0/P1/P2)

## Priority rollout guidance

- P0 (must-have parity):
  - Farms, houses, house monitoring, tasks, workers, organizations, security basics
- P1:
  - Programs, BI dashboard, expanded reporting, rotem deep-dive
- P2:
  - Advanced admin/email tooling and optimization features

## Acceptance criteria for parity design

- Every major web route capability has an iOS destination screen or justified omission.
- All CRUD-heavy modules include create/edit/detail/list designs.
- Role-sensitive actions are explicitly modeled in screen behavior.
- Monitoring and analytics have filterable, drill-down-friendly mobile layouts.
- Final design package is implementation-ready for SwiftUI engineering.

## Prompt package for Claude AI (copy/paste)

Use the following instruction block with Claude:

You are designing iOS screens (SwiftUI, iOS 17+) for a farm management app. The web app already supports these modules: auth, farms, houses, monitoring, tasks, programs, workers, organizations, flocks, analytics, reports, rotem monitoring, email manager, and security settings.

Goal: produce an implementation-ready iOS UX design specification that covers all existing web features and closes parity gaps with current iOS coverage.

Requirements:

1. Output a full screen inventory grouped by module.
2. Provide a navigation architecture (tabs, stacks, deep links).
3. For each screen: objective, fields/filters, components, actions, states (loading/empty/error/offline), and role permissions.
4. Include create/edit/detail/list flows for all CRUD entities.
5. Include monitoring and analytics drill-down flows (farm -> house -> metric detail).
6. Include organization/member/invite and security/account management flows.
7. Include tasks/program workflows with assignment and status updates.
8. Identify reusable SwiftUI components and design tokens.
9. Provide a phased roadmap (P0/P1/P2) and handoff notes for engineers.

Constraints:

- Respect mobile-first iOS interaction patterns.
- Optimize for field operations (quick actions, at-a-glance status, low-friction updates).
- Avoid desktop-style dense tables unless absolutely necessary.
- Keep consistency with existing tabs: Home, Houses/Operations, Alerts, Reports/Analytics, Profile.

Output format:

- Section 1: Information architecture
- Section 2: Screen catalog (module by module)
- Section 3: User flows
- Section 4: State matrix
- Section 5: Reusable components
- Section 6: Delivery roadmap