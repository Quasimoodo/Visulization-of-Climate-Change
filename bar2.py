import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time
from sklearn.linear_model import LinearRegression
# 创建虚构的数据集
Population_Finland =5550000
Population_World = 7e9
data = pd.DataFrame({
    'Category': ['Commute','Commute', 'Commute','Commute', 'Diet', 'Diet', 'Diet', 'Energy', 'Energy','Energy','Flights','Flights','Flights','Extra','Country Emission'],
    'Component': ['Driving(Petrol)','Driving(Electric)', 'Public Transit','Walking or Bicycle','Meat in most meals', 'Meat in some meals', 'Vegetarian', 'Around €10', '€10~€40','> €40','<10 hours','10~50 hours','>50 hours','Extra','Country Emission'],
    'Emission:ton/yr': [1.8, 0.2, 0.1, 0, 3, 2, 1, 0.4, 1.1, 2.5, 0.8, 4.2,9,3.5,2.5],
})
data['Choice']='You'
# 创建 Streamlit 应用
st.title('Your choice matters for climate change!')

col1, col2 = st.columns([2, 5])


color_scale = alt.Scale(domain=['Extra','Country Emission','Driving(Petrol)','Driving(Electric)', 'Public Transit','Walking or Bicycle','Meat in most meals', 'Vegetarian', 'Meat in some meals', 'Around €10', '€10~€40','> €40','<10 hours','10~50 hours','>50 hours'],
                        range=['grey','grey','red', 'orange','green','lightblue', 'red', 'lightblue','orange','lightblue','orange', 'red','lightblue','orange', 'red'])
color2 = alt.Scale(domain=['Historical','Predicted',"Changed"],
                   range = ['black','red','green'])
avg_data = pd.DataFrame({
    'Category': ['Commute','Diet', 'Energy','Flights','Extra','Country Emission'],
    'Component': ['Public Transit', 'Meat in some meals', '€10~€40','10~50 hours','Extra','Country Emission'],
    'Emission:ton/yr': [0.1,2,1.1,4.2,3.5,2.5],
    'Choice':['Average','Average','Average','Average','Average','Average']
})
#st.info("Your selection has been updated.")


#### load and predict
df2 =  pd.read_csv('annual_csv.csv')

# Linear Regression Model
model = LinearRegression()
X = df2[['Year']]  # Features matrix
y = df2['Mean']    # Target variable
model.fit(X, y)

# Predicting up to the year 2100
future_years = np.arange(2024, 2101).reshape(-1, 1)
predictions = model.predict(future_years)

# Adding random error
random_error = np.random.normal(0, 0.03, predictions.shape)  # Assuming std deviation is 0.1
predictions_with_error = predictions + random_error

# Ensuring that the prediction for 2100 is approximately 5.5
#predictions_with_error[-1] = 5.5 + np.random.normal(0, 0.1)


# Creating a DataFrame for the future predictions
future_df = pd.DataFrame({
    'Year': np.arange(2024, 2101),
    'Mean': predictions_with_error
})
diff_2023_2024 = future_df[future_df['Year'] == 2024]['Mean'].values[0] - df2[df2['Year'] == 2023]['Mean'].values[0]

# 将这个差值应用到2024年之后的所有预测数据上
future_df['Mean'] -= diff_2023_2024

df2['Type'] = 'Historical'
future_df['Type'] = 'Predicted'
y_df = None
# Combine historical and future data
complete_df = pd.concat([df2, future_df])

# Display the complete DataFrame
##print(complete_df)






####

with col1:
# 添加选择框，用于选择要显示或取消显示的数据
    st.header("Your choice:")
    commute_option = st.radio('Most common daily commute:', ['Public Transit','Driving(Petrol)','Driving(Electric)','Walking or Bicycle'])
    diet_options = st.radio('Most common Diet:', ['Meat in some meals','Meat in most meals', 'Vegetarian'])
    energy_options = st.radio('You spend ... on electric monthly:', ['Around €10','€10~€40','> €40'])
    flight_option = st.radio('In last years, you spent ... on flight', ['10~50 hours','<10 hours', '>50 hours'])
    #heating_options = st.selectbox('Heating:', ['Low Temp', 'High Temp'])
# 根据选择的数据过滤数据
filtered_data = data[(data['Component'].isin([commute_option])) |
                     ((data['Component'].isin([diet_options]))) |
                     ((data['Component'].isin([energy_options])))|
                     ((data['Component'].isin([flight_option])))
                     ]
filtered_data = pd.concat([filtered_data,data[data['Component']=='Extra']],ignore_index=True)
filtered_data = pd.concat([filtered_data,data[data['Component']=='Country Emission']],ignore_index=True)
#print(filtered_data)
filtered_data=filtered_data.reset_index(drop=True)

