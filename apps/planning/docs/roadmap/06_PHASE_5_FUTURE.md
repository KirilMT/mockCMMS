# Phase 5 – Future Enhancements

These items are intentionally out of scope for the initial Planning integration but should be considered in future sprints.

- [ ] 7.1. Manpower status API (JSON-backed)
  - [ ] 7.1.1. Implement a service (initially using JSON) that exposes technician status: onsite, off, sick, vacation.
  - [ ] 7.1.2. Integrate this service into the planning engine so unavailable technicians are automatically excluded.
  - [ ] 7.1.3. **Testing:** Write integration tests to verify that the planning engine correctly excludes unavailable technicians based on the API's output.

- [ ] 7.2. Advanced REP task assignment
  - [ ] 7.2.1. Design a text-analysis-based approach for REP MOs (title/description based classification and prioritization).
  - [ ] 7.2.2. Reuse or adapt logic from `CMMS-SCADA-Excel-DataProcessor` to inform REP planning.
  - [ ] 7.2.3. Integrate REP auto-assignment into the main planning engine and UI.
  - [ ] 7.2.4. **Testing:** Develop unit tests for the text analysis logic and E2E tests to validate that REP tasks are correctly prioritized and assigned.

- [ ] 7.3. Automatic spare parts ordering
  - [ ] 7.3.1. Define a rule set for when to automatically generate spare parts orders ahead of planned tasks (e.g., previous shift).
  - [ ] 7.3.2. Implement a background job or service that checks upcoming tasks and triggers orders based on inventory and lead time.
  - [ ] 7.3.3. Integrate these orders with the core CMMS spares management module.
  - [ ] 7.3.4. **Testing:** Create tests for the background job to ensure orders are triggered correctly based on various inventory and timing scenarios.

- [ ] 7.4. Planning simulations and optimization
  - [ ] 7.4.1. Add a "simulation" mode that allows planners to test different scenarios without committing changes.
  - [ ] 7.4.2. Explore algorithmic or heuristic optimization (e.g., load balancing, minimizing technician travel, respecting preferences).
  - [ ] 7.4.3. **Testing:** Test the simulation mode to ensure it accurately reflects planning outcomes without altering the live plan. Validate that optimization algorithms produce measurably better results against a baseline.

- [ ] 7.5. **On-the-Go Emergency Planning** 🆕 **USER REQUEST - November 20, 2025**
  - **Use Case:** Quick planning for unexpected breakdowns or opportunities
  - **Scenario:** "There is a breakdown somewhere else and it allows us to do maintenance"
  - **Requirements:**
    - [ ] 7.5.1. **Quick Planning UI:**
      - Fast task creation (minimal required fields)
      - Duration selector (slider or quick buttons: 15min, 30min, 1hr, 2hr, custom)
      - Priority selector (urgent by default)
      - Skill requirements (dropdown, multi-select)
      - Immediate execution option
    - [ ] 7.5.2. **Planning Mode:**
      - Similar to shift-break mode but more flexible
      - User-defined duration window
      - Can interrupt/adjust existing plans
      - Real-time technician availability check
    - [ ] 7.5.3. **Integration:**
      - Accessible from main dashboard (quick action button)
      - Mobile-friendly UI (likely used in field)
      - Push notifications to assigned technicians
      - Can convert to regular MO after completion
    - [ ] 7.5.4. **Planning Engine Support:**
      - Prioritize emergency tasks over regular planning
      - Check current technician locations (if available)
      - Suggest nearest available technicians
      - Handle concurrent planning conflicts
    - [ ] 7.5.5. **Workflow:**
      1. User clicks "Emergency Planning" button
      2. Quick form: Task description, duration, skills needed
      3. System shows available technicians NOW
      4. User selects technicians or auto-assign
      5. Task immediately added to Gantt chart
      6. Notifications sent
      7. Can be tracked separately from regular planning
    - [ ] 7.5.6. **Features:**
      - Override regular planning (bump lower priority tasks)
      - Show impact on existing plans (which tasks delayed)
      - Undo/adjust option
      - History of emergency tasks
      - Analytics (how many emergencies per week/month)
  - **Priority:** 🟡 Medium - Real-world operational need
  - **Complexity:** MEDIUM - UI + planning logic + notifications
  - **Estimated Time:** 2 weeks
  - **Benefits:**
    - Faster response to breakdowns
    - Opportunistic maintenance
    - Better resource utilization
    - Real-time visibility
