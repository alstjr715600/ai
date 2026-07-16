const DEFAULT_PROFILE = {
  child_age: 3,
  priorities: [
    { category: 'CHILDCARE', weight: 5 },
    { category: 'MEDICAL', weight: 4 },
    { category: 'PARK', weight: 3 }
  ],
  recommendation_count: 3
}

export function saveProfile(profile) {
  localStorage.setItem('YookA_Map-profile', JSON.stringify(profile))
}

export function getProfile() {
  const saved = localStorage.getItem('YookA_Map-profile')

  if (!saved) {
    return DEFAULT_PROFILE
  }

  try {
    return JSON.parse(saved)
  } catch {
    return DEFAULT_PROFILE
  }
}
