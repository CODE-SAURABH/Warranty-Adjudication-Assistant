import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormControl, Validators } from '@angular/forms';
import { WarrantyService } from '../../services/warranty.service';
import { ClaimResult, AssessorOverride, ClaimDisposition } from '../../models/claim.model';

@Component({
  selector: 'app-claim-detail',
  templateUrl: './claim-detail.component.html',
  styleUrls: ['./claim-detail.component.css'],
})
export class ClaimDetailComponent implements OnInit {
  claim: ClaimResult | null = null;
  isLoading = true;
  loadError = '';
  showOverridePanel = false;
  overrideDisposition: ClaimDisposition = 'APPROVED';
  overrideRationale = new FormControl('', [Validators.required, Validators.minLength(10)]);
  isSubmittingOverride = false;
  overrideError = '';
  overrideSuccess = false;

  readonly dispositionOptions: { value: ClaimDisposition; label: string }[] = [
    { value: 'APPROVED', label: 'Approve' },
    { value: 'REJECTED', label: 'Reject' },
    { value: 'PENDING', label: 'Refer to Human' },
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private warrantyService: WarrantyService
  ) {}

  ngOnInit(): void {
    const claimId = this.route.snapshot.paramMap.get('id');
    if (!claimId) {
      this.router.navigate(['/dashboard']);
      return;
    }
    this.warrantyService.getClaimResult(claimId).subscribe({
      next: (result) => {
        this.claim = result;
        this.isLoading = false;
      },
      error: (err: Error) => {
        this.loadError = err.message;
        this.isLoading = false;
      },
    });
  }

  getConfidenceLabel(score: number): string {
    if (score >= 0.85) return 'High';
    if (score >= 0.6) return 'Medium';
    return 'Low';
  }

  getConfidenceClass(score: number): string {
    if (score >= 0.85) return 'confidence-high';
    if (score >= 0.6) return 'confidence-medium';
    return 'confidence-low';
  }

  submitOverride(): void {
    if (!this.claim || this.overrideRationale.invalid) {
      this.overrideRationale.markAsTouched();
      return;
    }
    this.isSubmittingOverride = true;
    this.overrideError = '';

    const override: AssessorOverride = {
      claimId: this.claim.claimId,
      originalDisposition: this.claim.disposition,
      overrideDisposition: this.overrideDisposition,
      assessorRationale: this.overrideRationale.value!,
      assessorId: 'ASSESSOR-001',
      timestamp: new Date().toISOString(),
    };

    this.warrantyService.submitAssessorOverride(override).subscribe({
      next: (updated) => {
        this.claim = updated;
        this.showOverridePanel = false;
        this.overrideSuccess = true;
        this.isSubmittingOverride = false;
        this.overrideRationale.reset();
      },
      error: (err: Error) => {
        this.overrideError = err.message;
        this.isSubmittingOverride = false;
      },
    });
  }
}
