import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI  # AI ინტეგრაციისთვის

# ──────────────────────────────────────────
# PAGE SETTINGS
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Baby Food Price Monitoring",
    page_icon="👶",
    layout="wide"
)

st.title("👶 Baby Food Price Monitoring Dashboard")
st.write("📊 Category Manager Analytics — Aversi")

# ──────────────────────────────────────────
# LOAD & CLEAN DATA (EXPERT APPROACH)
# ──────────────────────────────────────────
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    
    # სვეტების სახელების სტანდარტიზაცია (Pro-tip: აცილებს space-ების პრობლემას)
    df.columns = df.columns.str.strip().str.upper()
    
    if 'PRICE' not in df.columns or 'BRAND' not in df.columns:
        st.error("Error: Excel file must contain 'BRAND' and 'PRICE' columns!")
        return pd.DataFrame()

    # ფასების სვეტის სუფთა გაწმენდა ვექტორიზებულად
    df['PRICE'] = (
        df['PRICE']
        .astype(str)
        .str.replace('₾', '', regex=False)
        .str.replace('"', '', regex=False)
        .str.strip()
    )
    df['PRICE'] = pd.to_numeric(df['PRICE'], errors='coerce')
    
    # ნულოვანი და არასწორი ჩანაწერების მოცილება
    df = df.dropna(subset=['PRICE', 'BRAND'])
    df = df[df['PRICE'] > 0]
    
    # ფასების სეგმენტაცია pd.cut()-ით (ბევრად სწრაფია, ვიდრე .apply())
    bins = [0, 3, 7, 15, float('inf')]
    labels = ["Budget (< 3₾)", "Mid Range (3-7₾)", "Premium (7-15₾)", "Luxury (> 15₾)"]
    df['SEGMENT'] = pd.cut(df['PRICE'], bins=bins, labels=labels)
    
    return df

# ──────────────────────────────────────────
# SIDEBAR CONFIGURATION
# ──────────────────────────────────────────
uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx", "xls"])

# AI პარამეტრები გვერდითა პანელში
st.sidebar.title("🤖 AI Config")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key to unlock the AI Chatbot")

