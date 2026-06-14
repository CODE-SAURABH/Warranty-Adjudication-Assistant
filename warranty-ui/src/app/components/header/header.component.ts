import { Component } from '@angular/core';

@Component({
  selector: 'app-header',
  template: `
    <header class="app-header">
      <div class="header-content">
        <div class="brand">
          <div class="brand-icon">
            <img src="/assets/favicon.svg" height="44" alt="KlaimIQ logo" style="display:block;width:auto;">
          </div>
          <div class="brand-text">
            <span class="brand-name">KlaimIQ</span>
            <span class="brand-sub">KPIT Warranty Assistant</span>
          </div>
        </div>
        <nav class="nav-links">
          <a routerLink="/dashboard" routerLinkActive="active">Dashboard</a>
          <a routerLink="/claims/new" routerLinkActive="active" class="btn-new-claim">
            + New Claim
          </a>
        </nav>
      </div>
    </header>
  `,
  styles: [`
    .app-header {
      background: linear-gradient(135deg, #0076A8 0%, #0096D6 100%);
      color: white;
      padding: 0 24px;
      box-shadow: 0 2px 10px rgba(0,118,168,0.25);
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-content {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 64px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: inherit;
    }
    .brand-icon { font-size: 28px; display: flex; align-items: center; }
    .brand-text { display: flex; flex-direction: column; line-height: 1.2; }
    .brand-name { font-size: 18px; font-weight: 700; letter-spacing: 0.3px; }
    .brand-sub { font-size: 11px; opacity: 0.80; text-transform: uppercase; letter-spacing: 1px; }
    .nav-links {
      display: flex;
      align-items: center;
      gap: 24px;
    }
    .nav-links a {
      color: rgba(255,255,255,0.88);
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
      padding: 6px 0;
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
    }
    .nav-links a:hover, .nav-links a.active {
      color: white;
      border-bottom-color: #7AC943;
    }
    .btn-new-claim {
      background: #7AC943;
      color: #1a3a00;
      border-radius: 8px;
      padding: 8px 16px !important;
      border-bottom: none !important;
      font-weight: 700 !important;
      transition: background 0.2s !important;
    }
    .btn-new-claim:hover {
      background: #5fa32e !important;
      color: white !important;
    }
  `],
})
export class HeaderComponent {}
