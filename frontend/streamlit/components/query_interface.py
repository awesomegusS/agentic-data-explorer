# frontend/streamlit/components/query_interface.py
"""
Query interface components for Streamlit frontend.
Handles user input, example queries, and result display.
"""

import streamlit as st
import requests
import pandas as pd
from typing import Dict, List, Any, Optional
import time
from datetime import datetime
from chart_builder import ChartBuilder

class QueryInterface:
    """Manages the query input interface and user interactions"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1"):
        self.api_base_url = api_base_url
        self.chart_builder = ChartBuilder()
        
        # Initialize session state
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'selected_question' not in st.session_state:
            st.session_state.selected_question = ""
    
    def render_query_input(self) -> Optional[str]:
        """Render the main query input interface"""
        
        st.subheader("🗣️ Ask Your Question")
        
        # Get default question from session state
        default_question = st.session_state.get('selected_question', '')
        
        # Main query input
        question = st.text_area(
            "Enter your question about the retail data:",
            value=default_question,
            height=100,
            placeholder="e.g., What was the total revenue last month?",
            help="Ask questions in natural language about sales, stores, products, or performance metrics."
        )
        
        # Clear the selected question after use
        if 'selected_question' in st.session_state and st.session_state.selected_question:
            st.session_state.selected_question = ""
        
        # Query options in columns
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Main query button
            query_button = st.button(
                "🔍 Ask Question", 
                type="primary", 
                disabled=not question.strip(),
                use_container_width=True
            )
        
        with col2:
            # Clear button
            if st.button("🗑️ Clear", use_container_width=True):
                st.rerun()
        
        with col3:
            # Random example button
            if st.button("🎲 Random Example", use_container_width=True):
                example_questions = self._get_example_questions()
                if example_questions:
                    import random
                    random_question = random.choice([
                        q for category in example_questions.values() 
                        for q in category
                    ])
                    st.session_state.selected_question = random_question
                    st.rerun()
        
        return question if query_button and question.strip() else None
    
    def render_query_options(self) -> Dict[str, Any]:
        """Render query configuration options"""
        
        with st.expander("⚙️ Query Options", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                max_rows = st.slider(
                    "Maximum Results", 
                    min_value=10, 
                    max_value=500, 
                    value=100, 
                    step=10,
                    help="Limit the number of rows returned"
                )
                
                include_sql = st.checkbox(
                    "Show Generated SQL", 
                    value=False,
                    help="Include the AI-generated SQL query in results"
                )
            
            with col2:
                timeout_seconds = st.slider(
                    "Query Timeout (seconds)", 
                    min_value=10, 
                    max_value=120, 
                    value=30,
                    help="Maximum time to wait for query completion"
                )
                
                chart_type = st.selectbox(
                    "Chart Type",
                    options=['auto', 'bar', 'line', 'pie', 'scatter', 'area', 'histogram'],
                    index=0,
                    help="Override automatic chart selection"
                )
        
        return {
            'max_rows': max_rows,
            'include_sql': include_sql,
            'timeout_seconds': timeout_seconds,
            'chart_type': chart_type
        }
    
    def render_example_queries(self):
        """Render example queries sidebar"""
        
        st.subheader("💡 Example Questions")
        
        example_questions = self._get_example_questions()
        
        if example_questions:
            # Search/filter examples
            search_term = st.text_input(
                "🔍 Search Examples", 
                placeholder="Filter examples...",
                label_visibility="collapsed"
            )
            
            for category, questions in example_questions.items():
                # Filter questions based on search
                if search_term:
                    filtered_questions = [
                        q for q in questions 
                        if search_term.lower() in q.lower()
                    ]
                else:
                    filtered_questions = questions[:5]  # Show first 5 per category
                
                if filtered_questions:
                    with st.expander(f"📈 {category}", expanded=False):
                        for question in filtered_questions:
                            if st.button(
                                f"💬 {question}", 
                                key=f"example_{hash(question)}",
                                use_container_width=True
                            ):
                                st.session_state.selected_question = question
                                st.rerun()
        
        else:
            # Fallback examples if API is unavailable
            st.info("💡 **Try asking questions like:**\n\n"
                   "• What was the total revenue last month?\n"
                   "• Show me the top 5 stores by sales\n"
                   "• Which product category has the highest sales?\n"
                   "• How do weekend sales compare to weekday sales?")
    
    def process_query(self, question: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Send query to API and return results"""
        
        try:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🤖 AI is analyzing your question...")
            progress_bar.progress(25)
            
            # Prepare request
            payload = {
                "question": question,
                "max_rows": options['max_rows'],
                "include_sql": options['include_sql'],
                "timeout_seconds": options['timeout_seconds']
            }
            
            status_text.text("🔗 Sending request to AI agent...")
            progress_bar.progress(50)
            
            # Send request
            start_time = time.time()
            response = requests.post(
                f"{self.api_base_url}/query",
                json=payload,
                timeout=options['timeout_seconds'] + 5
            )
            
            status_text.text("📊 Processing results...")
            progress_bar.progress(75)
            
            execution_time = (time.time() - start_time) * 1000
            
            progress_bar.progress(100)
            time.sleep(0.5)  # Brief pause for UX
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            if response.status_code == 200:
                result = response.json()
                
                # Add to query history
                self._add_to_history(question, result, True)
                
                return {
                    "success": True,
                    "data": result,
                    "execution_time": execution_time
                }
            else:
                error_detail = response.json().get("detail", "Unknown error")
                self._add_to_history(question, {"error": error_detail}, False)
                
                return {
                    "success": False,
                    "error": error_detail,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            error = "Query timed out. Try asking a simpler question."
            self._add_to_history(question, {"error": error}, False)
            return {"success": False, "error": error}
            
        except requests.exceptions.RequestException as e:
            error = f"Connection error: {str(e)}"
            self._add_to_history(question, {"error": error}, False)
            return {"success": False, "error": error}
    
    def render_results(self, question: str, result: Dict[str, Any], options: Dict[str, Any]):
        """Render query results with visualizations"""
        
        if result["success"]:
            data = result["data"]
            
            # Success message
            st.success(
                f"✅ **Query successful!** Found {data.get('row_count', 0)} results "
                f"in {data.get('execution_time_ms', 0):.1f}ms"
            )
            
            # Show SQL if requested
            if options['include_sql'] and data.get('sql_query'):
                with st.expander("📝 Generated SQL Query"):
                    st.code(data['sql_query'], language='sql')
            
            # Display results
            results = data.get('results', [])
            
            if results:
                self._render_result_tabs(question, results, options)
            else:
                st.warning("🤔 No results found. Try rephrasing your question or asking something else.")
        
        else:
            # Error handling
            error = result["error"]
            
            st.error(f"❌ **Query failed:** {error}")
            
            # Show suggestions if available
            if isinstance(error, dict) and error.get('suggestions'):
                st.write("**💡 Suggestions:**")
                for suggestion in error['suggestions']:
                    st.write(f"• {suggestion}")
    
    def _render_result_tabs(self, question: str, results: List[Dict], options: Dict[str, Any]):
        """Render results in tabbed interface"""
        
        tab1, tab2, tab3 = st.tabs(["📊 Visualization", "📋 Data Table", "📈 Summary"])
        
        with tab1:
            st.subheader("📊 Visualization")
            
            # Create visualization
            fig = self.chart_builder.create_visualization(
                results, 
                question, 
                options.get('chart_type', 'auto')
            )
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Chart type selector
                st.write("**Change Chart Type:**")
                chart_cols = st.columns(7)
                chart_types = ['bar', 'line', 'pie', 'scatter', 'area', 'histogram', 'box']
                
                for i, chart_type in enumerate(chart_types):
                    with chart_cols[i]:
                        if st.button(f"{chart_type.title()}", key=f"chart_{chart_type}"):
                            new_fig = self.chart_builder.create_visualization(
                                results, question, chart_type
                            )
                            if new_fig:
                                st.plotly_chart(new_fig, use_container_width=True)
            else:
                st.info("💡 No suitable visualization found for this data. Check the Data Table tab.")
        
        with tab2:
            st.subheader("📋 Raw Data")
            df = pd.DataFrame(results)
            
            # Display dataframe with search
            if len(df) > 10:
                search_col = st.selectbox(
                    "Search in column:", 
                    options=[''] + list(df.columns),
                    key="search_column"
                )
                
                if search_col:
                    search_value = st.text_input(f"Search in {search_col}:")
                    if search_value:
                        df = df[df[search_col].astype(str).str.contains(search_value, case=False, na=False)]
            
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
                df = pd.DataFrame(results)
                
                col_info = []
                for col_name in df.columns:
                    col_type = str(df[col_name].dtype)
                    null_count = df[col_name].isnull().sum()
                    unique_count = df[col_name].nunique()
                    
                    col_info.append({
                        'Column': col_name,
                        'Type': col_type,
                        'Nulls': null_count,
                        'Unique Values': unique_count
                    })
                
                st.dataframe(pd.DataFrame(col_info), use_container_width=True)
            
            # Query metadata
            if data.get('metadata'):
                with st.expander("🔧 Query Metadata"):
                    metadata = data['metadata']
                    
                    metrics = {
                        "AI Model": metadata.get('ai_model'),
                        "SQL Generation Time": f"{metadata.get('sql_generation_time_ms', 0):.1f}ms",
                        "Database Query Time": f"{metadata.get('database_query_time_ms', 0):.1f}ms",
                        "Total Execution Time": f"{data.get('execution_time_ms', 0):.1f}ms"
                    }
                    
                    for key, value in metrics.items():
                        st.write(f"**{key}:** {value}")
    
    def render_query_history(self):
        """Render query history in sidebar"""
        
        if st.session_state.query_history:
            st.subheader("📚 Query History")
            
            # Clear history button
            if st.button("🗑️ Clear History"):
                st.session_state.query_history = []
                st.rerun()
            
            # Show recent queries (last 10)
            recent_queries = st.session_state.query_history[-10:]
            
            for i, entry in enumerate(reversed(recent_queries)):
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                success_icon = "✅" if entry['success'] else "❌"
                
                with st.expander(f"{success_icon} {timestamp} - {entry['question'][:50]}..."):
                    st.write(f"**Question:** {entry['question']}")
                    st.write(f"**Success:** {entry['success']}")
                    
                    if entry['success'] and 'row_count' in entry['result']:
                        st.write(f"**Rows:** {entry['result']['row_count']}")
                        st.write(f"**Time:** {entry['result'].get('execution_time_ms', 0):.1f}ms")
                    
                    # Re-run button
                    if st.button(f"🔄 Re-run", key=f"rerun_{i}"):
                        st.session_state.selected_question = entry['question']
                        st.rerun()
    
    def _get_example_questions(self) -> Dict[str, List[str]]:
        """Fetch example questions from API"""
        try:
            response = requests.get(f"{self.api_base_url}/query/examples", timeout=5)
            if response.status_code == 200:
                return response.json().get('categories', {})
        except:
            pass
        return {}
    
    def _add_to_history(self, question: str, result: Dict, success: bool):
        """Add query to history"""
        entry = {
            'question': question,
            'result': result,
            'success': success,
            'timestamp': datetime.now()
        }
        
        st.session_state.query_history.append(entry)
        
        # Keep only last 50 entries
        if len(st.session_state.query_history) > 50:
            st.session_state.query_history = st.session_state.query_history[-50:]