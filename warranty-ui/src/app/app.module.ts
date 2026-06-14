import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HeaderComponent } from './components/header/header.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ClaimFormComponent } from './components/claim-form/claim-form.component';
import { ClaimDetailComponent } from './components/claim-detail/claim-detail.component';
import { DispositionBadgeComponent } from './components/disposition-badge/disposition-badge.component';
import { RepairCodeComboboxComponent } from './components/repair-code-combobox/repair-code-combobox.component';
import { VehicleZoneSelectorComponent } from './components/vehicle-zone-selector/vehicle-zone-selector.component';

@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    DashboardComponent,
    ClaimFormComponent,
    ClaimDetailComponent,
    DispositionBadgeComponent,
    RepairCodeComboboxComponent,
    VehicleZoneSelectorComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    ReactiveFormsModule,
    FormsModule,
  ],
  providers: [],
  bootstrap: [AppComponent],
})
export class AppModule {}
