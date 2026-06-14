import {
  Component,
  ElementRef,
  HostListener,
  Optional,
  Self,
} from '@angular/core';
import {
  ControlValueAccessor,
  NgControl,
} from '@angular/forms';
import {
  getRepairCodeEntry,
  REPAIR_CODES,
  RepairCodeEntry,
} from '../../data/repair-codes.data';

interface ComboboxOption {
  code: string;
  label: string;
  category: string;
  isCustom: boolean;
}

interface ComboboxGroup {
  category: string;
  options: ComboboxOption[];
}

@Component({
  selector: 'app-repair-code-combobox',
  templateUrl: './repair-code-combobox.component.html',
  styleUrls: ['./repair-code-combobox.component.css'],
})
export class RepairCodeComboboxComponent implements ControlValueAccessor {
  readonly entries = REPAIR_CODES;

  query = '';
  value = '';
  dropdownOpen = false;
  highlightedIndex = -1;
  disabled = false;

  private visibleOptions: ComboboxOption[] = [];
  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  constructor(
    private host: ElementRef<HTMLElement>,
    @Optional() @Self() public ngControl: NgControl | null,
  ) {
    if (this.ngControl) {
      this.ngControl.valueAccessor = this;
    }
  }

  get selectedEntry(): RepairCodeEntry | undefined {
    return getRepairCodeEntry(this.value);
  }

  get invalid(): boolean {
    return Boolean(this.ngControl?.invalid && this.ngControl?.touched);
  }

  get hasCustomValue(): boolean {
    return Boolean(this.value) && !this.selectedEntry;
  }

  get selectedBadgeLabel(): string {
    if (this.selectedEntry) {
      return `${this.selectedEntry.code} · ${this.selectedEntry.label}`;
    }
    return `Other · ${this.value}`;
  }

  get groupedOptions(): ComboboxGroup[] {
    const searchTerm = this.query.trim().toLowerCase();
    const filteredEntries = this.entries.filter((entry) => this.matchesSearch(entry, searchTerm));
    const groups = new Map<string, ComboboxOption[]>();

    for (const entry of filteredEntries) {
      const option: ComboboxOption = {
        code: entry.code,
        label: entry.label,
        category: entry.category,
        isCustom: false,
      };
      const bucket = groups.get(entry.category) ?? [];
      bucket.push(option);
      groups.set(entry.category, bucket);
    }

    const grouped = Array.from(groups.entries()).map(([category, options]) => ({
      category,
      options,
    }));

    const allowCustom = Boolean(searchTerm) && !this.entries.some((entry) => entry.code.toLowerCase() === searchTerm);
    if (allowCustom) {
      grouped.push({
        category: 'Other / not listed',
        options: [
          {
            code: this.query.trim(),
            label: `Use "${this.query.trim()}" as custom code`,
            category: 'Other / not listed',
            isCustom: true,
          },
        ],
      });
    }

    this.visibleOptions = grouped.flatMap((group) => group.options);
    if (this.highlightedIndex >= this.visibleOptions.length) {
      this.highlightedIndex = this.visibleOptions.length - 1;
    }
    return grouped;
  }

  writeValue(value: string | null): void {
    this.value = (value ?? '').trim();
    this.query = '';
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  onInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.query = input.value;
    this.dropdownOpen = true;
    this.highlightedIndex = this.visibleOptions.length > 0 ? 0 : -1;
    this.onTouched();
  }

  onFocus(): void {
    if (this.disabled) {
      return;
    }
    this.dropdownOpen = true;
  }

  onKeydown(event: KeyboardEvent): void {
    if (this.disabled) {
      return;
    }

    const options = this.visibleOptions;
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.dropdownOpen = true;
        if (options.length > 0) {
          this.highlightedIndex = Math.min(this.highlightedIndex + 1, options.length - 1);
        }
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (options.length > 0) {
          this.highlightedIndex = Math.max(this.highlightedIndex - 1, 0);
        }
        break;
      case 'Enter':
        if (this.dropdownOpen && this.highlightedIndex >= 0 && options[this.highlightedIndex]) {
          event.preventDefault();
          this.selectOption(options[this.highlightedIndex]);
        }
        break;
      case 'Escape':
        event.preventDefault();
        this.closeDropdown();
        break;
      default:
        break;
    }
  }

  selectOption(option: ComboboxOption): void {
    this.value = option.code;
    this.query = '';
    this.dropdownOpen = false;
    this.highlightedIndex = -1;
    this.onChange(option.code);
    this.onTouched();
  }

  clearSelection(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.value = '';
    this.query = '';
    this.highlightedIndex = -1;
    this.dropdownOpen = false;
    this.onChange('');
    this.onTouched();
  }

  isHighlighted(option: ComboboxOption): boolean {
    return this.visibleOptions[this.highlightedIndex]?.code === option.code
      && this.visibleOptions[this.highlightedIndex]?.label === option.label;
  }

  trackByCategory(_: number, group: ComboboxGroup): string {
    return group.category;
  }

  trackByOption(_: number, option: ComboboxOption): string {
    return `${option.category}:${option.code}:${option.label}`;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.host.nativeElement.contains(event.target as Node)) {
      this.closeDropdown();
    }
  }

  private closeDropdown(): void {
    this.dropdownOpen = false;
    this.highlightedIndex = -1;
    this.onTouched();
  }

  private matchesSearch(entry: RepairCodeEntry, searchTerm: string): boolean {
    if (!searchTerm) {
      return true;
    }

    const haystack = [
      entry.code,
      entry.label,
      entry.category,
      ...(entry.keywords ?? []),
      entry.causalPart ?? '',
    ]
      .join(' ')
      .toLowerCase();

    return haystack.includes(searchTerm);
  }
}
