// Handsome Dan's one-liners for the "we don't have it" and "found it" screens.
// One is picked at random each time a new result or missing page is shown.

export const CANT_FIND_SAYINGS = [
  "Sorry, I was busy beating Harvard and couldn't find what you needed!",
  'I sniffed every residential college twice. Came up empty-pawed!',
  'I chased this one from Old Campus to Science Hill. No luck!',
  "Even Sterling Library's stacks couldn't turn this one up. Sorry!",
  "I howled for it from the top of Harkness Tower, but nobody answered.",
  'I checked under every table at Mory\'s. Nothing but crumbs!',
  'Boola boo-hoo! We don\'t have that one.',
  "I dug up half of Cross Campus looking. Don't tell the groundskeepers.",
  'Not here! It must have slipped out through Phelps Gate.',
]

export const FOUND_SAYINGS = [
  'I love the smell of Harvard defeat in the morning!',
  'Boola Boola! Look what I dug up!',
  'Lux et Veritas, and also these!',
  'Bright College Years? More like bright college gear!',
  'Fetched faster than a Sterling Library all-nighter!',
  'Handsome Dan approved. Harvard not invited.',
  'These pass my sniff test with flying colors. Yale Blue, obviously.',
  'Fresh finds, worth a victory lap around Old Campus!',
]

export function randomSaying(sayings: string[]): string {
  return sayings[Math.floor(Math.random() * sayings.length)]
}
