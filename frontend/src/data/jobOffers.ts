import { JobOffer } from '../types';

export const jobOffers: JobOffer[] = [
  {
    id: 'job-001',
    title: 'Senior Frontend Engineer',
    department: 'Engineering',
    location: 'Paris / Hybride',
    contractType: 'CDI',
    experience: '5+ ans',
    salary_range: '65 000€ – 85 000€',
    description:
      'Nous recherchons un Senior Frontend Engineer passionné pour rejoindre notre équipe produit et contribuer à la construction d\'applications web de nouvelle génération. Vous travaillerez sur des projets impactants avec une stack moderne et une équipe de talent.',
    hardSkills: [
      'React',
      'TypeScript',
      'Next.js',
      'TailwindCSS',
      'GraphQL',
      'Jest / Vitest',
      'Git / CI/CD',
      'Accessibilité (a11y)',
    ],
    softSkills: [
      'Leadership technique',
      'Communication',
      'Mentorat',
      'Résolution de problèmes',
      'Travail d\'équipe',
      'Adaptabilité',
    ],
    requirements: [
      'Minimum 5 ans d\'expérience en développement frontend',
      'Maîtrise de React et TypeScript',
      'Expérience avec Next.js et les architectures modernes',
      'Connaissance des bonnes pratiques d\'accessibilité',
      'Anglais professionnel courant',
    ],
    responsibilities: [
      'Concevoir et développer des interfaces utilisateur performantes',
      'Participer aux décisions architecturales de la stack frontend',
      'Mentorer les développeurs plus juniors de l\'équipe',
      'Contribuer à la bibliothèque de composants interne',
      'Participer aux code reviews et à l\'amélioration continue',
    ],
  },
];
