import React, { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';

interface SearchInputProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  suggestions?: string[];
  className?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({ value, onChange, placeholder = 'Search...', suggestions = [], className = '' }) => {
  const [open, setOpen] = useState(false);
  const [filtered, setFiltered] = useState<string[]>([]);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setFiltered(suggestions.filter(s => s.toLowerCase().includes(value.toLowerCase())));
  }, [value, suggestions]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('click', onDoc);
    return () => document.removeEventListener('click', onDoc);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <div style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }}>
        <Search size={16} color="var(--text-tertiary)" />
      </div>
      <input
        type="text"
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        placeholder={placeholder}
        className={`input-field ${className}`}
        onFocus={() => setOpen(true)}
      />

      {open && filtered.length > 0 && (
        <div style={{ position: 'absolute', top: 'calc(100% + 8px)', right: 0, width: '100%', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 8, zIndex: 1200 }}>
          {filtered.slice(0, 6).map((s, idx) => (
            <div key={idx} onClick={() => { onChange(s); setOpen(false); }} style={{ padding: '8px', cursor: 'pointer', borderRadius: 6, color: 'var(--text-primary)' }}>
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchInput;
