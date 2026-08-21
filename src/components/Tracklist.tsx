export type Track = {
  artist: string
  title: string
  youtube: string
  songsterr: string
  cover: string | null
  spotify?: string
  tuning?: string | null
}

export default function TrackList({ tracks }: { tracks: Track[] }) {
  if (tracks.length === 0) return null

  return (
    <div className="flex flex-col gap-3">
      {tracks.map((t, i) => (
        <div
          key={`${i}-${t.artist}-${t.title}`}
          className="flex items-center gap-4 border-2 border-black bg-[#7a1616] p-3"
        >
          <div className="min-w-0 flex-1">
            <p className="font-display truncate text-[32px] leading-tight text-black">{t.title}</p>
            <p className="font-display truncate text-[22px] leading-tight text-black/60">{t.artist}</p>
            <p className="font-display truncate text-[14px] leading-tight tracking-[0.2em] text-black/45">
              {t.tuning ?? 'TUNING UNKNOWN'}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-3 pr-1">
            <a href={t.youtube} target="_blank" rel="noreferrer" title="YouTube" className="opacity-80 hover:opacity-100">
              <img src="https://cdn.simpleicons.org/youtube/000000" alt="YouTube" className="h-9 w-9" />
            </a>
            <a href={t.songsterr} target="_blank" rel="noreferrer" title="Songsterr" className="opacity-80 hover:opacity-100">
              <img src="https://www.google.com/s2/favicons?domain=songsterr.com&sz=64" alt="Songsterr" className="h-9 w-9" />
            </a>
          </div>
        </div>
      ))}
    </div>
  )
}