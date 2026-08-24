import { useMemo, useRef, useState } from 'react'
import Background from './components/Background'
import Layout from './components/Layout'
import SearchableDropdown, { type Option } from './components/Dropdown'
import NicheSlider from './components/NicheSlider'
import SearchButton from './components/SearchButton'
import TrackList, { type Track } from './components/Tracklist'

const ANY_TUNING = 'No Selection'
const API_BASE = import.meta.env.VITE_API_URL ?? ''

const GENRES: Option[] = [
  'Metalcore',
  'Melodic Metalcore',
  'Progressive Metalcore',
  'Deathcore',
  'Mathcore',
  'Nu Metalcore',
  'Easycore',

  'Death Metal',
  'Melodic Death Metal',
  'Technical Death Metal',
  'Brutal Death Metal',
  'Black Metal',
  'Blackgaze',
  'Grindcore',
  'Thrash Metal',
  'Crossover Thrash',
  'Speed Metal',
 
  'Doom Metal',
  'Sludge Metal',
  'Stoner Metal',
  'Post-Metal',
  'Groove Metal',
  'Djent',

 
  'Metal',
  'Heavy Metal',
  'Progressive Metal',
  'Power Metal',
  'Symphonic Metal',
  'Folk Metal',
  'Gothic Metal',
  'Industrial Metal',
  'Alternative Metal',
  'Nu Metal',
  'Funk Metal',
 
  'Hardcore',
  'Hardcore Punk',
  'Melodic Hardcore',
  'Beatdown Hardcore',
  'Powerviolence',
  'Post-Hardcore',
  'Screamo',
  'Punk',
  'Punk Rock',
  'Skate Punk',
  'Pop Punk',

  'Emo',
  'Midwest Emo',
  'Grunge',
  'Hard Rock',
  'Alternative Rock',
  'Math Rock',
  'Post-Rock',
  'Shoegaze',
  'Indie Rock',
  'Blues Rock',
  'Classic Rock',
]

/** Sharps only — Songsterr note names normalise to sharps, so 'Eb standard'
 *  has to be stored as D#G#C#F#A#D# or it will never match. */
const TUNINGS: Option[] = [
  { value: ANY_TUNING, label: ANY_TUNING },

  { value: 'EADGBE', label: 'E Standard' },
  { value: 'D#G#C#F#A#D#', label: 'Eb Standard' },
  { value: 'DGCFAD', label: 'D Standard' },
  { value: 'C#F#BEG#C#', label: 'C# Standard' },
  { value: 'CFA#D#GC', label: 'C Standard' },
  { value: 'BEADF#B', label: 'B Standard' },

  { value: 'DADGBE', label: 'Drop D' },
  { value: 'C#G#C#F#A#D#', label: 'Drop C#' },
  { value: 'CGCFAD', label: 'Drop C' },
  { value: 'BF#BEG#C#', label: 'Drop B' },
  { value: 'A#FA#D#GC', label: 'Drop A#' },
  { value: 'AEADF#B', label: 'Drop A' },

  { value: 'BEADGBE', label: '7-string B Standard' },
  { value: 'A#D#G#C#F#A#D#', label: '7-string A# Standard' },
  { value: 'ADGCFAD', label: '7-string A Standard' },
  { value: 'GCFA#D#GC', label: '7-string G Standard' },
  { value: 'AEADGBE', label: '7-string Drop A' },
  { value: 'G#D#G#C#F#A#D#', label: '7-string Drop G#' },
  { value: 'GDGCFAD', label: '7-string Drop G' },
  { value: 'FCFA#D#GC', label: '7-string Drop F' },

  { value: 'F#BEADGBE', label: '8-string F# Standard' },
  { value: 'FA#D#G#C#F#A#D#', label: '8-string F Standard' },
  { value: 'EADGCFAD', label: '8-string E Standard' },
  { value: 'EBEADGBE', label: '8-string Drop E' },
  { value: 'D#A#D#G#C#F#A#D#', label: '8-string Drop D#' },
  { value: 'DADGCFAD', label: '8-string Drop D' },

  { value: 'DADGAD', label: 'DADGAD' },
  { value: 'DADGBD', label: 'Double Drop D' },
  { value: 'DADF#AD', label: 'Open D' },
  { value: 'DGDGBD', label: 'Open G' },
  { value: 'CGCGCE', label: 'Open C' },
  { value: 'EBEG#BE', label: 'Open E' },
  { value: 'EAEAC#E', label: 'Open A' },
]

