import { useState, useRef, useEffect, useMemo } from 'react'

export type Option = string | { value: string; label: string }

type SearchableDropdownProps = {
  label: string
  options: Option[]
  value: string | null
  onChange: (v: string) => void
}

const toOption = (o: Option) =>
  typeof o === 'string' ? { value: o, label: o } : o

/** Lowercase and drop whitespace so 'drop c' matches 'Drop C' and
 *  'c g c f a d' matches 'CGCFAD'. Needle and haystack both go through it. */
const fold = (s: string) => s.toLowerCase().replace(/\s+/g, '')

/** Shared by the closed button and the open input so the frame never shifts */
const TRIGGER =
  `flex w-full items-center justify-between border-2 border-black
   bg-[#7a1616] px-6 py-4 text-left font-display text-[32px] text-black`

export default function SearchableDropdown({
  label,
  options,
  value,
  onChange,
}: SearchableDropdownProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [highlight, setHighlight] = useState(0)

  const ref = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const items = useMemo(() => options.map(toOption), [options])
  const selected = items.find(o => o.value === value) ?? null

  const filtered = useMemo(() => {
    const q = fold(query)
    if (!q) return items
    return items.filter(o => fold(o.label).includes(q) || fold(o.value).includes(q))
  }, [items, query])

  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  // Fresh query each time it opens, cursor straight into the trigger
  useEffect(() => {
    if (!open) {
      setQuery('')
      return
    }
    const i = items.findIndex(o => o.value === value)
    setHighlight(Math.max(0, i))
    inputRef.current?.focus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  // Keep the highlighted row on screen while arrowing through a long list
  useEffect(() => {
    if (!open) return
    const row = listRef.current?.children[highlight] as HTMLElement | undefined
    row?.scrollIntoView({ block: 'nearest' })
  }, [highlight, open])

  function commit(next: string) {
    onChange(next)
    setOpen(false)
  }

  function onSearchKeyDown(e: React.KeyboardEvent) {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlight(h => Math.min(h + 1, filtered.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlight(h => Math.max(h - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (filtered[highlight]) commit(filtered[highlight].value)
        break
      case 'Tab':
        setOpen(false)
        break
    }
  }

  return (
    <div ref={ref} className="relative">
      {open ? (
        <div className={TRIGGER}>
          <input
            ref={inputRef}
            value={query}
            onChange={e => {
              setQuery(e.target.value)
              setHighlight(0)
            }}
            onKeyDown={onSearchKeyDown}
            placeholder={selected?.label ?? label}
            className="w-full min-w-0 bg-transparent font-display text-[32px]
                       text-black placeholder:text-black/40 focus:outline-none"
          />
          <button
            onClick={() => setOpen(false)}
            aria-label="Close"
            className="shrink-0 pl-4 text-[20px] rotate-180"
          >
            ▾
          </button>
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          aria-expanded={false}
          className={`${TRIGGER} hover:bg-[#8f1a1a]`}
        >
          <span>{selected?.label ?? label}</span>
          <span className="text-[20px]">▾</span>
        </button>
      )}

      {open && (
        <div className="absolute left-0 right-0 z-30 max-h-64 overflow-y-auto
                        border-2 border-t-0 border-black bg-[#7a1616]">
          <div ref={listRef}>
            {filtered.length === 0 && (
              <p className="px-6 py-3 font-display text-[24px] text-black/40">
                No matches
              </p>
            )}

            {filtered.map((opt, i) => (
              <button
                key={opt.value}
                onMouseEnter={() => setHighlight(i)}
                onMouseDown={e => e.preventDefault()}
                onClick={() => commit(opt.value)}
                className={`block w-full px-6 py-3 text-left font-display text-[24px]
                            text-black hover:bg-[#a01e1e]
                            ${i === highlight ? 'bg-[#a01e1e]' : ''}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}