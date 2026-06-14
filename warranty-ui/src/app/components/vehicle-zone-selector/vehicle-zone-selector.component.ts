import {
  Component,
  Output,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { getRepairCodeEntry } from '../../data/repair-codes.data';
import { VehicleType, VehicleView, VehicleZone, ZoneIssueEvent } from '../../models/claim.model';

interface ZoneIssue {
  repairCode: string;
  label: string;
  description: string;
}

interface ZonePopup {
  zoneId: string;
  zoneLabel: string;
  x: number;
  y: number;
  issues: ZoneIssue[];
}

function zoneIssue(repairCode: string, label: string, description: string): ZoneIssue {
  const entry = getRepairCodeEntry(repairCode);
  if (!entry) {
    throw new Error(`Unknown repair code in zoneIssueMap: ${repairCode}`);
  }
  return {
    repairCode: entry.code,
    label,
    description,
  };
}

@Component({
  selector: 'app-vehicle-zone-selector',
  templateUrl: './vehicle-zone-selector.component.html',
  styleUrls: ['./vehicle-zone-selector.component.css'],
})
export class VehicleZoneSelectorComponent implements OnChanges {
  /** Emitted each time the user applies an issue for a zone */
  @Output() issueAdded = new EventEmitter<ZoneIssueEvent>();
  /** Emitted when the user removes an individual issue */
  @Output() issueRemoved = new EventEmitter<ZoneIssueEvent>();
  /** Emitted when the vehicle type is changed and all selections are cleared */
  @Output() allCleared = new EventEmitter<void>();
  /** Increment from parent to clear all zone selections */
  @Input() clearSignal = 0;

  vehicleType: VehicleType = 'car';
  activeView: VehicleView = 'left';
  hoveredZone: string | null = null;
  /** Set of zone IDs that have at least one issue selected */
  selectedZones: Set<string> = new Set();
  /** Per-zone list of selected issues (multiple allowed) */
  selectedZoneIssues: Map<string, ZoneIssue[]> = new Map();
  popup: ZonePopup | null = null;
  /** Repair codes currently checked in the open popup */
  popupChecked: Set<string> = new Set();

  // ── Vehicle-change warning ───────────────────────────────────────────────
  showVehicleChangeWarning = false;
  pendingVehicleType: VehicleType | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['clearSignal'] && !changes['clearSignal'].firstChange) {
      this._clearAll();
    }
  }

  /** Public — called by parent via ViewChild or clearSignal input */
  clearAll(): void {
    this._clearAll();
  }

  private _clearAll(): void {
    this.selectedZones.clear();
    this.selectedZoneIssues.clear();
    this.popupChecked.clear();
    this.popup = null;
  }

  /** Flat list of all selected issues for use in the summary template */
  get selectedIssuesList(): Array<{ zoneId: string; zoneLabel: string; issue: ZoneIssue }> {
    const result: Array<{ zoneId: string; zoneLabel: string; issue: ZoneIssue }> = [];
    for (const [zoneId, issues] of this.selectedZoneIssues.entries()) {
      const zoneLabel = this.getZoneLabel(zoneId);
      for (const issue of issues) {
        result.push({ zoneId, zoneLabel, issue });
      }
    }
    return result;
  }

  readonly vehicleTypes: { type: VehicleType; label: string; icon: string }[] = [
    { type: 'car', label: 'Car / Sedan', icon: '🚗' },
    { type: 'bike', label: 'Motorcycle', icon: '🏍️' },
    { type: 'truck', label: 'Truck / SUV', icon: '🚙' },
  ];

  readonly views: { view: VehicleView; label: string }[] = [
    { view: 'front', label: 'Front' },
    { view: 'left', label: 'Left Side' },
    { view: 'rear', label: 'Rear' },
    { view: 'right', label: 'Right Side' },
    { view: 'top', label: 'Top / Roof' },
  ];

  // Zone issue catalog per zone id
  private readonly zoneIssueMap: Record<string, ZoneIssue[]> = {
    // --- CAR ZONES ---
    'car-engine': [
      zoneIssue('ENG-001', 'Oil Leak', 'Engine oil leak detected from gasket or seal area.'),
      zoneIssue('ENG-002', 'Overheating', 'Engine temperature exceeds normal operating range.'),
      zoneIssue('ENG-003', 'Misfiring / Rough Idle', 'Engine misfiring or rough idle condition.'),
    ],
    'car-hood': [
      zoneIssue('ENG-001', 'Hood Latch Failure', 'Hood latch does not engage or disengage properly.'),
      zoneIssue('BODY-001', 'Hood Panel Damage', 'Hood panel shows signs of deformation or misalignment.'),
    ],
    'car-front-bumper': [
      zoneIssue('BODY-001', 'Bumper Damage', 'Front bumper shows cracking, deformation, or misalignment.'),
      zoneIssue('ELEC-003', 'Parking Sensor Failure', 'Front parking sensors not detecting obstacles.'),
    ],
    'car-front-lights': [
      zoneIssue('ELEC-004', 'Headlight Failure', 'One or more headlight units not functioning.'),
      zoneIssue('ELEC-005', 'DRL Malfunction', 'Daytime running lights not operating correctly.'),
    ],
    'car-windshield': [
      zoneIssue('BODY-002', 'Windshield Crack', 'Windshield crack or chip affecting driver visibility.'),
      zoneIssue('ELEC-006', 'Wiper Motor Failure', 'Windshield wipers not operating at correct speed or not at all.'),
    ],
    'car-roof': [
      zoneIssue('BODY-003', 'Roof Panel Issue', 'Roof panel shows dents, rust, or water ingress.'),
      zoneIssue('AC-001', 'Sunroof Malfunction', 'Sunroof does not open/close or seals are leaking.'),
    ],
    'car-door-fl': [
      zoneIssue('BODY-004', 'Door Latch/Lock', 'Front left door latch or lock mechanism failure.'),
      zoneIssue('ELEC-007', 'Power Window Failure', 'Front left power window motor or regulator failed.'),
      zoneIssue('BODY-005', 'Door Seal Leak', 'Door weather seal allows water or wind ingress.'),
    ],
    'car-door-rl': [
      zoneIssue('BODY-004', 'Door Latch/Lock', 'Rear left door latch or lock mechanism failure.'),
      zoneIssue('ELEC-007', 'Power Window Failure', 'Rear left power window motor or regulator failed.'),
      zoneIssue('BODY-005', 'Door Seal Leak', 'Door weather seal allows water or wind ingress.'),
    ],
    'car-door-fr': [
      zoneIssue('BODY-004', 'Door Latch/Lock', 'Front right door latch or lock mechanism failure.'),
      zoneIssue('ELEC-007', 'Power Window Failure', 'Front right power window motor or regulator failed.'),
    ],
    'car-door-rr': [
      zoneIssue('BODY-004', 'Door Latch/Lock', 'Rear right door latch or lock mechanism failure.'),
      zoneIssue('ELEC-007', 'Power Window Failure', 'Rear right power window motor or regulator failed.'),
    ],
    'car-wheel-fl': [
      zoneIssue('BRKS-001', 'Brake ABS Malfunction', 'ABS warning on front left wheel speed sensor.'),
      zoneIssue('SUSP-001', 'Suspension / Strut', 'Front left strut or control arm worn or damaged.'),
      zoneIssue('TIRE-001', 'Tire / Rim Damage', 'Tire pressure loss or rim deformation on front left.'),
    ],
    'car-wheel-rl': [
      zoneIssue('BRKS-001', 'Brake ABS Malfunction', 'ABS warning on rear left wheel speed sensor.'),
      zoneIssue('SUSP-002', 'Rear Suspension', 'Rear left shock absorber or spring issue.'),
      zoneIssue('TIRE-001', 'Tire / Rim Damage', 'Tire pressure loss or rim deformation on rear left.'),
    ],
    'car-wheel-fr': [
      zoneIssue('BRKS-001', 'Brake ABS Malfunction', 'ABS warning on front right wheel speed sensor.'),
      zoneIssue('SUSP-001', 'Suspension / Strut', 'Front right strut or control arm worn or damaged.'),
      zoneIssue('TIRE-001', 'Tire / Rim Damage', 'Tire pressure loss or rim deformation on front right.'),
    ],
    'car-wheel-rr': [
      zoneIssue('BRKS-001', 'Brake ABS Malfunction', 'ABS warning on rear right wheel speed sensor.'),
      zoneIssue('SUSP-002', 'Rear Suspension', 'Rear right shock absorber or spring issue.'),
      zoneIssue('TIRE-001', 'Tire / Rim Damage', 'Tire pressure loss or rim deformation on rear right.'),
    ],
    'car-transmission': [
      zoneIssue('TRANS-001', 'Transmission Slipping', 'Transmission slips between gears under load.'),
      zoneIssue('TRANS-002', 'No Shift / Hard Shift', 'Transmission fails to shift or shifts harshly.'),
    ],
    'car-exhaust': [
      zoneIssue('EXH-001', 'Exhaust Leak', 'Exhaust gases leaking from manifold, pipe, or joint.'),
      zoneIssue('EXH-002', 'Catalytic Converter', 'Catalytic converter efficiency below threshold.'),
    ],
    'car-rear-bumper': [
      zoneIssue('BODY-001', 'Bumper Damage', 'Rear bumper shows cracking or misalignment.'),
      zoneIssue('ELEC-003', 'Rear Sensor Failure', 'Rear parking sensors not functioning.'),
    ],
    'car-trunk': [
      zoneIssue('BODY-006', 'Trunk Latch Failure', 'Trunk lid does not latch or release properly.'),
      zoneIssue('ELEC-008', 'Power Tailgate Issue', 'Power trunk/tailgate motor or sensor failed.'),
    ],
    'car-rear-lights': [
      zoneIssue('ELEC-009', 'Tail Light Failure', 'Tail light, brake light, or reverse light not working.'),
    ],
    'car-battery': [
      zoneIssue('ELEC-001', 'Battery Drain', 'Battery discharges unexpectedly overnight or within hours.'),
      zoneIssue('ELEC-002', 'Alternator Failure', 'Alternator not charging battery while engine running.'),
    ],
    'car-ac': [
      zoneIssue('AC-001', 'A/C Compressor Failure', 'Air conditioning compressor not engaging or blowing warm.'),
      zoneIssue('AC-002', 'Refrigerant Leak', 'A/C system refrigerant level low due to leak.'),
    ],
    'car-interior': [
      zoneIssue('INT-001', 'Dashboard Warning Light', 'Persistent warning light on instrument cluster.'),
      zoneIssue('INT-002', 'Infotainment Failure', 'Head unit / display screen not responding or blank.'),
      zoneIssue('ELEC-010', 'Airbag System Fault', 'Airbag warning light on or SRS fault code present.'),
    ],
    // --- BIKE ZONES ---
    'bike-engine': [
      zoneIssue('ENG-001', 'Engine Oil Leak', 'Engine oil leaking from gasket or case seam.'),
      zoneIssue('ENG-003', 'Misfiring / No Start', 'Engine misfires or fails to start.'),
    ],
    'bike-front-wheel': [
      zoneIssue('BRKS-002', 'Front Brake Fade', 'Front brake pad worn or caliper seized.'),
      zoneIssue('SUSP-003', 'Fork Seal Leak', 'Front fork seals leaking oil.'),
      zoneIssue('TIRE-001', 'Tire Damage', 'Front tire puncture or sidewall damage.'),
    ],
    'bike-rear-wheel': [
      zoneIssue('BRKS-003', 'Rear Brake Issue', 'Rear brake pad worn or drum issue.'),
      zoneIssue('SUSP-004', 'Rear Shock Failure', 'Rear shock absorber leaking or collapsed.'),
      zoneIssue('TIRE-001', 'Tire Damage', 'Rear tire puncture or excessive wear.'),
    ],
    'bike-fuel-tank': [
      zoneIssue('FUEL-001', 'Fuel Leak', 'Fuel tank or fuel line leaking.'),
      zoneIssue('FUEL-002', 'Fuel Gauge Failure', 'Fuel gauge reads inaccurately or not at all.'),
    ],
    'bike-exhaust': [
      zoneIssue('EXH-001', 'Exhaust Leak', 'Header pipe or muffler leaking exhaust gases.'),
    ],
    'bike-handlebars': [
      zoneIssue('ELEC-011', 'Switch Gear Failure', 'Handlebar switches (turn signal, horn, starter) not working.'),
      zoneIssue('SUSP-003', 'Steering Bearing', 'Steering head bearings worn causing handlebar play.'),
    ],
    'bike-lights': [
      zoneIssue('ELEC-004', 'Headlight Failure', 'Headlight bulb or unit not functioning.'),
      zoneIssue('ELEC-009', 'Turn Signal Failure', 'Turn signal indicators not flashing or dead.'),
    ],
    // --- TRUCK ZONES ---
    'truck-engine': [
      zoneIssue('ENG-001', 'Oil Leak', 'Heavy-duty engine oil leaking from seals.'),
      zoneIssue('ENG-002', 'Overheating', 'Engine overheating under load or highway.'),
    ],
    'truck-front-axle': [
      zoneIssue('SUSP-005', 'Front Axle / Hub', 'Front axle hub bearing worn or damaged.'),
      zoneIssue('BRKS-004', 'Air Brake Issue', 'Air brake system pressure drop or valve failure.'),
    ],
    'truck-rear-axle': [
      zoneIssue('TRANS-003', 'Differential Failure', 'Rear differential noise or fluid leak.'),
      zoneIssue('BRKS-004', 'Air Brake Issue', 'Rear air brake system failure.'),
    ],
    'truck-cab': [
      zoneIssue('INT-001', 'Dashboard Warning', 'Instrument cluster warning light active.'),
      zoneIssue('AC-001', 'A/C Failure', 'Cab air conditioning not cooling.'),
    ],
    'truck-cargo-bed': [
      zoneIssue('BODY-007', 'Bed Liner Damage', 'Cargo bed liner cracked or delaminating.'),
      zoneIssue('ELEC-008', 'Tailgate Actuator', 'Power tailgate or tonneau cover motor failed.'),
    ],
    'truck-exhaust': [
      zoneIssue('EXH-003', 'DPF / EGR Issue', 'Diesel particulate filter or EGR valve fault.'),
      zoneIssue('EXH-001', 'Exhaust Leak', 'Exhaust manifold or turbo downpipe leaking.'),
    ],
  };

  getZonesForView(): VehicleZone[] {
    return this.svgZones[this.vehicleType]?.[this.activeView] ?? [];
  }

  getIssuesForZone(zoneId: string): ZoneIssue[] {
    return this.zoneIssueMap[zoneId] ?? [];
  }

  onZoneClick(zone: VehicleZone, event: MouseEvent): void {
    const svgEl = (event.target as SVGElement).closest('svg');
    if (!svgEl) return;
    const containerRect = (svgEl.parentElement as HTMLElement).getBoundingClientRect();
    const popupX = event.clientX - containerRect.left;
    const popupY = event.clientY - containerRect.top;

    // Pre-populate checkboxes with already-selected issues for this zone
    const existing = this.selectedZoneIssues.get(zone.id) ?? [];
    this.popupChecked = new Set(existing.map(i => i.repairCode));

    this.popup = {
      zoneId: zone.id,
      zoneLabel: zone.label,
      x: Math.min(popupX, containerRect.width - 280),
      y: Math.min(popupY + 12, containerRect.height - 220),
      issues: this.getIssuesForZone(zone.id),
    };
  }

  /** Toggle a checkbox in the popup */
  togglePopupIssue(repairCode: string): void {
    if (this.popupChecked.has(repairCode)) {
      this.popupChecked.delete(repairCode);
    } else {
      this.popupChecked.add(repairCode);
    }
  }

  isIssueChecked(repairCode: string): boolean {
    return this.popupChecked.has(repairCode);
  }

  /** Apply the current checkbox state: diff vs previous selection, emit events */
  applyPopupIssues(): void {
    if (!this.popup) return;
    const { zoneId, zoneLabel, issues } = this.popup;

    const prevCodes = new Set((this.selectedZoneIssues.get(zoneId) ?? []).map(i => i.repairCode));
    const newCodes = new Set(this.popupChecked);

    // Emit added issues
    for (const issue of issues) {
      if (newCodes.has(issue.repairCode) && !prevCodes.has(issue.repairCode)) {
        this.issueAdded.emit({ zoneId, zoneLabel, repairCode: issue.repairCode, issueLabel: issue.label });
      }
    }
    // Emit removed issues
    for (const issue of issues) {
      if (prevCodes.has(issue.repairCode) && !newCodes.has(issue.repairCode)) {
        this.issueRemoved.emit({ zoneId, zoneLabel, repairCode: issue.repairCode, issueLabel: issue.label });
      }
    }

    // Update internal state
    const selectedIssues = issues.filter(i => newCodes.has(i.repairCode));
    if (selectedIssues.length > 0) {
      this.selectedZones.add(zoneId);
      this.selectedZoneIssues.set(zoneId, selectedIssues);
    } else {
      this.selectedZones.delete(zoneId);
      this.selectedZoneIssues.delete(zoneId);
    }

    this.popup = null;
    this.popupChecked.clear();
  }

  /** Remove a single issue from a zone tag (× button in summary) */
  removeIssue(zoneId: string, repairCode: string): void {
    const issues = this.selectedZoneIssues.get(zoneId) ?? [];
    const issue = issues.find(i => i.repairCode === repairCode);
    if (!issue) return;
    const updated = issues.filter(i => i.repairCode !== repairCode);
    if (updated.length === 0) {
      this.selectedZones.delete(zoneId);
      this.selectedZoneIssues.delete(zoneId);
    } else {
      this.selectedZoneIssues.set(zoneId, updated);
    }
    this.issueRemoved.emit({ zoneId, zoneLabel: this.getZoneLabel(zoneId), repairCode, issueLabel: issue.label });
  }

  closePopup(): void {
    this.popup = null;
  }

  @HostListener('document:keydown.escape')
  onEsc(): void {
    this.popup = null;
  }

  setVehicleType(type: VehicleType): void {
    if (type === this.vehicleType) return;
    if (this.selectedZones.size > 0) {
      // Show inline warning instead of immediately switching
      this.pendingVehicleType = type;
      this.showVehicleChangeWarning = true;
      return;
    }
    this._applyVehicleType(type);
  }

  confirmVehicleChange(): void {
    if (!this.pendingVehicleType) return;
    this._clearAll();
    this.allCleared.emit();
    this._applyVehicleType(this.pendingVehicleType);
    this.pendingVehicleType = null;
    this.showVehicleChangeWarning = false;
  }

  cancelVehicleChange(): void {
    this.pendingVehicleType = null;
    this.showVehicleChangeWarning = false;
  }

  private _applyVehicleType(type: VehicleType): void {
    this.vehicleType = type;
    this.activeView = 'left';
    this.popup = null;
  }

  setView(view: VehicleView): void {
    this.activeView = view;
    this.popup = null;
  }

  rotateView(dir: 1 | -1): void {
    const views = this.views.map(v => v.view);
    const idx = views.indexOf(this.activeView);
    const next = (idx + dir + views.length) % views.length;
    this.setView(views[next]);
  }

  isZoneSelected(zoneId: string): boolean {
    return this.selectedZones.has(zoneId);
  }

  /** Search all views for the current vehicle type to find a zone's label */
  getZoneLabel(zoneId: string): string {
    const allViews = this.svgZones[this.vehicleType] ?? {};
    for (const zones of Object.values(allViews)) {
      const match = (zones as VehicleZone[]).find(z => z.id === zoneId);
      if (match) return match.label;
    }
    return zoneId;
  }

  // ─── SVG Zone Definitions ─────────────────────────────────────────────────
  readonly svgZones: Record<string, Partial<Record<VehicleView, VehicleZone[]>>> = {
    car: {
      left: [
        { id: 'car-wheel-fl', label: 'Front Wheel', repairCode: 'SUSP-001', description: '', view: 'left',
          svgPath: 'M 62 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-wheel-rl', label: 'Rear Wheel', repairCode: 'SUSP-002', description: '', view: 'left',
          svgPath: 'M 338 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-engine', label: 'Engine Bay', repairCode: 'ENG-001', description: '', view: 'left',
          svgPath: 'M 22 115 L 40 80 L 110 60 L 110 148 L 22 148 Z' },
        { id: 'car-door-fl', label: 'Front Door', repairCode: 'BODY-004', description: '', view: 'left',
          svgPath: 'M 140 68 L 220 65 L 220 148 L 140 148 Z' },
        { id: 'car-door-rl', label: 'Rear Door', repairCode: 'BODY-004', description: '', view: 'left',
          svgPath: 'M 222 65 L 305 68 L 305 148 L 222 148 Z' },
        { id: 'car-windshield', label: 'Windshield', repairCode: 'BODY-002', description: '', view: 'left',
          svgPath: 'M 108 62 L 140 48 L 140 100 L 108 108 Z' },
        { id: 'car-roof', label: 'Roof', repairCode: 'BODY-003', description: '', view: 'left',
          svgPath: 'M 140 45 L 270 45 L 270 62 L 140 62 Z' },
        { id: 'car-trunk', label: 'Trunk / Boot', repairCode: 'BODY-006', description: '', view: 'left',
          svgPath: 'M 305 65 L 360 78 L 360 148 L 305 148 Z' },
        { id: 'car-exhaust', label: 'Exhaust', repairCode: 'EXH-001', description: '', view: 'left',
          svgPath: 'M 345 150 L 380 150 L 380 162 L 345 162 Z' },
      ],
      right: [
        { id: 'car-wheel-fr', label: 'Front Wheel', repairCode: 'SUSP-001', description: '', view: 'right',
          svgPath: 'M 338 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-wheel-rr', label: 'Rear Wheel', repairCode: 'SUSP-002', description: '', view: 'right',
          svgPath: 'M 62 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-engine', label: 'Engine Bay', repairCode: 'ENG-001', description: '', view: 'right',
          svgPath: 'M 378 115 L 360 80 L 290 60 L 290 148 L 378 148 Z' },
        { id: 'car-door-fr', label: 'Front Door', repairCode: 'BODY-004', description: '', view: 'right',
          svgPath: 'M 260 68 L 180 65 L 180 148 L 260 148 Z' },
        { id: 'car-door-rr', label: 'Rear Door', repairCode: 'BODY-004', description: '', view: 'right',
          svgPath: 'M 178 65 L 95 68 L 95 148 L 178 148 Z' },
        { id: 'car-windshield', label: 'Windshield', repairCode: 'BODY-002', description: '', view: 'right',
          svgPath: 'M 292 62 L 260 48 L 260 100 L 292 108 Z' },
        { id: 'car-roof', label: 'Roof', repairCode: 'BODY-003', description: '', view: 'right',
          svgPath: 'M 260 45 L 130 45 L 130 62 L 260 62 Z' },
        { id: 'car-trunk', label: 'Trunk', repairCode: 'BODY-006', description: '', view: 'right',
          svgPath: 'M 95 65 L 40 78 L 40 148 L 95 148 Z' },
      ],
      front: [
        { id: 'car-front-bumper', label: 'Front Bumper', repairCode: 'BODY-001', description: '', view: 'front',
          svgPath: 'M 60 155 L 340 155 L 350 180 L 50 180 Z' },
        { id: 'car-front-lights', label: 'Headlights', repairCode: 'ELEC-004', description: '', view: 'front',
          svgPath: 'M 60 95 L 140 95 L 140 145 L 60 145 Z M 260 95 L 340 95 L 340 145 L 260 145 Z' },
        { id: 'car-hood', label: 'Hood', repairCode: 'BODY-001', description: '', view: 'front',
          svgPath: 'M 80 60 L 320 60 L 340 100 L 60 100 Z' },
        { id: 'car-windshield', label: 'Windshield', repairCode: 'BODY-002', description: '', view: 'front',
          svgPath: 'M 100 25 L 300 25 L 310 60 L 90 60 Z' },
        { id: 'car-wheel-fl', label: 'Front-Left Wheel', repairCode: 'SUSP-001', description: '', view: 'front',
          svgPath: 'M 22 118 m -22 0 a 22 22 0 1 0 44 0 a 22 22 0 1 0 -44 0' },
        { id: 'car-wheel-fr', label: 'Front-Right Wheel', repairCode: 'SUSP-001', description: '', view: 'front',
          svgPath: 'M 378 118 m -22 0 a 22 22 0 1 0 44 0 a 22 22 0 1 0 -44 0' },
        { id: 'car-battery', label: 'Battery / Electrical', repairCode: 'ELEC-001', description: '', view: 'front',
          svgPath: 'M 160 80 L 240 80 L 240 100 L 160 100 Z' },
      ],
      rear: [
        { id: 'car-rear-bumper', label: 'Rear Bumper', repairCode: 'BODY-001', description: '', view: 'rear',
          svgPath: 'M 60 155 L 340 155 L 350 180 L 50 180 Z' },
        { id: 'car-rear-lights', label: 'Tail Lights', repairCode: 'ELEC-009', description: '', view: 'rear',
          svgPath: 'M 60 95 L 140 95 L 140 155 L 60 155 Z M 260 95 L 340 95 L 340 155 L 260 155 Z' },
        { id: 'car-trunk', label: 'Trunk Lid', repairCode: 'BODY-006', description: '', view: 'rear',
          svgPath: 'M 80 50 L 320 50 L 340 100 L 60 100 Z' },
        { id: 'car-windshield', label: 'Rear Window', repairCode: 'BODY-002', description: '', view: 'rear',
          svgPath: 'M 110 25 L 290 25 L 300 50 L 100 50 Z' },
        { id: 'car-exhaust', label: 'Exhaust Pipe(s)', repairCode: 'EXH-001', description: '', view: 'rear',
          svgPath: 'M 148 162 L 198 162 L 198 177 L 148 177 Z M 202 162 L 252 162 L 252 177 L 202 177 Z' },
        { id: 'car-wheel-rl', label: 'Rear-Left Wheel', repairCode: 'SUSP-002', description: '', view: 'rear',
          svgPath: 'M 22 128 m -22 0 a 22 22 0 1 0 44 0 a 22 22 0 1 0 -44 0' },
        { id: 'car-wheel-rr', label: 'Rear-Right Wheel', repairCode: 'SUSP-002', description: '', view: 'rear',
          svgPath: 'M 378 128 m -22 0 a 22 22 0 1 0 44 0 a 22 22 0 1 0 -44 0' },
      ],
      top: [
        { id: 'car-hood', label: 'Hood', repairCode: 'ENG-001', description: '', view: 'top',
          svgPath: 'M 80 10 L 320 10 L 330 120 L 70 120 Z' },
        { id: 'car-roof', label: 'Roof', repairCode: 'BODY-003', description: '', view: 'top',
          svgPath: 'M 90 125 L 310 125 L 300 200 L 100 200 Z' },
        { id: 'car-trunk', label: 'Trunk', repairCode: 'BODY-006', description: '', view: 'top',
          svgPath: 'M 100 205 L 300 205 L 290 280 L 110 280 Z' },
        { id: 'car-wheel-fl', label: 'Front-Left Wheel', repairCode: 'SUSP-001', description: '', view: 'top',
          svgPath: 'M 20 20 L 65 20 L 65 90 L 20 90 Z' },
        { id: 'car-wheel-fr', label: 'Front-Right Wheel', repairCode: 'SUSP-001', description: '', view: 'top',
          svgPath: 'M 335 20 L 380 20 L 380 90 L 335 90 Z' },
        { id: 'car-wheel-rl', label: 'Rear-Left Wheel', repairCode: 'SUSP-002', description: '', view: 'top',
          svgPath: 'M 20 215 L 65 215 L 65 280 L 20 280 Z' },
        { id: 'car-wheel-rr', label: 'Rear-Right Wheel', repairCode: 'SUSP-002', description: '', view: 'top',
          svgPath: 'M 335 215 L 380 215 L 380 280 L 335 280 Z' },
        { id: 'car-interior', label: 'Interior / Cabin', repairCode: 'INT-001', description: '', view: 'top',
          svgPath: 'M 75 125 L 325 125 L 310 200 L 90 200 Z' },
        { id: 'car-ac', label: 'HVAC / Climate', repairCode: 'AC-001', description: '', view: 'top',
          svgPath: 'M 155 55 L 245 55 L 245 100 L 155 100 Z' },
        { id: 'car-battery', label: 'Battery Area', repairCode: 'ELEC-001', description: '', view: 'top',
          svgPath: 'M 80 40 L 150 40 L 150 80 L 80 80 Z' },
        { id: 'car-transmission', label: 'Drivetrain / Transmission', repairCode: 'TRANS-001', description: '', view: 'top',
          svgPath: 'M 160 140 L 240 140 L 240 185 L 160 185 Z' },
      ],
    },

    bike: {
      left: [
        { id: 'bike-engine', label: 'Engine', repairCode: 'ENG-001', description: '', view: 'left',
          svgPath: 'M 155 110 L 245 110 L 245 180 L 155 180 Z' },
        { id: 'bike-front-wheel', label: 'Front Wheel', repairCode: 'BRKS-002', description: '', view: 'left',
          svgPath: 'M 68 155 m -52 0 a 52 52 0 1 0 104 0 a 52 52 0 1 0 -104 0' },
        { id: 'bike-rear-wheel', label: 'Rear Wheel', repairCode: 'BRKS-003', description: '', view: 'left',
          svgPath: 'M 332 155 m -52 0 a 52 52 0 1 0 104 0 a 52 52 0 1 0 -104 0' },
        { id: 'bike-fuel-tank', label: 'Fuel Tank', repairCode: 'FUEL-001', description: '', view: 'left',
          svgPath: 'M 150 60 L 260 60 L 260 108 L 150 108 Z' },
        { id: 'bike-exhaust', label: 'Exhaust', repairCode: 'EXH-001', description: '', view: 'left',
          svgPath: 'M 248 175 L 360 165 L 360 185 L 248 195 Z' },
        { id: 'bike-handlebars', label: 'Handlebars / Controls', repairCode: 'ELEC-011', description: '', view: 'left',
          svgPath: 'M 88 55 L 145 55 L 145 80 L 88 80 Z' },
        { id: 'bike-lights', label: 'Lights', repairCode: 'ELEC-004', description: '', view: 'left',
          svgPath: 'M 28 80 L 80 75 L 80 105 L 28 110 Z' },
      ],
      front: [
        { id: 'bike-front-wheel', label: 'Front Wheel', repairCode: 'BRKS-002', description: '', view: 'front',
          svgPath: 'M 200 190 m -60 0 a 60 60 0 1 0 120 0 a 60 60 0 1 0 -120 0' },
        { id: 'bike-handlebars', label: 'Handlebars', repairCode: 'ELEC-011', description: '', view: 'front',
          svgPath: 'M 80 60 L 320 60 L 320 80 L 80 80 Z' },
        { id: 'bike-lights', label: 'Headlight', repairCode: 'ELEC-004', description: '', view: 'front',
          svgPath: 'M 160 25 L 240 25 L 240 60 L 160 60 Z' },
      ],
      rear: [
        { id: 'bike-rear-wheel', label: 'Rear Wheel', repairCode: 'BRKS-003', description: '', view: 'rear',
          svgPath: 'M 200 190 m -60 0 a 60 60 0 1 0 120 0 a 60 60 0 1 0 -120 0' },
        { id: 'bike-lights', label: 'Tail Light', repairCode: 'ELEC-009', description: '', view: 'rear',
          svgPath: 'M 155 25 L 245 25 L 245 60 L 155 60 Z' },
        { id: 'bike-exhaust', label: 'Exhaust Exit', repairCode: 'EXH-001', description: '', view: 'rear',
          svgPath: 'M 220 175 L 280 175 L 280 205 L 220 205 Z' },
      ],
      right: [
        { id: 'bike-engine', label: 'Engine', repairCode: 'ENG-001', description: '', view: 'right',
          svgPath: 'M 155 110 L 245 110 L 245 180 L 155 180 Z' },
        { id: 'bike-front-wheel', label: 'Front Wheel', repairCode: 'BRKS-002', description: '', view: 'right',
          svgPath: 'M 68 155 m -52 0 a 52 52 0 1 0 104 0 a 52 52 0 1 0 -104 0' },
        { id: 'bike-rear-wheel', label: 'Rear Wheel', repairCode: 'BRKS-003', description: '', view: 'right',
          svgPath: 'M 332 155 m -52 0 a 52 52 0 1 0 104 0 a 52 52 0 1 0 -104 0' },
        { id: 'bike-fuel-tank', label: 'Fuel Tank', repairCode: 'FUEL-001', description: '', view: 'right',
          svgPath: 'M 150 60 L 260 60 L 260 108 L 150 108 Z' },
        { id: 'bike-handlebars', label: 'Handlebars', repairCode: 'ELEC-011', description: '', view: 'right',
          svgPath: 'M 250 55 L 310 55 L 310 80 L 250 80 Z' },
      ],
      top: [
        { id: 'bike-fuel-tank', label: 'Fuel Tank', repairCode: 'FUEL-001', description: '', view: 'top',
          svgPath: 'M 155 60 L 245 60 L 245 150 L 155 150 Z' },
        { id: 'bike-engine', label: 'Engine', repairCode: 'ENG-001', description: '', view: 'top',
          svgPath: 'M 145 155 L 255 155 L 255 230 L 145 230 Z' },
        { id: 'bike-front-wheel', label: 'Front Wheel', repairCode: 'BRKS-002', description: '', view: 'top',
          svgPath: 'M 168 5 L 232 5 L 232 55 L 168 55 Z' },
        { id: 'bike-rear-wheel', label: 'Rear Wheel', repairCode: 'BRKS-003', description: '', view: 'top',
          svgPath: 'M 168 240 L 232 240 L 232 295 L 168 295 Z' },
      ],
    },

    truck: {
      left: [
        { id: 'truck-engine', label: 'Engine Bay', repairCode: 'ENG-001', description: '', view: 'left',
          svgPath: 'M 20 60 L 130 50 L 135 145 L 20 148 Z' },
        { id: 'truck-cab', label: 'Cab', repairCode: 'INT-001', description: '', view: 'left',
          svgPath: 'M 135 45 L 225 40 L 225 148 L 135 148 Z' },
        { id: 'truck-cargo-bed', label: 'Cargo Bed', repairCode: 'BODY-007', description: '', view: 'left',
          svgPath: 'M 228 55 L 370 55 L 370 148 L 228 148 Z' },
        { id: 'truck-front-axle', label: 'Front Axle / Wheel', repairCode: 'SUSP-005', description: '', view: 'left',
          svgPath: 'M 72 158 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
        { id: 'truck-rear-axle', label: 'Rear Axle / Wheel', repairCode: 'TRANS-003', description: '', view: 'left',
          svgPath: 'M 330 158 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
        { id: 'truck-exhaust', label: 'Exhaust / DPF', repairCode: 'EXH-003', description: '', view: 'left',
          svgPath: 'M 130 50 L 160 42 L 160 55 L 130 55 Z' },
      ],
      front: [
        { id: 'truck-engine', label: 'Engine / Grille', repairCode: 'ENG-001', description: '', view: 'front',
          svgPath: 'M 80 90 L 320 90 L 330 155 L 70 155 Z' },
        { id: 'truck-front-axle', label: 'Front Wheels', repairCode: 'SUSP-005', description: '', view: 'front',
          svgPath: 'M 20 118 m -20 0 a 20 20 0 1 0 40 0 a 20 20 0 1 0 -40 0 M 380 118 m -20 0 a 20 20 0 1 0 40 0 a 20 20 0 1 0 -40 0' },
        { id: 'truck-cab', label: 'Windshield / Cabin', repairCode: 'BODY-002', description: '', view: 'front',
          svgPath: 'M 90 20 L 310 20 L 320 90 L 80 90 Z' },
      ],
      rear: [
        { id: 'truck-cargo-bed', label: 'Tailgate / Cargo', repairCode: 'BODY-007', description: '', view: 'rear',
          svgPath: 'M 70 50 L 330 50 L 340 155 L 60 155 Z' },
        { id: 'truck-rear-axle', label: 'Rear Wheels', repairCode: 'TRANS-003', description: '', view: 'rear',
          svgPath: 'M 30 128 m -25 0 a 25 25 0 1 0 50 0 a 25 25 0 1 0 -50 0 M 370 128 m -25 0 a 25 25 0 1 0 50 0 a 25 25 0 1 0 -50 0' },
        { id: 'truck-exhaust', label: 'Exhaust', repairCode: 'EXH-003', description: '', view: 'rear',
          svgPath: 'M 150 158 L 200 158 L 200 175 L 150 175 Z' },
      ],
      right: [
        { id: 'truck-engine', label: 'Engine Bay', repairCode: 'ENG-001', description: '', view: 'right',
          svgPath: 'M 380 60 L 270 50 L 265 145 L 380 148 Z' },
        { id: 'truck-cab', label: 'Cab', repairCode: 'INT-001', description: '', view: 'right',
          svgPath: 'M 265 45 L 175 40 L 175 148 L 265 148 Z' },
        { id: 'truck-cargo-bed', label: 'Cargo Bed', repairCode: 'BODY-007', description: '', view: 'right',
          svgPath: 'M 30 55 L 172 55 L 172 148 L 30 148 Z' },
        { id: 'truck-front-axle', label: 'Front Axle / Wheel', repairCode: 'SUSP-005', description: '', view: 'right',
          svgPath: 'M 330 158 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
        { id: 'truck-rear-axle', label: 'Rear Axle / Wheel', repairCode: 'TRANS-003', description: '', view: 'right',
          svgPath: 'M 72 158 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
      ],
      top: [
        { id: 'truck-engine', label: 'Engine', repairCode: 'ENG-001', description: '', view: 'top',
          svgPath: 'M 85 10 L 315 10 L 315 120 L 85 120 Z' },
        { id: 'truck-cab', label: 'Cab Interior', repairCode: 'INT-001', description: '', view: 'top',
          svgPath: 'M 90 125 L 310 125 L 305 190 L 95 190 Z' },
        { id: 'truck-cargo-bed', label: 'Cargo Bed', repairCode: 'BODY-007', description: '', view: 'top',
          svgPath: 'M 88 195 L 312 195 L 310 285 L 90 285 Z' },
        { id: 'truck-front-axle', label: 'Front-Left Wheel', repairCode: 'SUSP-005', description: '', view: 'top',
          svgPath: 'M 20 22 L 66 22 L 66 92 L 20 92 Z' },
        { id: 'truck-rear-axle', label: 'Rear-Left Wheel', repairCode: 'TRANS-003', description: '', view: 'top',
          svgPath: 'M 20 218 L 66 218 L 66 283 L 20 283 Z' },
      ],
    },
  };
}
