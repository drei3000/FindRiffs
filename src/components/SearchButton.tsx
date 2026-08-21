type SearchButtonProps = {
  onClick: () => void
  disabled?: boolean
  loading?: boolean
}

export default function SearchButton({
  onClick,
  disabled = false,
  loading = false,
}: SearchButtonProps) {
  const isBlocked = disabled || loading

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isBlocked}
      className="font-display w-full cursor-pointer bg-black
                 px-6 py-4 text-3xl tracking-[0.25em] text-red-900
                 hover:bg-[#1A1A1A]
                 focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-[#F2E3C6]
                 disabled:cursor-not-allowed disabled:bg-black/50"
    >
      {loading ? 'SEARCHING' : 'SEARCH'}
    </button>
  )
}