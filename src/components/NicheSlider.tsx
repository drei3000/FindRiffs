type NicheSliderProps = {
  value: number
  onChange: (value: number) => void
  label?: string
}

export default function NicheSlider({
  value,
  onChange,
  label = 'NICHE',
}: NicheSliderProps) {
  return (
    <div className="font-display flex flex-col items-center gap-1">
      <input
        id="niche"
        type="range"
        min={0}
        max={100}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="niche-slider"
        aria-label={label}
        aria-valuetext={`${value} out of 100`}
      />
      <label htmlFor="niche" className="text-sm tracking-wide font-display text-[40px] text-black">
        {value}% {label}
      </label>
    </div>
  )
}