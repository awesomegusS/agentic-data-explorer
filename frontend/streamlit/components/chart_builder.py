# frontend/streamlit/components/chart_builder.py
"""
Smart chart building component for Streamlit frontend.
Automatically selects appropriate visualizations based on data and context.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime

class ChartBuilder:
    """Intelligent chart builder that selects appropriate visualizations"""
    
    def __init__(self):
        self.color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        # Chart type priorities based on data characteristics
        self.chart_priorities = {
            'time_series': ['line', 'area'],
            'comparison': ['bar', 'column'],
            'distribution': ['pie', 'donut', 'treemap'],
            'correlation': ['scatter', 'bubble'],
            'composition': ['stacked_bar', 'stacked_area']
        }
    
    def analyze_data_context(self, data: List[Dict], question: str) -> Dict[str, Any]:
        """Analyze data structure and question context to determine best visualization"""
        if not data:
            return {'type': 'no_data', 'reason': 'Empty dataset'}
        
        df = pd.DataFrame(data)
        question_lower = question.lower()
        
        # Analyze columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = []
        
        # Detect date columns
        for col in df.columns:
            if any(date_word in col.lower() for date_word in ['date', 'time', 'day', 'month', 'year']):
                try:
                    pd.to_datetime(df[col].iloc[0])
                    date_cols.append(col)
                except:
                    pass
        
        # Analyze question intent
        intent_patterns = {
            'trend': ['trend', 'over time', 'time series', 'monthly', 'daily', 'yearly', 'growth', 'change'],
            'comparison': ['compare', 'vs', 'versus', 'top', 'bottom', 'best', 'worst', 'highest', 'lowest'],
            'distribution': ['breakdown', 'distribution', 'by category', 'by region', 'segment', 'share'],
            'total': ['total', 'sum', 'overall', 'aggregate', 'combined'],
            'average': ['average', 'mean', 'typical', 'per'],
            'count': ['count', 'number of', 'how many']
        }
        
        detected_intent = []
        for intent, patterns in intent_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                detected_intent.append(intent)
        
        return {
            'df': df,
            'numeric_cols': numeric_cols,
            'categorical_cols': categorical_cols,
            'date_cols': date_cols,
            'row_count': len(df),
            'col_count': len(df.columns),
            'intent': detected_intent,
            'question': question_lower
        }
    
    def create_visualization(self, data: List[Dict], question: str, chart_type: str = 'auto') -> Optional[go.Figure]:
        """Create appropriate visualization based on data and context"""
        
        context = self.analyze_data_context(data, question)
        
        if context['type'] == 'no_data':
            return None
        
        df = context['df']
        
        # Auto-select chart type if not specified
        if chart_type == 'auto':
            chart_type = self._select_optimal_chart_type(context)
        
        try:
            # Route to specific chart creation method
            chart_methods = {
                'line': self._create_line_chart,
                'bar': self._create_bar_chart,
                'pie': self._create_pie_chart,
                'scatter': self._create_scatter_chart,
                'area': self._create_area_chart,
                'histogram': self._create_histogram,
                'box': self._create_box_plot,
                'heatmap': self._create_heatmap,
                'treemap': self._create_treemap,
                'gauge': self._create_gauge_chart
            }
            
            method = chart_methods.get(chart_type, self._create_bar_chart)
            fig = method(df, context)
            
            if fig:
                # Apply consistent styling
                self._apply_theme(fig, question)
                return fig
            
        except Exception as e:
            st.warning(f"Error creating {chart_type} chart: {str(e)}")
            # Fallback to simple table
            return None
        
        return None
    
    def _select_optimal_chart_type(self, context: Dict) -> str:
        """Select the best chart type based on data characteristics"""
        df = context['df']
        intent = context['intent']
        numeric_cols = context['numeric_cols']
        categorical_cols = context['categorical_cols']
        date_cols = context['date_cols']
        
        # Time series data
        if date_cols and numeric_cols and any(i in intent for i in ['trend', 'time']):
            return 'line'
        
        # Comparison queries
        if any(i in intent for i in ['comparison', 'top', 'bottom']) and categorical_cols and numeric_cols:
            if len(df) <= 10:
                return 'bar'
            else:
                return 'bar'  # Still bar, but we'll limit data
        
        # Distribution queries
        if any(i in intent for i in ['distribution', 'breakdown']) and categorical_cols and numeric_cols:
            if len(df) <= 8:
                return 'pie'
            else:
                return 'treemap'
        
        # Single metric
        if len(df) == 1 and len(numeric_cols) == 1:
            return 'gauge'
        
        # Default based on data structure
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            if len(df) <= 15:
                return 'bar'
            else:
                return 'treemap'
        elif len(numeric_cols) >= 2:
            return 'scatter'
        elif len(numeric_cols) == 1:
            return 'histogram'
        
        return 'bar'  # Safe default
    
    def _create_line_chart(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create line chart for time series data"""
        numeric_cols = context['numeric_cols']
        date_cols = context['date_cols']
        categorical_cols = context['categorical_cols']
        
        # Determine x and y axes
        if date_cols:
            x_col = date_cols[0]
        elif categorical_cols:
            x_col = categorical_cols[0]
        else:
            x_col = df.columns[0]
        
        y_col = numeric_cols[0] if numeric_cols else df.columns[1]
        
        # Handle grouping if needed
        if len(categorical_cols) > 1:
            group_col = [col for col in categorical_cols if col != x_col][0]
            fig = px.line(df, x=x_col, y=y_col, color=group_col,
                         title=f"{y_col} over {x_col}")
        else:
            fig = px.line(df, x=x_col, y=y_col,
                         title=f"{y_col} over {x_col}")
        
        return fig
    
    def _create_bar_chart(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create bar chart for comparisons"""
        numeric_cols = context['numeric_cols']
        categorical_cols = context['categorical_cols']
        
        if not numeric_cols or not categorical_cols:
            return None
        
        # Limit data for readability
        if len(df) > 20:
            df = df.nlargest(20, numeric_cols[0])
        
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        
        # Determine orientation based on category names length
        avg_length = df[x_col].astype(str).str.len().mean()
        horizontal = avg_length > 15
        
        if horizontal:
            fig = px.bar(df, y=x_col, x=y_col, orientation='h',
                        title=f"{y_col} by {x_col}")
        else:
            fig = px.bar(df, x=x_col, y=y_col,
                        title=f"{y_col} by {x_col}")
            # Rotate x-axis labels if needed
            if avg_length > 8:
                fig.update_layout(xaxis_tickangle=-45)
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create pie chart for distributions"""
        numeric_cols = context['numeric_cols']
        categorical_cols = context['categorical_cols']
        
        if not numeric_cols or not categorical_cols:
            return None
        
        # Limit to top categories for readability
        if len(df) > 8:
            df = df.nlargest(8, numeric_cols[0])
        
        fig = px.pie(df, values=numeric_cols[0], names=categorical_cols[0],
                    title=f"{numeric_cols[0]} Distribution by {categorical_cols[0]}")
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create scatter plot for correlations"""
        numeric_cols = context['numeric_cols']
        
        if len(numeric_cols) < 2:
            return None
        
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        
        # Add color grouping if categorical column available
        color_col = context['categorical_cols'][0] if context['categorical_cols'] else None
        
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col,
                        title=f"{y_col} vs {x_col}")
        
        return fig
    
    def _create_area_chart(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create area chart for cumulative data"""
        numeric_cols = context['numeric_cols']
        categorical_cols = context['categorical_cols']
        
        if not numeric_cols or not categorical_cols:
            return None
        
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        
        fig = px.area(df, x=x_col, y=y_col,
                     title=f"{y_col} Area Chart")
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create histogram for distributions"""
        numeric_cols = context['numeric_cols']
        
        if not numeric_cols:
            return None
        
        col = numeric_cols[0]
        fig = px.histogram(df, x=col, title=f"Distribution of {col}")
        
        return fig
    
    def _create_box_plot(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create box plot for statistical distributions"""
        numeric_cols = context['numeric_cols']
        categorical_cols = context['categorical_cols']
        
        if not numeric_cols:
            return None
        
        y_col = numeric_cols[0]
        x_col = categorical_cols[0] if categorical_cols else None
        
        fig = px.box(df, x=x_col, y=y_col,
                    title=f"Distribution of {y_col}")
        
        return fig
    
    def _create_heatmap(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create heatmap for correlation matrices"""
        numeric_cols = context['numeric_cols']
        
        if len(numeric_cols) < 2:
            return None
        
        corr_matrix = df[numeric_cols].corr()
        
        fig = px.imshow(corr_matrix, 
                       title="Correlation Heatmap",
                       color_continuous_scale='RdBu')
        
        return fig
    
    def _create_treemap(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create treemap for hierarchical data"""
        numeric_cols = context['numeric_cols']
        categorical_cols = context['categorical_cols']
        
        if not numeric_cols or not categorical_cols:
            return None
        
        # Limit data for performance
        if len(df) > 20:
            df = df.nlargest(20, numeric_cols[0])
        
        fig = px.treemap(df, 
                        path=[categorical_cols[0]], 
                        values=numeric_cols[0],
                        title=f"{numeric_cols[0]} Treemap by {categorical_cols[0]}")
        
        return fig
    
    def _create_gauge_chart(self, df: pd.DataFrame, context: Dict) -> go.Figure:
        """Create gauge chart for single metrics"""
        numeric_cols = context['numeric_cols']
        
        if not numeric_cols or len(df) != 1:
            return None
        
        value = df[numeric_cols[0]].iloc[0]
        
        # Determine gauge range (simple heuristic)
        max_value = max(value * 1.5, 100)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': numeric_cols[0]},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, max_value*0.5], 'color': "lightgray"},
                    {'range': [max_value*0.5, max_value*0.8], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value*0.9
                }
            }
        ))
        
        return fig
    
    def _apply_theme(self, fig: go.Figure, title: str):
        """Apply consistent theming to charts"""
        fig.update_layout(
            title={
                'text': title[:100] + "..." if len(title) > 100 else title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            template="plotly_white",
            height=500,
            margin=dict(l=50, r=50, t=80, b=50),
            font=dict(size=12),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update colors
        if hasattr(fig.data[0], 'marker'):
            if len(fig.data) == 1:
                fig.update_traces(marker_color=self.color_palette[0])
            else:
                fig.update_traces(marker=dict(
                    colorscale=[[0, self.color_palette[0]], [1, self.color_palette[1]]]
                ))

