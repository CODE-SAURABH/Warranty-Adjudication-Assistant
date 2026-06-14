import { Component } from '@angular/core';

@Component({
  selector: 'app-header',
  template: `
    <header class="app-header">
      <div class="header-content">
        <div class="brand">
          <div class="brand-icon">
            <!-- Combined brain + scales logo -->
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <!-- Glow background circle -->
              <circle cx="20" cy="20" r="19" fill="url(#bgGrad)" opacity="0.18"/>
              <!-- Scales beam -->
              <line x1="8" y1="26" x2="32" y2="26" stroke="#7dd3fc" stroke-width="1.6" stroke-linecap="round"/>
              <!-- Centre post -->
              <line x1="20" y1="14" x2="20" y2="26" stroke="#7dd3fc" stroke-width="1.6" stroke-linecap="round"/>
              <!-- Left pan arm -->
              <line x1="8" y1="26" x2="12" y2="31" stroke="#7dd3fc" stroke-width="1.4" stroke-linecap="round"/>
              <!-- Right pan arm -->
              <line x1="32" y1="26" x2="28" y2="31" stroke="#7dd3fc" stroke-width="1.4" stroke-linecap="round"/>
              <!-- Left pan -->
              <path d="M9 31 Q12 33.5 15 31" stroke="#38bdf8" stroke-width="1.5" fill="none" stroke-linecap="round"/>
              <!-- Right pan -->
              <path d="M25 31 Q28 33.5 31 31" stroke="#38bdf8" stroke-width="1.5" fill="none" stroke-linecap="round"/>
              <!-- Brain left lobe -->
              <path d="M20 14 C20 14 14 12 12 15 C10 18 11 21 13 22 C14 22.5 15 22 15 22"
                    stroke="#c084fc" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <!-- Brain right lobe -->
              <path d="M20 14 C20 14 26 12 28 15 C30 18 29 21 27 22 C26 22.5 25 22 25 22"
                    stroke="#c084fc" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <!-- Brain centre fold -->
              <line x1="20" y1="13" x2="20" y2="22" stroke="#c084fc" stroke-width="1.2" stroke-linecap="round" stroke-dasharray="1.5 1.5"/>
              <!-- Brain wrinkles left -->
              <path d="M13 17.5 C14.5 16.5 15.5 18.5 14 19.5" stroke="#e879f9" stroke-width="1" fill="none" stroke-linecap="round"/>
              <!-- Brain wrinkles right -->
              <path d="M27 17.5 C25.5 16.5 24.5 18.5 26 19.5" stroke="#e879f9" stroke-width="1" fill="none" stroke-linecap="round"/>
              <!-- Centre top knob -->
              <circle cx="20" cy="12.5" r="1.5" fill="#c084fc"/>
              <defs>
                <linearGradient id="bgGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#c084fc"/>
                  <stop offset="100%" stop-color="#38bdf8"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div class="brand-text">
            <span class="brand-name">KlaimIQ</span>
            <span class="brand-sub">Adjudication Assistant</span>
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
      background: linear-gradient(135deg, #1e3a5f 0%, #2d5a9e 100%);
      color: white;
      padding: 0 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
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
    .brand-icon { font-size: 28px; display: flex; align-items: center; filter: drop-shadow(0 0 6px rgba(192,132,252,0.5)); }
    .brand-text { display: flex; flex-direction: column; line-height: 1.2; }
    .brand-name { font-size: 18px; font-weight: 700; letter-spacing: 0.3px; }
    .brand-sub { font-size: 11px; opacity: 0.75; text-transform: uppercase; letter-spacing: 1px; }
    .nav-links {
      display: flex;
      align-items: center;
      gap: 24px;
    }
    .nav-links a {
      color: rgba(255,255,255,0.85);
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
      padding: 6px 0;
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
    }
    .nav-links a:hover, .nav-links a.active {
      color: white;
      border-bottom-color: #60a5fa;
    }
    .btn-new-claim {
      background: #3b82f6;
      border-radius: 8px;
      padding: 8px 16px !important;
      border-bottom: none !important;
      transition: background 0.2s !important;
    }
    .btn-new-claim:hover {
      background: #2563eb !important;
    }
  `],
})
export class HeaderComponent {}
