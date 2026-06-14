export type ClaimDisposition = 'APPROVED' | 'REJECTED' | 'PENDING';

export type VehicleType = 'car' | 'bike' | 'truck';
export type VehicleView = 'front' | 'left' | 'rear' | 'right' | 'top';

export interface VehicleZone {
  id: string;
  label: string;
  repairCode: string;
  description: string;
  svgPath: string;
  view: VehicleView;
}

export interface SelectedZone {
  zoneId: string;
  label: string;
  repairCode: string;
  defaultDescription: string;
}

/** Emitted by VehicleZoneSelectorComponent when an issue is added or removed */
export interface ZoneIssueEvent {
  zoneId: string;
  zoneLabel: string;
  repairCode: string;
  issueLabel: string;
}

export interface ServiceHistoryEntry {
  date: string;
  odometerReading: number;
  repairCode: string;
  description: string;
}

export interface ClaimSubmission {
  vin: string;
  inServiceDate: string;
  repairOrderDate: string;
  currentOdometerReading: number;
  repairCodes: string[];
  causalParts: string[];
  partsCostEur: number;
  laborHours: number;
  failureDescription: string;
  serviceHistory?: ServiceHistoryEntry[];
}

export interface PolicyClause {
  clauseId: string;
  section: string;
  text: string;
  relevanceScore?: number;
}

export interface MissingInfo {
  field: string;
  description: string;
  clauseReference?: string;
}

export interface ClaimResult {
  claimId: string;
  disposition: ClaimDisposition;
  confidenceScore: number;
  justification: string;
  citedClauses: PolicyClause[];
  missingInfo?: MissingInfo[];
  assessorNotes?: string;
  timestamp: string;
  submission: ClaimSubmission;
}

export interface ClaimQueueItem {
  claimId: string;
  vin: string;
  disposition: ClaimDisposition;
  confidenceScore: number;
  repairCode: string;
  timestamp: string;
  assessorOverridden?: boolean;
}

export interface AssessorOverride {
  claimId: string;
  originalDisposition: ClaimDisposition;
  overrideDisposition: ClaimDisposition;
  assessorRationale: string;
  assessorId: string;
  timestamp: string;
}

export interface AdjudicationResponse {
  claimId: string;
  disposition: ClaimDisposition;
  confidenceScore: number;
  justification: string;
  citedClauses: PolicyClause[];
  missingInfo?: MissingInfo[];
  processingTimeMs?: number;
}

export type BackendDecision = 'APPROVE' | 'REJECT' | 'REFER_TO_HUMAN';

export interface BackendCitation {
  clause_id: string;
  clause_quote?: string;
  clause_link?: string;
  justification?: string;
}

export interface BackendMissingInformation {
  item: string;
  message: string;
  required_clause_id?: string;
  required_clause_quote?: string;
  required_clause_link?: string;
}

export interface BackendAdjudicationUiResponse {
  claim_id: string;
  disposition_per_claim: {
    decision: BackendDecision;
    confidence: number;
  };
  cited_justification: BackendCitation[];
  missing_information: BackendMissingInformation[];
  assessor_ui: {
    claim_queue: {
      claim_id: string;
      recommended_action: BackendDecision;
      priority: 'NORMAL' | 'HIGH';
    };
    decision_detail: {
      summary: string;
      rule_summary: string;
      flags: string[];
      citations: Array<{
        clause_id: string;
        clause_link?: string;
      }>;
    };
    override_capability: {
      allowed: boolean;
      required_fields: string[];
    };
  };
}
