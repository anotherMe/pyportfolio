<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAllInstruments } from '@/services/instrumentsService'

interface Instrument {
  id: number
  isin: string | null
  ticker: string | null
  name: string
  currency: string | null
}

const instruments = ref<Instrument[]>([])
const loading = ref(true)

onMounted(async () => {
  instruments.value = await getAllInstruments()
  loading.value = false
})
</script>

<template>
  <section class="p-6">
    <h1 class="text-2xl font-semibold mb-2">🔧 Instruments</h1>
    <h2 class="text-lg mb-4 text-gray-600">Instruments list</h2>

    <div v-if="loading" class="text-gray-500">Loading…</div>
    <div v-else-if="!instruments.length" class="text-gray-500">No instruments found.</div>

    <table v-else class="min-w-full border border-gray-300 rounded-xl text-sm">
      <thead class="bg-gray-100">
        <tr>
          <th class="text-left p-2">ISIN</th>
          <th class="text-left p-2">Ticker</th>
          <th class="text-left p-2">Name</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="inst in instruments" :key="inst.id" class="border-t">
          <td class="p-2">
            <a v-if="inst.isin" :href="`https://www.justetf.com/en/etf-profile.html?isin=${inst.isin}`" target="_blank" class="text-blue-600 hover:underline">
              {{ inst.isin }}
            </a>
          </td>
          <td class="p-2">
            <a v-if="inst.ticker" :href="`https://finance.yahoo.com/quote/${inst.ticker}`" target="_blank" class="text-blue-600 hover:underline">
              {{ inst.ticker }}
            </a>
          </td>
          <td class="p-2">{{ inst.name }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
table {
  border-collapse: collapse;
  width: 100%;
}
</style>
