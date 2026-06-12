import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import {
  ClaimSubmission,
  AdjudicationResponse,
  ClaimResult,
  ClaimQueueItem,
  AssessorOverride,
  ClaimDisposition,
} from '../models/claim.model';
import { environment } from '../../environments/environment';

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
      .post<AdjudicationResponse>(`${this.baseUrl}/claims/adjudicate`, submission)
      .pipe(
        tap((response) => this.addToQueue(response, submission)),
        catchError(this.handleError)
      );
  }

  getClaimResult(claimId: string): Observable<ClaimResult> {
    return this.http
      .get<ClaimResult>(`${this.baseUrl}/claims/${claimId}`)
      .pipe(catchError(this.handleError));
  }

  getClaimQueue(): Observable<ClaimQueueItem[]> {
    return this.http.get<ClaimQueueItem[]>(`${this.baseUrl}/claims`).pipe(
      tap((items) => this.claimQueueSubject.next(items)),
      catchError(this.handleError)
    );
  }

  submitAssessorOverride(override: AssessorOverride): Observable<ClaimResult> {
    return this.http
      .post<ClaimResult>(`${this.baseUrl}/claims/${override.claimId}/override`, override)
      .pipe(
        tap(() => this.refreshQueueItem(override.claimId, override.overrideDisposition)),
        catchError(this.handleError)
      );
  }

  private addToQueue(response: AdjudicationResponse, submission: ClaimSubmission): void {
    const existing = this.claimQueueSubject.getValue();
    const queueItem: ClaimQueueItem = {
      claimId: response.claimId,
      vin: submission.vin,
      disposition: response.disposition,
      confidenceScore: response.confidenceScore,
      repairCode: submission.repairCode,
      timestamp: new Date().toISOString(),
    };
    this.claimQueueSubject.next([queueItem, ...existing]);
  }

  private refreshQueueItem(claimId: string, newDisposition: ClaimDisposition): void {
    const queue = this.claimQueueSubject.getValue().map((item) =>
      item.claimId === claimId
        ? { ...item, disposition: newDisposition, assessorOverridden: true }
        : item
    );
    this.claimQueueSubject.next(queue);
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let message = 'An unexpected error occurred. Please try again.';
    if (error.status === 422) {
      message = 'Validation error: Please check all required fields.';
    } else if (error.status === 404) {
      message = 'Claim not found.';
    } else if (error.status === 0) {
      message = 'Cannot reach the server. Please ensure the API is running.';
    } else if (error.error?.detail) {
      message = error.error.detail;
    }
    return throwError(() => new Error(message));
  }
}
