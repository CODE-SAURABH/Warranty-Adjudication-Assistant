import {
  Component,
  Output,
  EventEmitter,
  HostListener,
  ElementRef,
} from '@angular/core';
import { VehicleType, VehicleView, VehicleZone, SelectedZone } from '../../models/claim.model';

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

@Component({
  selector: 'app-vehicle-zone-selector',
  templateUrl: './vehicle-zone-selector.component.html',
  styleUrls: ['./vehicle-zone-selector.component.css'],
})
export class VehicleZoneSelectorComponent {
  @Output() zoneSelected = new EventEmitter<SelectedZone>();

  vehicleType: VehicleType = 'car';
  activeView: VehicleView = 'left';
  hoveredZone: string | null = null;
  selectedZones: Set<string> = new Set();
  popup: ZonePopup | null = null;

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
      { repairCode: 'ENG-001', label: 'Oil Leak', description: 'Engine oil leak detected from gasket or seal area.' },
      { repairCode: 'ENG-002', label: 'Overheating', description: 'Engine temperature exceeds normal operating range.' },
      { repairCode: 'ENG-003', label: 'Misfiring / Rough Idle', description: 'Engine misfiring or rough idle condition.' },
    ],
    'car-hood': [
      { repairCode: 'ENG-001', label: 'Hood Latch Failure', description: 'Hood latch does not engage or disengage properly.' },
      { repairCode: 'BODY-001', label: 'Hood Panel Damage', description: 'Hood panel shows signs of deformation or misalignment.' },
    ],
    'car-front-bumper': [
      { repairCode: 'BODY-001', label: 'Bumper Damage', description: 'Front bumper shows cracking, deformation, or misalignment.' },
      { repairCode: 'ELEC-003', label: 'Parking Sensor Failure', description: 'Front parking sensors not detecting obstacles.' },
    ],
    'car-front-lights': [
      { repairCode: 'ELEC-004', label: 'Headlight Failure', description: 'One or more headlight units not functioning.' },
      { repairCode: 'ELEC-005', label: 'DRL Malfunction', description: 'Daytime running lights not operating correctly.' },
    ],
    'car-windshield': [
      { repairCode: 'BODY-002', label: 'Windshield Crack', description: 'Windshield crack or chip affecting driver visibility.' },
      { repairCode: 'ELEC-006', label: 'Wiper Motor Failure', description: 'Windshield wipers not operating at correct speed or not at all.' },
    ],
    'car-roof': [
      { repairCode: 'BODY-003', label: 'Roof Panel Issue', description: 'Roof panel shows dents, rust, or water ingress.' },
      { repairCode: 'AC-001', label: 'Sunroof Malfunction', description: 'Sunroof does not open/close or seals are leaking.' },
    ],
    'car-door-fl': [
      { repairCode: 'BODY-004', label: 'Door Latch/Lock', description: 'Front left door latch or lock mechanism failure.' },
      { repairCode: 'ELEC-007', label: 'Power Window Failure', description: 'Front left power window motor or regulator failed.' },
      { repairCode: 'BODY-005', label: 'Door Seal Leak', description: 'Door weather seal allows water or wind ingress.' },
    ],
    'car-door-rl': [
      { repairCode: 'BODY-004', label: 'Door Latch/Lock', description: 'Rear left door latch or lock mechanism failure.' },
      { repairCode: 'ELEC-007', label: 'Power Window Failure', description: 'Rear left power window motor or regulator failed.' },
      { repairCode: 'BODY-005', label: 'Door Seal Leak', description: 'Door weather seal allows water or wind ingress.' },
    ],
    'car-door-fr': [
      { repairCode: 'BODY-004', label: 'Door Latch/Lock', description: 'Front right door latch or lock mechanism failure.' },
      { repairCode: 'ELEC-007', label: 'Power Window Failure', description: 'Front right power window motor or regulator failed.' },
    ],
    'car-door-rr': [
      { repairCode: 'BODY-004', label: 'Door Latch/Lock', description: 'Rear right door latch or lock mechanism failure.' },
      { repairCode: 'ELEC-007', label: 'Power Window Failure', description: 'Rear right power window motor or regulator failed.' },
    ],
    'car-wheel-fl': [
      { repairCode: 'BRKS-001', label: 'Brake ABS Malfunction', description: 'ABS warning on front left wheel speed sensor.' },
      { repairCode: 'SUSP-001', label: 'Suspension / Strut', description: 'Front left strut or control arm worn or damaged.' },
      { repairCode: 'TIRE-001', label: 'Tire / Rim Damage', description: 'Tire pressure loss or rim deformation on front left.' },
    ],
    'car-wheel-rl': [
      { repairCode: 'BRKS-001', label: 'Brake ABS Malfunction', description: 'ABS warning on rear left wheel speed sensor.' },
      { repairCode: 'SUSP-002', label: 'Rear Suspension', description: 'Rear left shock absorber or spring issue.' },
      { repairCode: 'TIRE-001', label: 'Tire / Rim Damage', description: 'Tire pressure loss or rim deformation on rear left.' },
    ],
    'car-wheel-fr': [
      { repairCode: 'BRKS-001', label: 'Brake ABS Malfunction', description: 'ABS warning on front right wheel speed sensor.' },
      { repairCode: 'SUSP-001', label: 'Suspension / Strut', description: 'Front right strut or control arm worn or damaged.' },
      { repairCode: 'TIRE-001', label: 'Tire / Rim Damage', description: 'Tire pressure loss or rim deformation on front right.' },
    ],
    'car-wheel-rr': [
      { repairCode: 'BRKS-001', label: 'Brake ABS Malfunction', description: 'ABS warning on rear right wheel speed sensor.' },
      { repairCode: 'SUSP-002', label: 'Rear Suspension', description: 'Rear right shock absorber or spring issue.' },
      { repairCode: 'TIRE-001', label: 'Tire / Rim Damage', description: 'Tire pressure loss or rim deformation on rear right.' },
    ],
    'car-transmission': [
      { repairCode: 'TRANS-001', label: 'Transmission Slipping', description: 'Transmission slips between gears under load.' },
      { repairCode: 'TRANS-002', label: 'No Shift / Hard Shift', description: 'Transmission fails to shift or shifts harshly.' },
    ],
    'car-exhaust': [
      { repairCode: 'EXH-001', label: 'Exhaust Leak', description: 'Exhaust gases leaking from manifold, pipe, or joint.' },
      { repairCode: 'EXH-002', label: 'Catalytic Converter', description: 'Catalytic converter efficiency below threshold.' },
    ],
    'car-rear-bumper': [
      { repairCode: 'BODY-001', label: 'Bumper Damage', description: 'Rear bumper shows cracking or misalignment.' },
      { repairCode: 'ELEC-003', label: 'Rear Sensor Failure', description: 'Rear parking sensors not functioning.' },
    ],
    'car-trunk': [
      { repairCode: 'BODY-006', label: 'Trunk Latch Failure', description: 'Trunk lid does not latch or release properly.' },
      { repairCode: 'ELEC-008', label: 'Power Tailgate Issue', description: 'Power trunk/tailgate motor or sensor failed.' },
    ],
    'car-rear-lights': [
      { repairCode: 'ELEC-009', label: 'Tail Light Failure', description: 'Tail light, brake light, or reverse light not working.' },
    ],
    'car-battery': [
      { repairCode: 'ELEC-001', label: 'Battery Drain', description: 'Battery discharges unexpectedly overnight or within hours.' },
      { repairCode: 'ELEC-002', label: 'Alternator Failure', description: 'Alternator not charging battery while engine running.' },
    ],
    'car-ac': [
      { repairCode: 'AC-001', label: 'A/C Compressor Failure', description: 'Air conditioning compressor not engaging or blowing warm.' },
      { repairCode: 'AC-002', label: 'Refrigerant Leak', description: 'A/C system refrigerant level low due to leak.' },
    ],
    'car-interior': [
      { repairCode: 'INT-001', label: 'Dashboard Warning Light', description: 'Persistent warning light on instrument cluster.' },
      { repairCode: 'INT-002', label: 'Infotainment Failure', description: 'Head unit / display screen not responding or blank.' },
      { repairCode: 'ELEC-010', label: 'Airbag System Fault', description: 'Airbag warning light on or SRS fault code present.' },
    ],
    // --- BIKE ZONES ---
    'bike-engine': [
      { repairCode: 'ENG-001', label: 'Engine Oil Leak', description: 'Engine oil leaking from gasket or case seam.' },
      { repairCode: 'ENG-003', label: 'Misfiring / No Start', description: 'Engine misfires or fails to start.' },
    ],
    'bike-front-wheel': [
      { repairCode: 'BRKS-002', label: 'Front Brake Fade', description: 'Front brake pad worn or caliper seized.' },
      { repairCode: 'SUSP-003', label: 'Fork Seal Leak', description: 'Front fork seals leaking oil.' },
      { repairCode: 'TIRE-001', label: 'Tire Damage', description: 'Front tire puncture or sidewall damage.' },
    ],
    'bike-rear-wheel': [
      { repairCode: 'BRKS-003', label: 'Rear Brake Issue', description: 'Rear brake pad worn or drum issue.' },
      { repairCode: 'SUSP-004', label: 'Rear Shock Failure', description: 'Rear shock absorber leaking or collapsed.' },
      { repairCode: 'TIRE-001', label: 'Tire Damage', description: 'Rear tire puncture or excessive wear.' },
    ],
    'bike-fuel-tank': [
      { repairCode: 'FUEL-001', label: 'Fuel Leak', description: 'Fuel tank or fuel line leaking.' },
      { repairCode: 'FUEL-002', label: 'Fuel Gauge Failure', description: 'Fuel gauge reads inaccurately or not at all.' },
    ],
    'bike-exhaust': [
      { repairCode: 'EXH-001', label: 'Exhaust Leak', description: 'Header pipe or muffler leaking exhaust gases.' },
    ],
    'bike-handlebars': [
      { repairCode: 'ELEC-011', label: 'Switch Gear Failure', description: 'Handlebar switches (turn signal, horn, starter) not working.' },
      { repairCode: 'SUSP-003', label: 'Steering Bearing', description: 'Steering head bearings worn causing handlebar play.' },
    ],
    'bike-lights': [
      { repairCode: 'ELEC-004', label: 'Headlight Failure', description: 'Headlight bulb or unit not functioning.' },
      { repairCode: 'ELEC-009', label: 'Turn Signal Failure', description: 'Turn signal indicators not flashing or dead.' },
    ],
    // --- TRUCK ZONES ---
    'truck-engine': [
      { repairCode: 'ENG-001', label: 'Oil Leak', description: 'Heavy-duty engine oil leaking from seals.' },
      { repairCode: 'ENG-002', label: 'Overheating', description: 'Engine overheating under load or highway.' },
    ],
    'truck-front-axle': [
      { repairCode: 'SUSP-005', label: 'Front Axle / Hub', description: 'Front axle hub bearing worn or damaged.' },
      { repairCode: 'BRKS-004', label: 'Air Brake Issue', description: 'Air brake system pressure drop or valve failure.' },
    ],
    'truck-rear-axle': [
      { repairCode: 'TRANS-003', label: 'Differential Failure', description: 'Rear differential noise or fluid leak.' },
      { repairCode: 'BRKS-004', label: 'Air Brake Issue', description: 'Rear air brake system failure.' },
    ],
    'truck-cab': [
      { repairCode: 'INT-001', label: 'Dashboard Warning', description: 'Instrument cluster warning light active.' },
      { repairCode: 'AC-001', label: 'A/C Failure', description: 'Cab air conditioning not cooling.' },
    ],
    'truck-cargo-bed': [
      { repairCode: 'BODY-007', label: 'Bed Liner Damage', description: 'Cargo bed liner cracked or delaminating.' },
      { repairCode: 'ELEC-008', label: 'Tailgate Actuator', description: 'Power tailgate or tonneau cover motor failed.' },
    ],
    'truck-exhaust': [
      { repairCode: 'EXH-003', label: 'DPF / EGR Issue', description: 'Diesel particulate filter or EGR valve fault.' },
      { repairCode: 'EXH-001', label: 'Exhaust Leak', description: 'Exhaust manifold or turbo downpipe leaking.' },
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
    const svgRect = svgEl.getBoundingClientRect();
    const containerRect = (svgEl.parentElement as HTMLElement).getBoundingClientRect();

    const popupX = (event.clientX - containerRect.left);
    const popupY = (event.clientY - containerRect.top);

    this.popup = {
      zoneId: zone.id,
      zoneLabel: zone.label,
      x: Math.min(popupX, containerRect.width - 280),
      y: Math.min(popupY + 12, containerRect.height - 200),
      issues: this.getIssuesForZone(zone.id),
    };
  }

  selectIssue(issue: ZoneIssue): void {
    if (!this.popup) return;
    const zoneId = this.popup.zoneId;
    const zoneLabel = this.popup.zoneLabel;
    this.selectedZones.add(zoneId);
    this.zoneSelected.emit({
      zoneId,
      label: zoneLabel,
      repairCode: issue.repairCode,
      defaultDescription: issue.description,
    });
    this.popup = null;
  }

  closePopup(): void {
    this.popup = null;
  }

  @HostListener('document:keydown.escape')
  onEsc(): void {
    this.popup = null;
  }

  setVehicleType(type: VehicleType): void {
    this.vehicleType = type;
    this.activeView = 'left';
    this.selectedZones.clear();
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

  // ─── SVG Zone Definitions ─────────────────────────────────────────────────
  readonly svgZones: Record<string, Partial<Record<VehicleView, VehicleZone[]>>> = {
    car: {
      left: [
        { id: 'car-wheel-fl', label: 'Front Wheel', repairCode: 'SUSP-001', description: '', view: 'left',
          svgPath: 'M 62 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-wheel-rl', label: 'Rear Wheel', repairCode: 'SUSP-002', description: '', view: 'left',
          svgPath: 'M 338 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-engine', label: 'Engine Bay', repairCode: 'ENG-001', description: '', view: 'left',
          svgPath: 'M 24 80 L 110 60 L 130 100 L 24 110 Z' },
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
          svgPath: 'M 62 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-wheel-rr', label: 'Rear Wheel', repairCode: 'SUSP-002', description: '', view: 'right',
          svgPath: 'M 338 158 m -28 0 a 28 28 0 1 0 56 0 a 28 28 0 1 0 -56 0' },
        { id: 'car-engine', label: 'Engine Bay', repairCode: 'ENG-001', description: '', view: 'right',
          svgPath: 'M 24 80 L 110 60 L 130 100 L 24 110 Z' },
        { id: 'car-door-fr', label: 'Front Door', repairCode: 'BODY-004', description: '', view: 'right',
          svgPath: 'M 140 68 L 220 65 L 220 148 L 140 148 Z' },
        { id: 'car-door-rr', label: 'Rear Door', repairCode: 'BODY-004', description: '', view: 'right',
          svgPath: 'M 222 65 L 305 68 L 305 148 L 222 148 Z' },
        { id: 'car-windshield', label: 'Windshield', repairCode: 'BODY-002', description: '', view: 'right',
          svgPath: 'M 108 62 L 140 48 L 140 100 L 108 108 Z' },
        { id: 'car-roof', label: 'Roof', repairCode: 'BODY-003', description: '', view: 'right',
          svgPath: 'M 140 45 L 270 45 L 270 62 L 140 62 Z' },
        { id: 'car-trunk', label: 'Trunk', repairCode: 'BODY-006', description: '', view: 'right',
          svgPath: 'M 305 65 L 360 78 L 360 148 L 305 148 Z' },
      ],
      front: [
        { id: 'car-front-bumper', label: 'Front Bumper', repairCode: 'BODY-001', description: '', view: 'front',
          svgPath: 'M 60 155 L 340 155 L 350 180 L 50 180 Z' },
        { id: 'car-front-lights', label: 'Headlights', repairCode: 'ELEC-004', description: '', view: 'front',
          svgPath: 'M 60 100 L 140 95 L 145 140 L 60 145 Z M 260 95 L 340 100 L 340 145 L 255 140 Z' },
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
          svgPath: 'M 60 100 L 140 95 L 145 155 L 60 155 Z M 260 95 L 340 100 L 340 155 L 255 155 Z' },
        { id: 'car-trunk', label: 'Trunk Lid', repairCode: 'BODY-006', description: '', view: 'rear',
          svgPath: 'M 80 50 L 320 50 L 340 100 L 60 100 Z' },
        { id: 'car-windshield', label: 'Rear Window', repairCode: 'BODY-002', description: '', view: 'rear',
          svgPath: 'M 110 25 L 290 25 L 300 50 L 100 50 Z' },
        { id: 'car-exhaust', label: 'Exhaust Pipe(s)', repairCode: 'EXH-001', description: '', view: 'rear',
          svgPath: 'M 150 165 L 200 165 L 200 180 L 150 180 Z M 220 165 L 260 165 L 260 180 L 220 180 Z' },
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
          svgPath: 'M 200 130 m -60 0 a 60 60 0 1 0 120 0 a 60 60 0 1 0 -120 0' },
        { id: 'bike-handlebars', label: 'Handlebars', repairCode: 'ELEC-011', description: '', view: 'front',
          svgPath: 'M 80 60 L 320 60 L 320 80 L 80 80 Z' },
        { id: 'bike-lights', label: 'Headlight', repairCode: 'ELEC-004', description: '', view: 'front',
          svgPath: 'M 160 25 L 240 25 L 240 60 L 160 60 Z' },
      ],
      rear: [
        { id: 'bike-rear-wheel', label: 'Rear Wheel', repairCode: 'BRKS-003', description: '', view: 'rear',
          svgPath: 'M 200 130 m -60 0 a 60 60 0 1 0 120 0 a 60 60 0 1 0 -120 0' },
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
          svgPath: 'M 72 150 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
        { id: 'truck-rear-axle', label: 'Rear Axle / Wheel', repairCode: 'TRANS-003', description: '', view: 'left',
          svgPath: 'M 330 150 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
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
          svgPath: 'M 20 60 L 130 50 L 135 145 L 20 148 Z' },
        { id: 'truck-cab', label: 'Cab', repairCode: 'INT-001', description: '', view: 'right',
          svgPath: 'M 135 45 L 225 40 L 225 148 L 135 148 Z' },
        { id: 'truck-cargo-bed', label: 'Cargo Bed', repairCode: 'BODY-007', description: '', view: 'right',
          svgPath: 'M 228 55 L 370 55 L 370 148 L 228 148 Z' },
        { id: 'truck-front-axle', label: 'Front Axle / Wheel', repairCode: 'SUSP-005', description: '', view: 'right',
          svgPath: 'M 72 150 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
        { id: 'truck-rear-axle', label: 'Rear Axle / Wheel', repairCode: 'TRANS-003', description: '', view: 'right',
          svgPath: 'M 330 150 m -32 0 a 32 32 0 1 0 64 0 a 32 32 0 1 0 -64 0' },
      ],
      top: [
        { id: 'truck-engine', label: 'Engine', repairCode: 'ENG-001', description: '', view: 'top',
          svgPath: 'M 85 10 L 315 10 L 315 120 L 85 120 Z' },
        { id: 'truck-cab', label: 'Cab Interior', repairCode: 'INT-001', description: '', view: 'top',
          svgPath: 'M 90 125 L 310 125 L 305 190 L 95 190 Z' },
        { id: 'truck-cargo-bed', label: 'Cargo Bed', repairCode: 'BODY-007', description: '', view: 'top',
          svgPath: 'M 88 195 L 312 195 L 310 285 L 90 285 Z' },
        { id: 'truck-front-axle', label: 'Front-Left Wheel', repairCode: 'SUSP-005', description: '', view: 'top',
          svgPath: 'M 20 20 L 80 20 L 80 90 L 20 90 Z' },
        { id: 'truck-rear-axle', label: 'Rear-Left Wheel', repairCode: 'TRANS-003', description: '', view: 'top',
          svgPath: 'M 20 215 L 80 215 L 80 280 L 20 280 Z' },
      ],
    },
  };
}
