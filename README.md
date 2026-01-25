## README.md

# Mintlayer Node Health Monitoring - Phase 1

## Overview
This repository contains all documentation and reference material for the Phase 1 implementation of a Mintlayer Node Health Monitoring Dashboard. Phase 1 focuses on real-time monitoring and critical metrics without historical data.

## Features
- Node identity & metadata
- Node version & fork compatibility
- Sync status & block lag
- Peer count & connectivity
- Online/offline status
- Pool activity & delegations
- Alert system for critical and warning states
- Delegator-facing health badges

## Usage
- Review the Markdown files in `docs/` for design and schema guidance
- Use `api/endpoints.md` for Phase-1 API structure
- Examples are provided in `examples/`
- All files can be committed to a private GitHub repository for version control and collaboration

## Next Steps
- Implement Phase-1 pollers according to the design
- Build the dashboard UI based on `Dashboard_Design.md`
- Integrate alert logic and display badges
- Prepare for Phase-2 extensions such as historical data and visualizations

