<template>
  <span :class="['countdown', { expired: remaining <= 0 }]">
    {{ displayText }}
  </span>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  paymentStartedAt: { type: String, default: '' },
  ttlSeconds: { type: Number, default: 600 },
})

const emit = defineEmits(['expired'])

const now = ref(Date.now())
let timer = null

const remaining = computed(() => {
  if (!props.paymentStartedAt) return props.ttlSeconds
  const start = new Date(props.paymentStartedAt).getTime()
  return Math.max(0, props.ttlSeconds - Math.floor((now.value - start) / 1000))
})

const displayText = computed(() => {
  if (remaining.value <= 0) return '已超时'
  const m = Math.floor(remaining.value / 60)
  const s = remaining.value % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

watch(remaining, (val) => {
  if (val <= 0) emit('expired')
})

onMounted(() => {
  timer = setInterval(() => { now.value = Date.now() }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.countdown {
  color: #f56c6c;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}
.countdown.expired {
  color: #c0c4cc;
}
</style>