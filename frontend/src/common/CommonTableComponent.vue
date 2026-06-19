<template>
  <div class="overflow-hidden rounded-lg border border-slate-200 bg-white">
    <table class="min-w-full divide-y divide-slate-200">
      <thead class="bg-slate-50">
        <tr>
          <slot name="head" />
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        <slot />
      </tbody>
    </table>
  </div>
</template>
