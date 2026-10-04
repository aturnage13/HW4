// Handsome Dan, the original Yale bulldog (1889 photo, public domain, Wikimedia
// Commons), from public/brand/handsome-dan.jpg.
const PHOTO = '/brand/handsome-dan.jpg'

// Round crop of Dan's face, used as the chat assistant's avatar.
export function DanAvatar({ size = 40 }: { size?: number }) {
  return (
    <span
      className="dan-avatar"
      role="img"
      aria-label="Handsome Dan"
      style={{ width: size, height: size, backgroundImage: `url(${PHOTO})` }}
    />
  )
}

interface DanSaysProps {
  message: string
  mood?: 'sorry' | 'found'
  compact?: boolean
}

// Dan with a speech bubble: apologizing when we don't have something,
// cheering when a search finds matches.
export function DanSays({ message, mood = 'sorry', compact = false }: DanSaysProps) {
  const classes = ['sorry-dan', mood === 'found' ? 'found' : '', compact ? 'compact' : ''].join(' ')
  const alt = mood === 'found' ? 'Handsome Dan the bulldog, pleased with himself' : 'Handsome Dan the bulldog looking sorry'
  return (
    <div className={classes}>
      <img src={PHOTO} alt={alt} className="sorry-dan-photo" />
      <p className="speech-bubble">{message}</p>
    </div>
  )
}

export function SorryDan(props: Omit<DanSaysProps, 'mood'>) {
  return <DanSays {...props} mood="sorry" />
}
