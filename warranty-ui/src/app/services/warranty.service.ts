import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import {
  AdjudicationResponse,
  AssessorOverride,
  BackendAdjudicationUiResponse,
  ClaimQueueItem,
  ClaimResult,
  ClaimSubmission,
} from '../models/claim.model';
import { environment } from '../../environments/environment';

type BackendClaimPayload = {
  vin: string;
  in_service_date: string;
  repair_order_date: string;
  mileage_km: number;
  repair_code: string[];
  causal_part: string[];
  parts_cost_eur: number;
  labor_hours: number;
  failure_description: string;
  attachments: string[];
};

@Injectable({
  providedIn: 'root',
})
export class WarrantyService {
  private readonly baseUrl = environment.apiUrl;
  private claimQueueSubject = new BehaviorSubject<ClaimQueueItem[]>([]);

  claimQueue$ = this.claimQueueSubject.asObservable();

  constructor(private http: HttpClient) {}

  submitClaim(submission: ClaimSubmission): Observable<AdjudicationResponse> {
    return this.http
      .post<BackendAdjudicationUiResponse>(`${this.baseUrl}/adjudicate/ui`, this.toBackendPayload(submission))
      .pipe(
        tap(() => this.getClaimQueue().subscribe()),
        map((response) => this.toAdjudicationResponse(response)),
        catchError(this.handleError),
      );
  }

  getClaimResult(claimId: string): Observable<ClaimResult> {
    return this.http
      .get<ClaimResult>(`${this.baseUrl}/claims/${claimId}`)
      .pipe(catchError(this.handleError));
  }

  getClaimQueue(): Observable<ClaimQueueItem[]> {
    return this.http
      .get<ClaimQueueItem[]>(`${this.baseUrl}/claims`)
      .pipe(
        tap((items) => this.claimQueueSubject.next(items)),
        catchError(this.handleError)
      );
  }

  submitAssessorOverride(override: AssessorOverride): Observable<ClaimResult> {
    return this.http
      .post<ClaimResult>(`${this.baseUrl}/claims/${override.claimId}/override`, override)
      .pipe(
        tap(() => this.getClaimQueue().subscribe()),
        catchError(this.handleError)
      );
  }

  private toBackendPayload(submission: ClaimSubmission): BackendClaimPayload {
    return {
      vin: submission.vin,
      in_service_date: submission.inServiceDate,
      repair_order_date: submission.repairOrderDate,
      mileage_km: submission.currentOdometerReading,
      repair_code: submission.repairCodes,
      causal_part: submission.causalParts,
      parts_cost_eur: submission.partsCostEur,
      labor_hours: submission.laborHours,
      failure_description: submission.failureDescription,
      attachments: [],
    };
  }

  private toAdjudicationResponse(response: BackendAdjudicationUiResponse): AdjudicationResponse {
    const decision = response.disposition_per_claim?.decision;
    return {
      claimId: response.claim_id,
      disposition: decision === 'APPROVE' ? 'APPROVED' : decision === 'REJECT' ? 'REJECTED' : 'PENDING',
      confidenceScore: response.disposition_per_claim?.confidence ?? 0,
      justification: response.assessor_ui?.decision_detail?.summary || 'Decision completed.',
      citedClauses: (response.cited_justification || []).map((citation) => ({
        clauseId: citation.clause_id,
        section: citation.clause_link || 'Policy Clause',
        text: citation.clause_quote || citation.justification || 'No clause quote provided.',
      })),
      missingInfo: (response.missing_information || []).map((item) => ({
        field: item.item,
        description: item.message,
        clauseReference: item.required_clause_id,
      })),
    };
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let message = 'An unexpected error occurred. Please try again.';
    if (error.status === 422) {
      message = 'Validation error: Please check all required fields.';
    } else if (error.status === 404) {
      message = 'Claim not found.';
    } else if (error.status === 0) {
      message = 'Cannot reach the server. Please ensure the API is running.';
    } else if (typeof error.error?.detail === 'string') {
      message = error.error.detail;
    }
    return throwError(() => new Error(message));
  }
}
