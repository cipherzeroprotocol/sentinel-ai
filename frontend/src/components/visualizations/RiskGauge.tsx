"use client";

import React, { useEffect, useRef } from 'react';
// Import specific D3 modules
import { scaleLinear } from 'd3-scale';
import { arc } from 'd3-shape';
import { select } from 'd3-selection';

interface RiskGaugeProps {
  score: number;
  size?: number;
  label?: string;
  minValue?: number;
  maxValue?: number;
  decimalPlaces?: number;
}

const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  size = 200,
  label = "Risk Score",
  minValue = 0,
  maxValue = 100,
  decimalPlaces = 0
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  // Ensure score is between min and max
  const normalizedScore = Math.max(minValue, Math.min(maxValue, score));
  
  useEffect(() => {
    if (!svgRef.current) return;

    // Clear previous rendering
    select(svgRef.current).selectAll('*').remove();
    
    // Set up dimensions
    const width = size;
    const height = size;
    const radius = Math.min(width, height) / 2;
    const innerRadius = radius * 0.6;
    
    // Create SVG using select
    const svg = select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2})`);
      
    // Create a scale for the gauge using scaleLinear
    const scale = scaleLinear()
      .domain([minValue, maxValue])
      .range([-Math.PI / 2, Math.PI / 2]);
    
    // Create gauge background using arc
    const background = arc()
      .innerRadius(innerRadius)
      .outerRadius(radius)
      .startAngle(-Math.PI / 2)
      .endAngle(Math.PI / 2);
      
    // Create foreground arc based on score using arc
    const foreground = arc()
      .innerRadius(innerRadius)
      .outerRadius(radius)
      .startAngle(-Math.PI / 2)
      .endAngle(scale(normalizedScore));
      
    // Add background arc
    svg.append('path')
      .attr('d', background as any)
      .style('fill', '#e5e7eb');
      
    // Calculate color based on score
    let color = '#22c55e'; // Green for low risk
    if (normalizedScore > maxValue * 0.7) {
      color = '#ef4444'; // Red for high risk
    } else if (normalizedScore > maxValue * 0.4) {
      color = '#f59e0b'; // Yellow for medium risk
    }
    
    // Add foreground arc with color
    svg.append('path')
      .attr('d', foreground as any)
      .style('fill', color);
      
    // Add score text
    svg.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.3em')
      .attr('class', 'text-3xl font-bold')
      .style('fill', 'currentColor')
      .text(normalizedScore.toFixed(decimalPlaces));
      
    // Add label text
    svg.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.5em')
      .attr('class', 'text-sm')
      .style('fill', 'currentColor')
      .style('opacity', '0.7')
      .text(label);
      
    // Add tick marks
    const ticks = [0, 25, 50, 75, 100].filter(t => t >= minValue && t <= maxValue);
    
    ticks.forEach(tick => {
      const tickAngle = scale(tick);
      const x1 = (radius + 8) * Math.cos(tickAngle);
      const y1 = (radius + 8) * Math.sin(tickAngle);
      const x2 = (radius - 2) * Math.cos(tickAngle);
      const y2 = (radius - 2) * Math.sin(tickAngle);
      
      svg.append('line')
        .attr('x1', x2)
        .attr('y1', y2)
        .attr('x2', x1)
        .attr('y2', y1)
        .attr('stroke', 'currentColor')
        .attr('opacity', 0.3)
        .attr('stroke-width', 2);
        
      svg.append('text')
        .attr('x', (radius + 18) * Math.cos(tickAngle))
        .attr('y', (radius + 18) * Math.sin(tickAngle))
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('class', 'text-xs')
        .style('fill', 'currentColor')
        .style('opacity', '0.5')
        .text(tick);
    });
      
  }, [normalizedScore, size, label, minValue, maxValue, decimalPlaces]);
  
  return (
    <div className="flex flex-col items-center">
      <svg ref={svgRef} width={size} height={size} className="overflow-visible" />
    </div>
  );
};

export default RiskGauge;
