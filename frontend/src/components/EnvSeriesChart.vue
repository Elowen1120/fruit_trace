<template>
  <div class="ft-env-series-wrap">
    <p v-if="!hasRecords" class="small text-muted mb-0">暂无温湿度数据</p>
    <div v-else ref="chartEl" class="ft-env-chart" />
  </div>
</template>

<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps({
  /** 与 environmentSeries.storage / transport 单项结构一致：{ label, temp, humidity? } */
  records: { type: Array, default: () => [] },
});

const chartEl = ref(null);
let chartInstance = null;
let resizeObserver = null;

const hasRecords = computed(
  () => Array.isArray(props.records) && props.records.length > 0
);

function parseNum(v) {
  if (v == null || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function buildOption() {
  const cats = props.records.map((r) =>
    r?.label != null ? String(r.label) : ""
  );
  const temps = props.records.map((r) => parseNum(r?.temp));
  const hums = props.records.map((r) => parseNum(r?.humidity));
  const hasHumidity = hums.some((v) => v != null);

  const base = {
    tooltip: { trigger: "axis" },
    grid: {
      left: "3%",
      right: hasHumidity ? "8%" : "4%",
      bottom: "48",
      top: "14%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: cats,
      name: "时间",
      nameLocation: "middle",
      nameGap: 28,
    },
  };

  if (!hasHumidity) {
    return {
      ...base,
      color: ["#c44c4c"],
      legend: { data: ["温度(℃)"], bottom: 0 },
      yAxis: { type: "value", name: "温度(℃)" },
      series: [
        {
          name: "温度(℃)",
          type: "line",
          smooth: true,
          showSymbol: true,
          data: temps,
        },
      ],
    };
  }

  return {
    ...base,
    color: ["#c44c4c", "#4a8fd4"],
    legend: { data: ["温度(℃)", "湿度(%)"], bottom: 0 },
    yAxis: [
      { type: "value", name: "温度(℃)" },
      { type: "value", name: "湿度(%)" },
    ],
    series: [
      {
        name: "温度(℃)",
        type: "line",
        smooth: true,
        showSymbol: true,
        yAxisIndex: 0,
        data: temps,
      },
      {
        name: "湿度(%)",
        type: "line",
        smooth: true,
        showSymbol: true,
        yAxisIndex: 1,
        data: hums,
      },
    ],
  };
}

function disposeChart() {
  resizeObserver?.disconnect();
  resizeObserver = null;
  chartInstance?.dispose();
  chartInstance = null;
}

function resize() {
  chartInstance?.resize();
}

watch(
  () => props.records,
  async () => {
    await nextTick();
    if (!hasRecords.value) {
      disposeChart();
      return;
    }
    await nextTick();
    if (!chartEl.value) return;
    if (!chartInstance) {
      chartInstance = echarts.init(chartEl.value);
      window.addEventListener("resize", resize);
      if (typeof ResizeObserver !== "undefined") {
        resizeObserver = new ResizeObserver(() => resize());
        resizeObserver.observe(chartEl.value);
      }
    }
    chartInstance.setOption(buildOption(), true);
  },
  { deep: true, immediate: true, flush: "post" }
);

onUnmounted(() => {
  window.removeEventListener("resize", resize);
  disposeChart();
});
</script>

<style scoped>
.ft-env-chart {
  width: 100%;
  height: 220px;
  min-height: 180px;
}
</style>