if uploaded_file:
    df = load_data(uploaded_file)
    
    if not df.empty:
        # ──────────────────────────────────────
        # SIDEBAR FILTERS
        # ──────────────────────────────────────
        st.sidebar.title("🔎 Filters")

        brands = sorted(df['BRAND'].unique().tolist())
        selected_brands = st.sidebar.multiselect(
            "Select Brands",
            options=brands,
            default=brands
        )

        price_min = float(df['PRICE'].min())
        price_max = float(df['PRICE'].max())
        price_range = st.sidebar.slider(
            "Price Range (₾)",
            min_value=price_min,
            max_value=price_max,
            value=(price_min, price_max)
        )

        # ფილტრების გამოყენება
        filtered_df = df[
            (df['BRAND'].isin(selected_brands)) &
            (df['PRICE'] >= price_range[0]) &
            (df['PRICE'] <= price_range[1])
        ].copy()

        # ──────────────────────────────────────
        # KPI METRICS
        # ──────────────────────────────────────
        st.subheader("📊 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Products", f"{len(filtered_df):,}")
        with col2:
            st.metric("Total Brands", filtered_df['BRAND'].nunique())
        with col3:
            st.metric("Avg Price", f"{filtered_df['PRICE'].mean():.2f} ₾")
        with col4:
            st.metric("Min Price", f"{filtered_df['PRICE'].min():.2f} ₾")
        with col5:
            st.metric("Max Price", f"{filtered_df['PRICE'].max():.2f} ₾")

        st.divider()

        # ──────────────────────────────────────
        # CHARTS ROW 1
        # ──────────────────────────────────────
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏷️ Products per Brand")
            brand_counts = filtered_df['BRAND'].value_counts().reset_index(name='COUNT')
            fig1 = px.bar(
                brand_counts,
                x='COUNT', y='BRAND',
                orientation='h',
                color='COUNT',
                color_continuous_scale='Blues',
                template="plotly_white"
            )
            fig1.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("💰 Average Price per Brand")
            avg_price = filtered_df.groupby('BRAND')['PRICE'].mean().reset_index(name='AVG_PRICE')
            fig2 = px.bar(
                avg_price,
                x='AVG_PRICE', y='BRAND',
                orientation='h',
                color='AVG_PRICE',
                color_continuous_scale='Oranges',
                template="plotly_white"
            )
            fig2.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)

        # ──────────────────────────────────────
        # CHARTS ROW 2
        # ──────────────────────────────────────
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🥧 Market Share by Brand")
            fig3 = px.pie(
                brand_counts,
                names='BRAND', values='COUNT',
                hole=0.4,  # Donut chart უფრო თანამედროვეა
                template="plotly_white"
            )
            fig3.update_layout(height=400)
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            st.subheader("📦 Price Distribution")
            fig4 = px.box(
                filtered_df,
                x='BRAND', y='PRICE',
                color='BRAND',
                template="plotly_white"
            )
            fig4.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig4, use_container_width=True)

        # ──────────────────────────────────────
        # PRICE SEGMENTS
        # ──────────────────────────────────────
        st.subheader("💎 Price Segments")
        col1, col2 = st.columns(2)

        with col1:
            segment_counts = filtered_df['SEGMENT'].value_counts().reset_index(name='COUNT')
            fig5 = px.pie(
                segment_counts,
                names='SEGMENT', values='COUNT',
                color='SEGMENT',
                color_discrete_map={
                    'Budget (< 3₾)': '#2ecc71',
                    'Mid Range (3-7₾)': '#3498db',
                    'Premium (7-15₾)': '#9b59b6',
                    'Luxury (> 15₾)': '#e74c3c'
                },
                template="plotly_white"
            )
            fig5.update_layout(height=350)
            st.plotly_chart(fig5, use_container_width=True)

        with col2:
            segment_brand = filtered_df.groupby(['BRAND', 'SEGMENT'], observed=False).size().reset_index(name='COUNT')
            fig6 = px.bar(
                segment_brand,
                x='BRAND', y='COUNT',
                color='SEGMENT',
                barmode='stack',
                template="plotly_white"
            )
            fig6.update_layout(height=350, xaxis_tickangle=-45)
            st.plotly_chart(fig6, use_container_width=True)

        # ──────────────────────────────────────
        # TOP & BOTTOM PRODUCTS
        # ──────────────────────────────────────
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔝 Top 10 Most Expensive Products")
            top10 = filtered_df.nlargest(10, 'PRICE')[['BRAND', 'PRICE']].reset_index(drop=True)
            top10.index += 1
            st.dataframe(top10, use_container_width=True)

        with col2:
            st.subheader("💚 Top 10 Cheapest Products")
            bottom10 = filtered_df.nsmallest(10, 'PRICE')[['BRAND', 'PRICE']].reset_index(drop=True)
            bottom10.index += 1
            st.dataframe(bottom10, use_container_width=True)

        # ──────────────────────────────────────
        # BRAND COMPARISON TABLE
        # ──────────────────────────────────────
        st.divider()
        st.subheader("📋 Brand Comparison Table")

        brand_summary = filtered_df.groupby('BRAND').agg(
            Products=('PRICE', 'count'),
            Avg_Price=('PRICE', 'mean'),
            Min_Price=('PRICE', 'min'),
            Max_Price=('PRICE', 'max'),
            Total_Value=('PRICE', 'sum')
        ).round(2).reset_index()

        brand_summary.columns = ['Brand', 'Products', 'Avg Price (₾)', 'Min Price (₾)', 'Max Price (₾)', 'Total Value (₾)']
        brand_summary = brand_summary.sort_values('Products', ascending=False)
        st.dataframe(brand_summary, use_container_width=True, index=False)

        # ──────────────────────────────────────
        # DOWNLOAD DATA
        # ──────────────────────────────────────
        st.divider()
        st.subheader("⬇️ Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name="baby_food_filtered.csv",
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="📥 Download Brand Summary (CSV)",
                data=brand_summary.to_csv(index=False).encode('utf-8'),
                file_name="brand_summary.csv",
                mime="text/csv"
            )

        # ──────────────────────────────────────
        # ADVANCED AI CHATBOT INTEGRATION
        # ──────────────────────────────────────
        st.divider()
        st.subheader("🤖 Chat with Your Advanced AI Analyst")

        if not openai_api_key:
            st.info("💡 Please enter your OpenAI API Key in the sidebar to activate the AI Analyst.")
        else:
            # სესიის ინიციალიზაცია ჩატისთვის
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": "Hello! I am your AI Category Management assistant. Ask me anything about this data!"}
                ]

            # ძველი მესიჯების ჩვენება
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

            # ახალი კითხვა მომხმარებლისგან
            if prompt := st.chat_input("How do our brands compare in the premium segment?"):
                with st.chat_message("user"):
                    st.write(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                # კონტექსტის მომზადება AI-სთვის (აგზავნის შეჯამებულ ციფრებს, რომ AI-მ ზუსტად იცოდეს პასუხი)
                data_context = brand_summary.to_string(index=False)
                total_products = len(filtered_df)
                avg_total_price = filtered_df['PRICE'].mean()

                system_prompt = f"""
                You are an expert Data Analyst and Category Manager working for Aversi pharmacy chain. 
                You are analyzing baby food price monitoring data.
                Here is the current filtered data summary:
                Total products listed: {total_products}
                Overall Average Price: {avg_total_price:.2f} GEL
                
                Brand Performance Summary:
                {data_context}
                
                Answer the user's questions accurately using this data. Be professional, concise, and business-oriented. 
                If asked in Georgian, answer in Georgian.
                """

                try:
                    client = OpenAI(api_key=openai_api_key)
                    
                    # API-ს გამოძახება
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        # Stream რეჟიმი ეფექტური ვიზუალიზაციისთვის
                        completion = client.chat.completions.create(
                            model="gpt-4o-mini", # ან "gpt-4" ბიუჯეტის მიხედვით
                            messages=[
                                {"role": "system", "content": system_prompt},
                                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                            ],
                            stream=True
                        )
                        
                        for chunk in completion:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                message_placeholder.write(full_response + "▌")
                        
                        message_placeholder.write(full_response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                except Exception as e:
                    st.error(f"AI Error: {str(e)}")

else:
    st.info("👆 Please upload your Excel file to get started!")
