import type { CampusPhoto } from '../data/campusPhotos'

// A row of captioned campus photos.
export default function CampusGallery({ photos }: { photos: CampusPhoto[] }) {
  return (
    <div className="campus-gallery">
      {photos.map((p) => (
        <figure key={p.src} className="campus-photo">
          <img src={p.src} alt={p.caption} loading="lazy" />
          <figcaption>{p.caption}</figcaption>
        </figure>
      ))}
    </div>
  )
}
