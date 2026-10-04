// Campus photos from Wikimedia Commons (downloaded with approval into public/campus/).
// Credits are shown in the footer, as their licenses require.
export interface CampusPhoto {
  src: string
  caption: string
  credit: string
  license: string
}

export const CAMPUS = {
  harknessAutumn: {
    src: '/campus/campus-harkness-autumn.jpg',
    caption: 'Harkness Tower in the fall',
    credit: 'ajay_suresh',
    license: 'CC BY 2.0',
  },
  oldCampusFall: {
    src: '/campus/campus-old-campus-fall.jpg',
    caption: 'Old Campus in the fall',
    credit: 'Francisco Anzola',
    license: 'CC BY 2.0',
  },
  branfordHarkness: {
    src: '/campus/campus-branford-harkness.jpg',
    caption: 'Branford Court and Harkness Tower',
    credit: 'Namkota',
    license: 'CC BY-SA 4.0',
  },
  oldCampusCourtyard: {
    src: '/campus/campus-old-campus-courtyard.jpg',
    caption: 'The Old Campus courtyard',
    credit: 'Gunnar Klack',
    license: 'CC BY-SA 4.0',
  },
  crossCampusLeaves: {
    src: '/campus/campus-cross-campus-leaves.jpg',
    caption: 'Fall leaves on Cross Campus',
    credit: 'Namkota',
    license: 'CC BY-SA 4.0',
  },
  killingworthSpring: {
    src: '/campus/campus-killingworth-spring.jpg',
    caption: 'Killingworth Court in spring',
    credit: 'Nick Allen',
    license: 'CC BY-SA 3.0',
  },
  sterlingLibrary: {
    src: '/campus/campus-sterling-library.jpg',
    caption: 'Sterling Memorial Library',
    credit: 'Carol M. Highsmith',
    license: 'public domain',
  },
  crossCampusPath: {
    src: '/campus/campus-cross-campus-path.jpg',
    caption: 'A walk across Cross Campus',
    credit: 'Emilie Foyer',
    license: 'CC BY-SA 3.0',
  },
  phelpsGateSpring: {
    src: '/campus/campus-phelps-gate-spring.jpg',
    caption: 'Dogwoods by Phelps Gate',
    credit: 'Adam Jones',
    license: 'CC BY-SA 2.0',
  },
} satisfies Record<string, CampusPhoto>

export const ALL_CAMPUS_PHOTOS: CampusPhoto[] = Object.values(CAMPUS)
