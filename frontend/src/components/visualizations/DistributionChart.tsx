"use client";

import React, { useRef, useEffect, useState } from 'react';
// Import specific D3 modules
import { scaleBand, scaleLinear, scaleOrdinal } from 'd3-scale';
import { schemeCategory10 } from 'd3-scale-chromatic';
import { axisBottom, axisLeft } from 'd3-axis';
import { select } from 'd3-selection';
import { sum, max } from 'd3-array';

interface DistributionItem {
  name: string;
  value: number;
  color?: string;
}

interface DistributionChartProps {
  data: DistributionItem[];
  height?: number;
  title?: string;
  showLegend?: boolean;
  interactive?: boolean;
}

const DistributionChart: React.FC<DistributionChartProps> = ({
  data = [],
  height = 300,
  title,
  showLegend = true,
  interactive = false
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  
  // Get container width
  useEffect(() => {
    if (containerRef.current) {
      const resizeObserver = new ResizeObserver(entries => {
        if (!entries.length) return;
        const { width } = entries[0].contentRect;
        setContainerWidth(width);
      });
      
      resizeObserver.observe(containerRef.current);
      return () => resizeObserver.disconnect();
    }
  }, []);

  // Draw chart
  useEffect(() => {
    if (!svgRef.current || !containerWidth || data.length === 0) return;

    // Clear previous chart using select
    select(svgRef.current).selectAll('*').remove();
    
    // Setup dimensions
    const margin = { top: 20, right: 20, bottom: 60, left: 60 };
    const width = containerWidth - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Create SVG using select
    const svg = select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', chartHeight + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Prepare data using sum and max
    const total = sum(data, d => d.value);
    const sortedData = [...data].sort((a, b) => b.value - a.value);
    // Use imported scaleOrdinal and schemeCategory10
    const colorScale = scaleOrdinal(schemeCategory10);
    
    // Prepare scales using scaleBand and scaleLinear
    const x = scaleBand()
      .domain(sortedData.map(d => d.name))
      .range([0, width])
      .padding(0.3);
      
    const y = scaleLinear()
      .domain([0, max(sortedData, d => d.value) || 1])
      .range([chartHeight, 0]);
    
    // Add x axis using axisBottom
    svg.append('g')
      .attr('transform', `translate(0, ${chartHeight})`)
      .call(axisBottom(x))
      .selectAll('text')
      .attr('transform', 'translate(-10,0)rotate(-45)')
      .style('text-anchor', 'end')
      .style('font-size', '10px');
      
    // Add y axis using axisLeft
    svg.append('g')
      .call(axisLeft(y));
      
    // Add bars
    svg.selectAll('rect')
      .data(sortedData)
      .enter()
      .append('rect')
      .attr('x', d => x(d.name) || 0)
      .attr('y', d => y(d.value))
      .attr('width', x.bandwidth())
      .attr('height', d => chartHeight - y(d.value))
      .attr('fill', (d, i) => d.color || colorScale(i.toString()))
      .attr('class', interactive ? 'cursor-pointer' : '');
    
    if (interactive && tooltipRef.current) {
      const tooltip = tooltipRef.current;
      
      svg.selectAll<SVGRectElement, DistributionItem>('rect') // Specify types for selection
        .on('mousemove', (event, d: DistributionItem) => { // Explicitly type 'd'
          // Ensure total is not zero to avoid division by zero
          const percentage = total ? ((d.value / total) * 100).toFixed(1) : '0.0';
          tooltip.style.display = 'block';
          tooltip.style.left = `${event.pageX + 10}px`;
          tooltip.style.top = `${event.pageY + 10}px`;
          tooltip.innerHTML = `
            <div class="font-medium">${d.name}</div>
            <div>Value: ${d.value.toLocaleString()}</div>
            <div>Percentage: ${percentage}%</div>
          `;
        })
        .on('mouseout', () => {
          tooltip.style.display = 'none';
        });
    }

    // Add legend if requested
    if (showLegend && sortedData.length > 0) {
      const legendItemWidth = 150;
      const legendItemHeight = 20;
      const legendColumns = Math.floor(width / legendItemWidth) || 1;
      
      const legend = svg.append('g')
        .attr('transform', `translate(0, ${chartHeight + 30})`);
      
      sortedData.forEach((d, i) => {
        const column = i % legendColumns;
        const row = Math.floor(i / legendColumns);
        
        const legendItem = legend.append('g')
          .attr('transform', `translate(${column * legendItemWidth}, ${row * legendItemHeight})`);
        
        legendItem.append('rect')
          .attr('width', 12)
          .attr('height', 12)
          .attr('fill', d.color || colorScale(i.toString()));
          
        legendItem.append('text')
          .attr('x', 18)
          .attr('y', 10)
          .attr('font-size', '10px')
          .text(`${d.name.length > 15 ? d.name.substring(0, 12) + '...' : d.name}`);
      });
    }
    
  }, [data, containerWidth, height, showLegend, interactive]);
  
  if (!data.length) {
    return (
      <div className="flex items-center justify-center bg-gray-50 dark:bg-gray-800/50 rounded-md p-4" style={{ height }}>
        <p className="text-gray-500 dark:text-gray-400 text-center">No distribution data available</p>
      </div>
    );
  }
  
  return (
    <div ref={containerRef} className="w-full">
      {title && <h4 className="text-base font-medium mb-2">{title}</h4>}
      <div className="w-full bg-white dark:bg-gray-800 rounded-md">
        <svg ref={svgRef} />
        {interactive && <div ref={tooltipRef} className="absolute bg-white dark:bg-gray-800 p-2 rounded shadow-lg border border-gray-200 dark:border-gray-700 text-sm hidden" />}
      </div>
    </div>
  );
};

export default DistributionChart;
