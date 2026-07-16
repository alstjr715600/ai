<template>
  <header class="app-header">
    <RouterLink to="/map" class="logo">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 2C7.5 2 4 5.6 4 10c0 6 8 12 8 12s8-6 8-12c0-4.4-3.5-8-8-8Z" fill="#2f7a5c" />
        <circle cx="12" cy="10" r="3.2" fill="#fff" />
      </svg>
      LocalHub
    </RouterLink>

    <nav>
      <RouterLink to="/map">서울 지도</RouterLink>
      <RouterLink to="/facilities">시설 조회</RouterLink>
      <RouterLink to="/community">커뮤니티</RouterLink>
      <RouterLink to="/">조건 다시 입력</RouterLink>
    </nav>
  </header>
</template>
