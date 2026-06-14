import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, FormControl, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { getRepairCodeEntry } from '../../data/repair-codes.data';
import { WarrantyService } from '../../services/warranty.service';
import { ClaimSubmission, ZoneIssueEvent } from '../../models/claim.model';

@Component({
  selector: 'app-claim-form',
  templateUrl: './claim-form.component.html',
  styleUrls: ['./claim-form.component.css'],
})
export class ClaimFormComponent implements OnInit {
  claimForm!: FormGroup;
  isSubmitting = false;
  submitError = '';
  /** Incremented to tell the zone selector to clear all selections */
  zoneClearSignal = 0;
  /** Standalone picker — selecting a code here adds it to repairCodes array */
  repairCodePicker = new FormControl('');
  /** Standalone picker for causal parts */
  causalPartInput = new FormControl('');
  /** Codes that arrived via zone selection, tracked for vehicle-change clearing */
  private zoneContributedCodes = new Set<string>();

  constructor(
    private fb: FormBuilder,
    private warrantyService: WarrantyService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.claimForm = this.fb.group({
      vin: ['', [Validators.required, Validators.pattern(/^[A-HJ-NPR-Z0-9]{17}$/)]],
      inServiceDate: ['', Validators.required],
      repairOrderDate: [this.getTodayDate(), Validators.required],
      currentOdometerReading: ['', [Validators.required, Validators.min(0), Validators.max(9999999)]],
      repairCodes: this.fb.array([]),
      causalParts: this.fb.array([]),
      partsCostEur: ['', [Validators.required, Validators.min(0)]],
      laborHours: ['', [Validators.required, Validators.min(0.1), Validators.max(99)]],
      failureDescription: ['', [Validators.required, Validators.minLength(20), Validators.maxLength(2000)]],
      serviceHistory: this.fb.array([]),
    });
    // When user picks a code in the combobox, add it to the array then reset the picker
    this.repairCodePicker.valueChanges.subscribe((code) => {
      const trimmed = String(code ?? '').trim();
      if (trimmed) {
        this.addRepairCode(trimmed);
        // Reset picker without triggering another emission
        setTimeout(() => this.repairCodePicker.setValue('', { emitEvent: false }), 0);
      }
    });
  }

  get serviceHistoryArray(): FormArray {
    return this.claimForm.get('serviceHistory') as FormArray;
  }

  get repairCodesArray(): FormArray {
    return this.claimForm.get('repairCodes') as FormArray;
  }

  get causalPartsArray(): FormArray {
    return this.claimForm.get('causalParts') as FormArray;
  }

  get causalPartsValue(): string[] {
    return this.causalPartsArray.value as string[];
  }

  get isCausalPartsInvalid(): boolean {
    return this.causalPartsArray.touched && this.causalPartsArray.length === 0;
  }

  addCausalPart(part: string): void {
    part = part.trim();
    if (!part || this.causalPartsValue.includes(part)) return;
    this.causalPartsArray.push(this.fb.control(part));
  }

  removeCausalPart(index: number): void {
    this.causalPartsArray.removeAt(index);
  }

  get repairCodesValue(): string[] {
    return this.repairCodesArray.value as string[];
  }

  get isRepairCodesInvalid(): boolean {
    return this.repairCodesArray.touched && this.repairCodesArray.length === 0;
  }

  addRepairCode(code: string): void {
    if (this.repairCodesValue.includes(code)) return;
    const wasFirst = this.repairCodesArray.length === 0;
    this.repairCodesArray.push(this.fb.control(code));
    if (wasFirst) {
      this.applyRepairCodeDefaults(code);
    }
  }

  removeRepairCode(index: number): void {
    const code: string = this.repairCodesArray.at(index).value;
    this.zoneContributedCodes.delete(code);
    this.repairCodesArray.removeAt(index);
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
    this.repairCodesArray.markAsTouched();
    this.causalPartsArray.markAsTouched();
    if (this.claimForm.invalid || this.repairCodesArray.length === 0 || this.causalPartsArray.length === 0) {
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

  /** Zone selector emitted a new issue — add it to the repairCodes array */
  onIssueAdded(event: ZoneIssueEvent): void {
    this.zoneContributedCodes.add(event.repairCode);
    this.addRepairCode(event.repairCode);
  }

  /** Zone selector removed an issue — remove its code from the array */
  onIssueRemoved(event: ZoneIssueEvent): void {
    const idx = this.repairCodesValue.indexOf(event.repairCode);
    if (idx !== -1) {
      this.repairCodesArray.removeAt(idx);
    }
    this.zoneContributedCodes.delete(event.repairCode);
  }

  /** Vehicle type changed — remove only zone-contributed codes, keep manual ones */
  onAllZonesCleared(): void {
    for (const code of this.zoneContributedCodes) {
      const idx = this.repairCodesValue.indexOf(code);
      if (idx !== -1) this.repairCodesArray.removeAt(idx);
    }
    this.zoneContributedCodes.clear();
  }

  onReset(): void {
    this.claimForm.reset();
    while (this.serviceHistoryArray.length) {
      this.serviceHistoryArray.removeAt(0);
    }
    while (this.repairCodesArray.length) {
      this.repairCodesArray.removeAt(0);
    }
    while (this.causalPartsArray.length) {
      this.causalPartsArray.removeAt(0);
    }
    this.repairCodePicker.setValue('', { emitEvent: false });
    this.causalPartInput.setValue('', { emitEvent: false });
    this.zoneContributedCodes.clear();
    this.claimForm.patchValue({ repairOrderDate: this.getTodayDate() });
    this.zoneClearSignal++;
    this.submitError = '';
  }

  private applyRepairCodeDefaults(repairCode: string): void {
    const selectedRepair = getRepairCodeEntry(repairCode);
    if (!selectedRepair) return;
    if (selectedRepair.causalPart && !this.causalPartsValue.includes(selectedRepair.causalPart)) {
      this.causalPartsArray.push(this.fb.control(selectedRepair.causalPart));
    }
    this.claimForm.patchValue({
      laborHours: selectedRepair.standardLaborHours ?? this.claimForm.get('laborHours')?.value,
    });
  }

  private getTodayDate(): string {
    return new Date().toISOString().slice(0, 10);
  }
}
