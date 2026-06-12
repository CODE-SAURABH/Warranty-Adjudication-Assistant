import { Component, Input } from '@angular/core';
import { ClaimDisposition } from '../../models/claim.model';

@Component({
  selector: 'app-disposition-badge',
  template: `
    <span class="badge" [ngClass]="badgeClass">
      <span class="badge-icon">{{ icon }}</span>
      {{ label }}
    </span>
  `,
  styles: [`
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .badge-approved {
      background: #d1fae5;
      color: #065f46;
      border: 1px solid #6ee7b7;
    }
    .badge-rejected {
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #fca5a5;
    }
    .badge-pending {
      background: #fef3c7;
      color: #92400e;
      border: 1px solid #fcd34d;
    }
    .badge-icon { font-size: 14px; }
  `],
})
export class DispositionBadgeComponent {
  @Input() disposition: ClaimDisposition = 'PENDING';

  get badgeClass(): string {
    const map: Record<ClaimDisposition, string> = {
      APPROVED: 'badge-approved',
      REJECTED: 'badge-rejected',
      PENDING: 'badge-pending',
    };
    return map[this.disposition];
  }

  get label(): string {
    const map: Record<ClaimDisposition, string> = {
      APPROVED: 'Approved',
      REJECTED: 'Rejected',
      PENDING: 'Pending Review',
    };
    return map[this.disposition];
  }

  get icon(): string {
    const map: Record<ClaimDisposition, string> = {
      APPROVED: '✓',
      REJECTED: '✕',
      PENDING: '⏳',
    };
    return map[this.disposition];
  }
}
