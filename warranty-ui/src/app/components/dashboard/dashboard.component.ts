import { Component, OnInit } from '@angular/core';
import { WarrantyService } from '../../services/warranty.service';
import { ClaimQueueItem, ClaimDisposition } from '../../models/claim.model';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
})
export class DashboardComponent implements OnInit {
  claims: ClaimQueueItem[] = [];
  filteredClaims: ClaimQueueItem[] = [];
  isLoading = true;
  loadError = '';
  filterDisposition: 'ALL' | ClaimDisposition = 'ALL';
  searchVin = '';

  constructor(private warrantyService: WarrantyService) {}

  ngOnInit(): void {
    // Subscribe to locally cached claim results.
    this.warrantyService.claimQueue$.subscribe((queue) => {
      this.claims = queue;
      this.applyFilters();
    });

    // Load any cached claims persisted by the submit flow.
    this.warrantyService.getClaimQueue().subscribe({
      next: () => { this.isLoading = false; },
      error: (err: Error) => {
        this.isLoading = false;
        if (this.claims.length === 0) {
          this.loadError = err.message;
        }
      },
    });
  }

  applyFilters(): void {
    this.filteredClaims = this.claims.filter((c) => {
      const matchDisposition = this.filterDisposition === 'ALL' || c.disposition === this.filterDisposition;
      const matchVin = !this.searchVin || c.vin.toUpperCase().includes(this.searchVin.toUpperCase());
      return matchDisposition && matchVin;
    });
  }

  setFilter(disposition: string): void {
    this.filterDisposition = disposition as 'ALL' | ClaimDisposition;
    this.applyFilters();
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  get stats(): { approved: number; rejected: number; pending: number; total: number } {
    return {
      total: this.claims.length,
      approved: this.claims.filter((c) => c.disposition === 'APPROVED').length,
      rejected: this.claims.filter((c) => c.disposition === 'REJECTED').length,
      pending: this.claims.filter((c) => c.disposition === 'PENDING').length,
    };
  }

  trackByClaim(_: number, item: ClaimQueueItem): string {
    return item.claimId;
  }
}