/** 'E A D G B E' -> 'EADGBE', so display strings compare cleanly */
const normalise = (t?: string | null) => (t ?? '').replace(/\s+/g, '').toUpperCase()

/** Readable name for the empty-state copy, so it reads 'in Drop C' */
const tuningLabel = (v: string | null) => {
  const hit = TUNINGS.find(o => typeof o !== 'string' && o.value === v)
  return hit && typeof hit !== 'string' ? hit.label : (v ?? '')
}

function App() {
  const [genre, setGenre] = useState<string | null>(null)
  const [tuning, setTuning] = useState<string | null>(ANY_TUNING)
  const [niche, setNiche] = useState(0)
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [allTracks, setAllTracks] = useState<Track[]>([])
  const abortRef = useRef<AbortController | null>(null)

  // Everything the search found stays in allTracks. Changing the tuning
  // dropdown just re-derives this list — no refetch.
  const visibleTracks = useMemo(() => {
    if (!tuning || tuning === ANY_TUNING) return allTracks
    const want = normalise(tuning)
    return allTracks.filter(t => normalise(t.tuning) === want)
  }, [allTracks, tuning])

  async function handleSearch() {
    if (!genre) return

    // Cancel an in-flight search so results can't interleave
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setHasSearched(true)
    setAllTracks([])

    const params = new URLSearchParams({
      tag: genre.toLowerCase(),
      nicheness: String(niche),
    })

    try {
      const res = await fetch(`${API_BASE}/api/tracks?${params.toString()}`, {
        signal: controller.signal,
      })

      if (!res.ok || !res.body) {
        const body = await res.json().catch(() => ({ error: res.statusText }))
        console.error(body.error)
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      for (;;) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Keep the trailing fragment, it's an incomplete line
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.trim()) continue

          let msg: { type: string } & Partial<Track>
          try {
            msg = JSON.parse(line)
          } catch {
            continue
          }

          if (msg.type === 'track') {
            setAllTracks(prev => [...prev, msg as Track])
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') console.error(err)
    } finally {
      if (abortRef.current === controller) setLoading(false)
    }
  }

   

  return (
    <>
      <Background />
      <Layout>
        <div className="flex flex-col gap-6 px-8 pt-8">
          <SearchableDropdown
            label="Genre"
            options={GENRES}
            value={genre}
            onChange={setGenre}
           />
          <SearchableDropdown
            label="Tuning"
            options={TUNINGS}
            value={tuning}
            onChange={setTuning}
           />
          <NicheSlider value={niche} onChange={setNiche} />
          <SearchButton
            onClick={handleSearch}
            disabled={!genre}
            loading={loading}
          />

  

          {!loading && hasSearched && allTracks.length > 0 && visibleTracks.length === 0 && (
            <p className="font-display text-center text-[20px] tracking-wide text-black/60">
              None of these {allTracks.length} tracks are in {tuningLabel(tuning)}. Pick another
              tuning or move the niche slider.
            </p>
          )}

          {!loading && hasSearched && allTracks.length === 0 && (
            <p className="font-display text-center text-[20px] tracking-wide text-black/60">
              Nothing came back for {genre}. Try a different genre.
            </p>
          )}

          <TrackList tracks={visibleTracks} />
        </div>
      </Layout>
    </>
  )
}

export default App