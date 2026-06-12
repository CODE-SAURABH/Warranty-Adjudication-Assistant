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

export interface ServiceHistoryEntry {
  date: string;
  odometerReading: number;
  repairCode: string;
  description: string;
}

export interface ClaimSubmission {
  vin: string;
  inServiceDate: string;
  currentOdometerReading: number;
  repairCode: string;
  parts: string;
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