combined_data = pd.concat([filtered_data, avg_data])

#(combined_data)
sum = filtered_data['Emission:ton/yr'].sum()
sum = round(sum,2)
change =0
if 'sum' not in st.session_state:
    st.session_state['sum'] = sum
    #y_df = future_df
if sum > st.session_state['sum']:
    message = st.empty()
    delta = sum - st.session_state['sum']
    count = delta*10
    count = round(count,1)
    message.error('You need to plant '+str(count)+ '🌳 to balance your emission!')
    st.session_state['sum'] = sum
    change =0
    time.sleep(2)
    message.empty()
elif sum < st.session_state['sum']:
    message = st.empty()
    delta = sum - st.session_state['sum']
    count = delta*-10
    count = round(count, 1)
    message.success('Your choice worth '+str(count)+' 🌳!')
    st.session_state['sum'] = sum
    minus = delta*-1
    #ton->gram
    minus *= 3000000
    #popluation
    minus *= Population_World
    minus /=44.01
    minus /=1.8e20
    y_df = future_df.copy()
    y_df['Mean']-=minus*10000
    change =1
    ##
    #y_df['Mean']-=1
    y_df['Type'] = 'Changed'
    time.sleep(2)
    message.empty()


with col2:
# 使用 Altair 创建交互式散点图

    st.header("Your Carbon Emission:")
    if 'sum' not in st.session_state:
        st.caption('Your annual carbon emissions will be ... tons.')
    else:
        st.caption('Your annual carbon emissions will be '+str(sum)+' tons.')

    # sort_order = ['Extra','Country Emission'] + [item for item in combined_data['Component'].unique() if item not in ['Extra','Country Emission']]
    top_categories = combined_data[combined_data['Component'].isin(['Extra', 'Country Emission'])]
    other_categories = combined_data[~combined_data['Component'].isin(['Extra', 'Country Emission'])]
    sorted_combined_data = pd.concat([other_categories, top_categories])
    chart = alt.Chart(sorted_combined_data).mark_bar(
        stroke='white',  # 设置条形图的边框颜色
        strokeWidth=0.4,  # 设置条形图边框的宽度
        size=40
    ).encode(
        #y='sum(Emission:kg/yr):Q',  # Y轴上显示的是yield的总和
        y=alt.Y('sum(Emission:ton/yr):Q', scale=alt.Scale(domain=(0, 25))),  # 设置X轴的范围为0到200
        #x='Category:N',     # X轴上显示的是variety
        x = 'Choice:N',
        color=alt.Color('Component:N', scale=color_scale),     # 使用site列来区分不同堆叠的部分
        #color=alt.Color('EmissionLevel:N', scale=color_scale),  # 使用排放等级来设置颜色
        #tooltip=['Option:N', 'CarbonEmission:Q', 'EmissionLevel:N']
    ).properties(
        width=600,  # 设置图表的宽度
        height=500  # 设置图表的高度
    )


    chart

### line chart
c2 = st.container()
with c2:
    st.header('Global Warming Tendency releated to YOU!')
    if change==1:
        st.subheader(':green[If people all over the world make the same difference...]')

    st.caption('Monthly mean temperature anomalies in degrees Celisius to a base period')
    historical_chart = alt.Chart(df2).mark_line(

        #strokeDash = [1, 1]
    ).encode(
        color=alt.Color('Type:N', scale=color2),  # Historical data in blue
        x='Year:Q',
        y='Mean:Q'
    ).properties(
        width=800,  # 设置图表的宽度
        height=380  # 设置图表的高度
    )

    # Create the line chart for predicted data
    predicted_chart = alt.Chart(future_df).mark_line(
        strokeDash=[1, 1]
    ).encode(
        color=alt.Color('Type:N', scale=color2),  # Predicted data in red
        x='Year:Q',
        y='Mean:Q'
    ).properties(
        width=800,  # 设置图表的宽度
        height=380  # 设置图表的高度
    )
    if y_df is not None:
        print(predicted_chart)
        print('00000000000000000')
        print(future_df)
        changed_chart = alt.Chart(y_df).mark_line(
            strokeDash=[3, 3]
        ).encode(
            color=alt.Color('Type:N', scale=color2),  # Predicted data in red
            x='Year:Q',
            y='Mean:Q'
        ).properties(
            width=800,  # 设置图表的宽度
            height=380  # 设置图表的高度
        )
        combined_chart = alt.layer(historical_chart, predicted_chart, changed_chart)

    ###

    else:
        combined_chart = alt.layer(historical_chart, predicted_chart)


# Display the chart
    combined_chart