# frontend/streamlit/demo_app.py
"""
🔍 Agentic Data Explorer - Streamlit Demo Application

Interactive dashboard for natural language querying of retail analytics data.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import json
from typing import Dict, Any, List, Optional

# Page configuration
st.set_page_config(
    page_title="🔍 Agentic Data Explorer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 1rem 0;
    }
    
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
        margin: 1rem 0;
    }
    
    .info-message {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        color: #0c5460;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health() -> Dict[str, Any]:
    """Check if the API is healthy and ready"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "data": response.json()}
        else:
            return {"status": "unhealthy", "error": f"API returned {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"status": "unreachable", "error": str(e)}

def query_api(question: str, max_rows: int = 100, include_sql: bool = False) -> Dict[str, Any]:
    """Send query to the API"""
    try:
        payload = {
            "question": question,
            "max_rows": max_rows,
            "include_sql": include_sql,
            "timeout_seconds": 30
        }
        
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=payload,
            timeout=35
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return {"success": False, "error": error_detail}
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Query timed out. Try asking a simpler question."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API request failed: {str(e)}"}

def get_example_queries() -> Dict[str, Any]:
    """Get example queries from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/query/examples", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except:
        return {}

def create_visualization(data: List[Dict], question: str) -> Optional[go.Figure]:
    """Create appropriate visualization based on the data and question"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    # Determine visualization type based on question and data
    question_lower = question.lower()
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(numeric_cols) == 0:
        return None
    
    fig = None
    
    try:
        # Time series patterns
        if any(word in question_lower for word in ['trend', 'time', 'month', 'year', 'day']):
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                time_col = categorical_cols[0]
                value_col = numeric_cols[0]
                fig = px.line(df, x=time_col, y=value_col, title=f"Trend: {value_col} over {time_col}")
        
        # Comparison patterns
        elif any(word in question_lower for word in ['top', 'bottom', 'best', 'worst', 'compare']):
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                cat_col = categorical_cols[0]
                value_col = numeric_cols[0]
                
                # Limit to top 10 for readability
                if len(df) > 10:
                    df_plot = df.nlargest(10, value_col)
                else:
                    df_plot = df
                
                fig = px.bar(df_plot, x=cat_col, y=value_col, 
                           title=f"{value_col} by {cat_col}")
                fig.update_xaxis(tickangle=45)
        
        # Category breakdown
        elif any(word in question_lower for word in ['category', 'segment', 'group', 'by']):
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                cat_col = categorical_cols[0]
                value_col = numeric_cols[0]
                
                if len(df) <= 15:  # Use pie chart for small number of categories
                    fig = px.pie(df, values=value_col, names=cat_col, 
                               title=f"{value_col} Distribution by {cat_col}")
                else:  # Use bar chart for many categories
                    fig = px.bar(df, x=cat_col, y=value_col, 
                               title=f"{value_col} by {cat_col}")
                    fig.update_xaxis(tickangle=45)
        
        # Default: simple bar chart
        else:
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                cat_col = categorical_cols[0]
                value_col = numeric_cols[0]
                
                fig = px.bar(df.head(20), x=cat_col, y=value_col, 
                           title=f"{value_col} by {cat_col}")
                fig.update_xaxis(tickangle=45)
        
        # Enhance the figure
        if fig:
            fig.update_layout(
                height=500,
                showlegend=True,
                title_x=0.5,
                font=dict(size=12),
                template="plotly_white"
            )
        
        return fig
        
    except Exception as e:
        st.warning(f"Could not create visualization: {str(e)}")
        return None

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🔍 Agentic Data Explorer</h1>', unsafe_allow_html=True)
    st.markdown("### 🤖 Ask questions about your retail data in natural language!")
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Configuration")
        
        # API Health Check
        st.subheader("🏥 System Health")
        if st.button("Check API Health"):
            with st.spinner("Checking API health..."):
                health = check_api_health()
                
                if health["status"] == "healthy":
                    st.success("✅ API is healthy and ready!")
                    health_data = health.get("data", {})
                    st.json({
                        "Status": health_data.get("status", "unknown"),
                        "Uptime": f"{health_data.get('uptime_seconds', 0):.1f}s",
                        "Services": health_data.get("services", {})
                    })
                else:
                    st.error(f"❌ API Health Issue: {health['error']}")
        
        st.divider()
        
        # Query Settings
        st.subheader("⚙️ Query Settings")
        max_rows = st.slider("Max Results", min_value=10, max_value=500, value=100, step=10)
        include_sql = st.checkbox("Show Generated SQL", value=False)
        
        st.divider()
        
        # Quick Actions
        st.subheader("🚀 Quick Actions")
        if st.button("🧪 Test AI Agent"):
            with st.spinner("Testing AI agent..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/query/test", timeout=15)
                    if response.status_code == 200:
                        test_results = response.json()
                        st.success("✅ AI Agent Test Complete!")
                        st.json(test_results)
                    else:
                        st.error("❌ AI Agent test failed")
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")
        
        if st.button("📊 View Database Schema"):
            with st.spinner("Loading schema..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/schema", timeout=10)
                    if response.status_code == 200:
                        schema = response.json()
                        st.success("✅ Schema loaded!")
                        
                        with st.expander("Database Schema Details"):
                            st.write(f"**Database:** {schema.get('database', 'Unknown')}")
                            st.write(f"**Total Tables:** {schema.get('summary', {}).get('total_tables', 0)}")
                            
                            for table_name, table_info in schema.get('tables', {}).items():
                                st.write(f"**{table_name.upper()}** ({table_info.get('type', 'TABLE')})")
                                cols = [col['name'] for col in table_info.get('columns', [])]
                                st.write(f"Columns: {', '.join(cols[:5])}" + ("..." if len(cols) > 5 else ""))
                    else:
                        st.error("❌ Failed to load schema")
                except Exception as e:
                    st.error(f"❌ Schema load failed: {str(e)}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("💡 Example Questions")
        
        # Load and display example queries
        examples = get_example_queries()
        
        if examples:
            categories = examples.get('categories', {})
            
            for category, questions in categories.items():
                with st.expander(f"📈 {category}"):
                    for question in questions[:3]:  # Show first 3 per category
                        if st.button(f"💬 {question}", key=f"example_{question[:20]}"):
                            st.session_state.selected_question = question
            
            # Tips
            if examples.get('tips'):
                with st.expander("💭 Tips for Better Questions"):
                    for tip in examples['tips']:
                        st.write(f"• {tip}")
        else:
            st.info("💡 **Try asking questions like:**\n\n"
                   "• What was the total revenue last month?\n"
                   "• Show me the top 5 stores by sales\n"
                   "• Which product category has the highest sales?\n"
                   "• How do weekend sales compare to weekday sales?")
    
    with col1:
        st.subheader("🗣️ Ask Your Question")
        
        # Question input
        default_question = st.session_state.get('selected_question', '')
        question = st.text_area(
            "Enter your question about the retail data:",
            value=default_question,
            height=100,
            placeholder="e.g., What was the total revenue last month?"
        )
        
        # Clear selected question after use
        if 'selected_question' in st.session_state:
            del st.session_state.selected_question
        
        # Query button
        if st.button("🔍 Ask Question", type="primary", disabled=not question.strip()):
            if question.strip():
                with st.spinner("🤖 AI is analyzing your question and generating SQL..."):
                    # Add progress bar
                    progress_bar = st.progress(0)
                    progress_bar.progress(25)
                    
                    # Query the API
                    result = query_api(question, max_rows, include_sql)
                    progress_bar.progress(100)
                    progress_bar.empty()
                    
                    if result["success"]:
                        data = result["data"]
                        
                        # Success message
                        st.markdown(f"""
                        <div class="success-message">
                            ✅ <strong>Query successful!</strong><br>
                            Found {data.get('row_count', 0)} results in {data.get('execution_time_ms', 0):.1f}ms
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show SQL if requested
                        if include_sql and data.get('sql_query'):
                            with st.expander("📝 Generated SQL Query"):
                                st.code(data['sql_query'], language='sql')
                        
                        # Display results
                        results = data.get('results', [])
                        
                        if results:
                            # Tabs for different views
                            tab1, tab2, tab3 = st.tabs(["📊 Visualization", "📋 Data Table", "📈 Summary"])
                            
                            with tab1:
                                st.subheader("📊 Visualization")
                                
                                # Create visualization
                                fig = create_visualization(results, question)
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("💡 No suitable visualization found for this data. Check the Data Table tab.")
                            
                            with tab2:
                                st.subheader("📋 Raw Data")
                                df = pd.DataFrame(results)
                                st.dataframe(df, use_container_width=True)
                                
                                # Download button
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download as CSV",
                                    data=csv,
                                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            
                            with tab3:
                                st.subheader("📈 Data Summary")
                                
                                # Basic statistics
                                col_a, col_b, col_c = st.columns(3)
                                
                                with col_a:
                                    st.metric("Total Rows", len(results))
                                
                                with col_b:
                                    st.metric("Total Columns", len(results[0].keys()) if results else 0)
                                
                                with col_c:
                                    complexity = data.get('complexity', 'unknown')
                                    st.metric("Query Complexity", complexity.title())
                                
                                # Column information
                                if results:
                                    st.write("**Column Information:**")
                                    for col_name, value in results[0].items():
                                        col_type = type(value).__name__
                                        st.write(f"• **{col_name}**: {col_type}")
                                
                                # Metadata
                                if data.get('metadata'):
                                    with st.expander("🔧 Query Metadata"):
                                        metadata = data['metadata']
                                        st.json({
                                            "AI Model": metadata.get('ai_model'),
                                            "SQL Generation Time": f"{metadata.get('sql_generation_time_ms', 0):.1f}ms",
                                            "Database Query Time": f"{metadata.get('database_query_time_ms', 0):.1f}ms",
                                            "Total Execution Time": f"{data.get('execution_time_ms', 0):.1f}ms"
                                        })
                        else:
                            st.warning("🤔 No results found. Try rephrasing your question or asking something else.")
                    
                    else:
                        # Error handling
                        error = result["error"]
                        
                        st.markdown(f"""
                        <div class="error-message">
                            ❌ <strong>Query failed:</strong><br>
                            {error.get('error', error) if isinstance(error, dict) else error}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show suggestions if available
                        if isinstance(error, dict) and error.get('suggestions'):
                            st.write("**💡 Suggestions:**")
                            for suggestion in error['suggestions']:
                                st.write(f"• {suggestion}")

    # Footer with statistics
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Query Statistics"):
            try:
                response = requests.get(f"{API_BASE_URL}/query/stats", timeout=5)
                if response.status_code == 200:
                    stats = response.json()['statistics']
                    st.json(stats)
            except:
                st.error("Failed to load statistics")
    
    with col2:
        st.write("**🔗 API Endpoints:**")
        st.write("• Health: `/health`")
        st.write("• Query: `/query`")
        st.write("• Examples: `/query/examples`")
    
    with col3:
        st.write("**🤖 Powered by:**")
        st.write("• Local AI (Ollama)")
        st.write("• Snowflake + dbt")
        st.write("• FastAPI + LangChain")

    # Auto-refresh option
    st.sidebar.divider()
    st.sidebar.subheader("🔄 Auto-Refresh")
    auto_refresh = st.sidebar.checkbox("Enable auto-refresh (30s)")
    
    if auto_refresh:
        time.sleep(30)
        st.experimental_rerun()

if __name__ == "__main__":
    # Initialize session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    main()