<template>
  <div class="flex min-h-screen bg-bnk-gray">
    <Sidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <Header />
      <main class="flex-1 overflow-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'
</script>
