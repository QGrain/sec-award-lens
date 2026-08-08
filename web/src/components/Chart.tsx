import * as echarts from "echarts/core";
import { BarChart, BoxplotChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useRef } from "react";
import type { EChartsCoreOption } from "echarts/core";

echarts.use([
  BarChart,
  BoxplotChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  CanvasRenderer,
]);

export function Chart({ option, height = 360, label }: { option: EChartsCoreOption; height?: number; label: string }) {
  const element = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!element.current) return;
    const chart = echarts.init(element.current, undefined, { renderer: "canvas" });
    chart.setOption(option);
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [option]);

  return <div className="chart" ref={element} style={{ height }} role="img" aria-label={label} />;
}
