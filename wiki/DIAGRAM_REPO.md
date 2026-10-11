# APEX_KINETIX Diagram Repository (Diagram-Design Standard)

This repository catalogs the formal architectural state machines and component graphs for **APEX_KINETIX**.
Governed by Apex Growth Systems LLC.

---

## 1. State Machine: Action Execution & Compensating Rollback Lifecycle

```mermaid
stateDiagram-v2
    [*] --> RESTING_STATE: Agent Idle / Cursor Parked

    RESTING_STATE --> TARGET_INGRESS: Target Request Received
    
    state TARGET_INGRESS {
        [*] --> ComputeFittsDuration
        ComputeFittsDuration --> QueryMAPElitesArchive
        QueryMAPElitesArchive --> ApplySessionDrift
        ApplySessionDrift --> ParameterGenomeReady
    }

    ParameterGenomeReady --> NEUROMOTOR_SYNTHESIS: Genome Selected

    state NEUROMOTOR_SYNTHESIS {
        [*] --> SynthesizeSigmaLognormal
        SynthesizeSigmaLognormal --> InjectSignalDependentNoise
        InjectSignalDependentNoise --> InjectPhysiologicalTremor
        InjectPhysiologicalTremor --> InjectVossMcCartneyPinkNoise
        InjectVossMcCartneyPinkNoise --> TrajectoryPointsCompiled
    }

    TrajectoryPointsCompiled --> TRANSACTION_SETUP: Points Buffer Ready

    state TRANSACTION_SETUP {
        [*] --> AssertPreConditions
        AssertPreConditions --> RecordTransactionInJournal
        RecordTransactionInJournal --> HardwareDispatchReady
    }

    HardwareDispatchReady --> OUTSIDE_IN_DISPATCH: 125 Hz Hardware Loop

    state OUTSIDE_IN_DISPATCH {
        [*] --> StreamMouseMoveEvents
        StreamMouseMoveEvents --> SampleClickDwellLatency
        SampleClickDwellLatency --> InjectHardwareMouseDown
        InjectHardwareMouseDown --> InjectHardwareMouseUp
    }

    OUTSIDE_IN_DISPATCH --> POST_ACTION_VALIDATION: Events Injected

    state POST_ACTION_VALIDATION {
        [*] --> VerifyTargetBoundsContainment
        VerifyTargetBoundsContainment --> CommitTransaction: Inside Bounds
        VerifyTargetBoundsContainment --> TriggerCompensatingRollback: Outside Bounds
    }

    CommitTransaction --> UPDATE_MAP_ELITES: Extract Phenotype
    UPDATE_MAP_ELITES --> RESTING_STATE: Success Verified

    TriggerCompensatingRollback --> EXECUTE_ROLLBACK: Pop LIFO Stack
    EXECUTE_ROLLBACK --> RESTING_STATE: State Restored
```

---

## 2. MAP-Elites Quality-Diversity Architecture Flow

```mermaid
flowchart TD
    subgraph PHENOTYPIC_INPUT["1. Trajectory Behavioral Features"]
        POINTS["Executed Trajectory Points"]
        VEL["b1: Mean Velocity (150 - 2400 px/s)"]
        CURV["b2: Curvature Entropy (0.2 - 3.2)"]
        SUB["b3: Submovement Jitter Ratio (0.0 - 0.5)"]
        FITTS_DEV["b4: Fitts ID Deviation (0.0 - 0.3)"]
        POINTS --> VEL
        POINTS --> CURV
        POINTS --> SUB
        POINTS --> FITTS_DEV
    end

    subgraph ARCHIVE_MAPPING["2. 4D Grid Indexing (O(1))"]
        HASH["Continuous-to-Discrete Bin Function"]
        CELL["Target Cell: (bin1, bin2, bin3, bin4)"]
        VEL --> HASH
        CURV --> HASH
        SUB --> HASH
        FITTS_DEV --> HASH
        HASH --> CELL
    end

    subgraph QUALITY_EVALUATION["3. Elite Competition & Illumination"]
        FITNESS["Fitness Score F(theta) = exp(-W1 - D_KS)"]
        COMPARE{"Is Cell Occupied?"}
        REPLACE{"New Fitness > Current Elite?"}
        STORE["Store New Elite in Cell"]
        DISCARD["Discard Candidate"]
        
        CELL --> COMPARE
        COMPARE -->|No: Empty Cell| STORE
        COMPARE -->|Yes: Occupied| REPLACE
        FITNESS --> REPLACE
        REPLACE -->|Yes| STORE
        REPLACE -->|No| DISCARD
    end
```

---

## 3. Neuromotor Signal Superposition Pipeline

```mermaid
flowchart LR
    A["Target & Distance"] --> B["Fitts MT Solver"]
    B --> C["Primary Stroke (82%)"]
    B --> D["Secondary Stroke (18%)"]
    C --> E["Sigma-Lognormal Sum"]
    D --> E
    E --> F["Signal-Dependent Noise"]
    F --> G["8-12 Hz Tremor"]
    G --> H["1/f Pink Noise"]
    H --> I["Final Natural Trajectory"]
```

---

## 4. Comprehensive E2E Verification & Adversarial Classifier Architecture

```mermaid
flowchart TD
    subgraph E2E_WORKFLOW["1. Multi-Step Workflow Invariants"]
        FORM["Multi-Step Form Ingress"]
        DRAG["Drag-and-Drop Trajectory"]
        FORM -->|3 Discrete Fields| DWELL["Log-Normal Dwell & Flight Invariant"]
        DRAG -->|Continuous Hold| MOMENTUM["Loaded Momentum & Continuous Sampling"]
    end

    subgraph ADVERSARIAL_BOUNDS["2. Boundary & Stress Verification"]
        TINY["2px Micro-Target (ID > 9 bits)"]
        CORNERS["Extreme Corners: (0,0) & (3840,2160)"]
        ENDURANCE["250-Action Session Endurance"]
        TINY --> BOUND_ASSERT["Finite Coordinate & Containment Invariant"]
        CORNERS --> BOUND_ASSERT
        ENDURANCE --> DRIFT_ASSERT["Ornstein-Uhlenbeck Drift & Bounded Memory"]
    end

    subgraph SAFETY_ROLLBACK["3. Transactional Safety & Saga Recovery"]
        CASCADE["Depth-10 Cascading Fault Injection"]
        LIFO_STACK["Transactional Rollback Journal"]
        CASCADE --> LIFO_STACK
        LIFO_STACK -->|Strict Reverse Order| REVERSAL["Compensating Inverse Reversal Verified"]
    end

    subgraph ADVERSARIAL_CLASSIFIER["4. Enterprise Anti-Bot Classifier Suite"]
        PROBES["Cloudflare / DataDome Simulation Probes"]
        SPEED_CHECK["Constant Velocity Probe (StdDev > 5 px/s)"]
        JERK_CHECK["Zero-Jerk Bezier Spline Probe (StdDev > 1 px/s^3)"]
        BOUNDARY_CHECK["Teleportation / Abrupt Start-End Probe"]
        PROBES --> SPEED_CHECK
        PROBES --> JERK_CHECK
        PROBES --> BOUNDARY_CHECK
        SPEED_CHECK --> CLASSIFIER_PASS["100% Evasion Rate (0 Flags Across 50 Trials)"]
        JERK_CHECK --> CLASSIFIER_PASS
        BOUNDARY_CHECK --> CLASSIFIER_PASS
    end
```

