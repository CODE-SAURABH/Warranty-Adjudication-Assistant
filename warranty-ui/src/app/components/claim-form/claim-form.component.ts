import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { WarrantyService } from '../../services/warranty.service';
import { ClaimSubmission, SelectedZone } from '../../models/claim.model';

@Component({
  selector: 'app-claim-form',
  templateUrl: './claim-form.component.html',
  styleUrls: ['./claim-form.component.css'],
})
export class ClaimFormComponent implements OnInit {
  claimForm!: FormGroup;
  isSubmitting = false;
  submitError = '';

  readonly repairCodes = [
    { code: 'ENG-001', label: 'Engine – Oil Leak' },
    { code: 'ENG-002', label: 'Engine – Overheating' },
    { code: 'ENG-003', label: 'Engine – Misfiring' },
    { code: 'TRANS-001', label: 'Transmission – Slipping' },
    { code: 'TRANS-002', label: 'Transmission – No Shift' },
    { code: 'ELEC-001', label: 'Electrical – Battery Drain' },
    { code: 'ELEC-002', label: 'Electrical – Alternator Failure' },
    { code: 'BRKS-001', label: 'Brakes – ABS Malfunction' },
    { code: 'SUSP-001', label: 'Suspension – Control Arm' },
    { code: 'AC-001', label: 'HVAC – Compressor Failure' },
    { code: 'OTHER', label: 'Other (specify in description)' },
  ];

  constructor(
    private fb: FormBuilder,
    private warrantyService: WarrantyService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.claimForm = this.fb.group({
      vin: ['', [Validators.required, Validators.pattern(/^[A-HJ-NPR-Z0-9]{17}$/)]],
      inServiceDate: ['', Validators.required],
      currentOdometerReading: ['', [Validators.required, Validators.min(0), Validators.max(9999999)]],
      repairCode: ['', Validators.required],
      parts: ['', Validators.required],
      laborHours: ['', [Validators.required, Validators.min(0.1), Validators.max(99)]],
      failureDescription: ['', [Validators.required, Validators.minLength(20), Validators.maxLength(2000)]],
      serviceHistory: this.fb.array([]),
    });
  }

  get serviceHistoryArray(): FormArray {
    return this.claimForm.get('serviceHistory') as FormArray;
  }

  addServiceHistory(): void {
    const entry = this.fb.group({
      date: ['', Validators.required],
      odometerReading: ['', [Validators.required, Validators.min(0)]],
      repairCode: ['', Validators.required],
      description: ['', Validators.required],
    });
    this.serviceHistoryArray.push(entry);
  }

  removeServiceHistory(index: number): void {
    this.serviceHistoryArray.removeAt(index);
  }

  isFieldInvalid(fieldName: string): boolean {
    const control = this.claimForm.get(fieldName);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  getFieldError(fieldName: string): string {
    const control = this.claimForm.get(fieldName);
    if (!control || !control.errors) return '';
    if (control.errors['required']) return 'This field is required.';
    if (control.errors['pattern']) return 'VIN must be exactly 17 alphanumeric characters (no I, O, Q).';
    if (control.errors['min']) return `Value must be at least ${control.errors['min'].min}.`;
    if (control.errors['max']) return `Value must be at most ${control.errors['max'].max}.`;
    if (control.errors['minlength']) return `Minimum ${control.errors['minlength'].requiredLength} characters required.`;
    if (control.errors['maxlength']) return `Maximum ${control.errors['maxlength'].requiredLength} characters allowed.`;
    return 'Invalid value.';
  }

  onSubmit(): void {
    if (this.claimForm.invalid) {
      this.claimForm.markAllAsTouched();
      return;
    }
    this.isSubmitting = true;
    this.submitError = '';

    const payload: ClaimSubmission = this.claimForm.value;

    this.warrantyService.submitClaim(payload).subscribe({
      next: (response) => {
        this.router.navigate(['/claims', response.claimId]);
      },
      error: (err: Error) => {
        this.submitError = err.message;
        this.isSubmitting = false;
      },
    });
  }

  onZoneSelected(zone: SelectedZone): void {
    // Auto-fill repair code from zone selection
    this.claimForm.patchValue({ repairCode: zone.repairCode });

    // Append zone description to failure description (don't overwrite existing text)
    const current: string = this.claimForm.get('failureDescription')?.value ?? '';
    const append = zone.defaultDescription;
    const newVal = current ? `${current}\n[${zone.label}] ${append}` : `[${zone.label}] ${append}`;
    this.claimForm.patchValue({ failureDescription: newVal.slice(0, 2000) });
  }

  onReset(): void {
    this.claimForm.reset();
    while (this.serviceHistoryArray.length) {
      this.serviceHistoryArray.removeAt(0);
    }
    this.submitError = '';
  }
}
