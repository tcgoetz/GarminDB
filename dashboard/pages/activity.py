from datetime import datetime, time

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import fitfile
from garmindb import ConfigManager, GarminConnectConfigManager
from garmindb.garmindb import (
    GarminDb,
    Attributes,
    ActivitiesDb,
    Activities,
    StepsActivities,
    ActivityLaps,
    ActivityRecords,
)
from idbutils.list_and_dict import list_not_none
from scipy.signal import savgol_filter
from utils import get_sport_icon, timestamp_to_seconds, timedelta_to_seconds


def compute_pace(speed, numeric=False):
    if speed == 0:
        # return 0 if not numeric else time(hour=0, minute=0, second=0)
        return 0
    km_minutes = 60 / speed
    minutes = int(km_minutes)
    seconds = (km_minutes - minutes) * 60
    if (seconds - int(seconds)) >= 0.5:
        seconds += 1
    if seconds >= 60:
        seconds = 59

    return (
        f"{minutes}m{seconds:.0f}s"
        if not numeric
        else minutes * 60 + seconds
        # else time(hour=0, minute=minutes, second=int(seconds))
    )


def get_activities():
    gc_config = GarminConnectConfigManager()
    db_params_dict = ConfigManager.get_db_params()

    garmin_db = GarminDb(db_params_dict)
    garmin_act_db = ActivitiesDb(db_params_dict)
    measurement_system = Attributes.measurements_type(garmin_db)
    unit_strings = fitfile.units.unit_strings[measurement_system]
    distance_units = unit_strings[fitfile.units.UnitTypes.distance_long]

    gc_config = GarminConnectConfigManager()
    db_params_dict = ConfigManager.get_db_params()
    activities = Activities.get_all(garmin_act_db)
    activities = list(map(lambda a: a.__dict__, activities))

    activities = pd.DataFrame(activities, columns=list(activities[0].keys()))
    activities.drop(
        columns=[
            "_sa_instance_state",
            "min_temperature",
            "max_temperature",
            "avg_temperature",
            "max_rr",
            "sub_sport",
            "type",
            "course_id",
            "avg_rr",
        ],
        inplace=True,
    )
    activities["pace"] = activities.avg_speed.apply(compute_pace)
    activities.sort_values("start_time", inplace=True, ascending=False)
    activities.set_index("activity_id", inplace=True)
    return activities


def get_activity_records(activity_id):
    db_params_dict = ConfigManager.get_db_params()
    garmin_act_db = ActivitiesDb(db_params_dict)
    records = ActivityRecords.get_activity(garmin_act_db, activity_id)
    return records


def print_activities(activities):
    cols = st.columns(5)
    fields = ["Display", "Name", "Date", "Sport", "Pace"]
    fields_name = ["name", "start_time", "sport", "pace"]
    act = activities[fields_name].copy(deep=True)
    act["start_time"] = act.start_time.apply(lambda x: x.strftime("%Y-%m-%d"))
    act["sport"] = act.sport.apply(get_sport_icon)

    for col, field in zip(cols, fields):
        col.write(f"**{field}**")

    if "start_id" not in st.session_state:
        st.session_state.start_id = 0
    if "end_id" not in st.session_state:
        st.session_state.end_id = 5

    def increment_ids():
        st.session_state.start_id += 5
        st.session_state.end_id += 5

    def decrement_ids():
        st.session_state.start_id -= 5
        st.session_state.end_id -= 5

    def update_selected_activity(activity_id):
        st.session_state.selected_activity = activities.loc[activity_id].to_dict()
        st.session_state.selected_activity["activity_id"] = activity_id

    for row in list(act.iterrows())[
        st.session_state.start_id : st.session_state.end_id
    ]:
        cols = st.columns(5)
        cols[0].button(
            "🔍",
            key=row[0],
            on_click=update_selected_activity,
            args=[row[0]],
        )
        for col, field in zip(cols[1:], row[1]):
            col.write(field)

    cols = st.columns(6)

    cols[2].button(
        "Prev", on_click=decrement_ids, disabled=st.session_state.start_id == 0
    )
    cols[4].button(
        "Next", on_click=increment_ids, disabled=len(act) <= st.session_state.end_id
    )


def activity_summary():
    cols = st.columns(4)
    cols[0].metric(
        label="👟 Pace",
        value=st.session_state.selected_activity["pace"],
    )
    cols[1].metric(
        label="🛣️ distance",
        value=f"{st.session_state.selected_activity['distance']:.2f} km",
    )
    cols[2].metric(
        label="🕘 total time",
        value=st.session_state.selected_activity["elapsed_time"].strftime("%H:%M:%S"),
    )
    cols[3].metric(
        label="🕘 moving time",
        value=st.session_state.selected_activity["moving_time"].strftime("%H:%M:%S"),
    )


def heart_rate_zones(col):
    activity = st.session_state.selected_activity
    zones = []
    for zone in ["hrz_1_time", "hrz_2_time", "hrz_3_time", "hrz_4_time", "hrz_5_time"]:
        zones.append(timestamp_to_seconds(activity[zone]))

    rows = [
        ["Zone 1", zones[0], activity["hrz_1_time"].strftime("%H:%M:%S")],
        ["Zone 2", zones[1], activity["hrz_2_time"].strftime("%H:%M:%S")],
        ["Zone 3", zones[2], activity["hrz_3_time"].strftime("%H:%M:%S")],
        ["Zone 4", zones[3], activity["hrz_4_time"].strftime("%H:%M:%S")],
        ["Zone 5", zones[4], activity["hrz_5_time"].strftime("%H:%M:%S")],
    ]
    df = pd.DataFrame(rows, columns=["Names", "Values", "Values formatted"])
    fig = px.pie(
        df,
        values="Values",
        names="Names",
        hover_data=["Values formatted"],
    )
    fig.update_layout(font=dict(size=21), legend=dict(font=dict(size=15)))
    col.plotly_chart(fig, theme="streamlit", use_container_width=True)


def heart_rate_plot(records, col):
    activity = st.session_state.selected_activity
    values = list(map(lambda x: x.hr, records))
    timestamps = list(
        map(
            lambda x: timedelta_to_seconds(x.timestamp - activity["start_time"]),
            records,
        )
    )
    fig = px.line(
        pd.DataFrame(zip(values, timestamps), columns=["Heart rate", "Time"]),
        y="Heart rate",
        x="Time",
    )
    fig.update_layout(font=dict(size=21), legend=dict(font=dict(size=15)))
    fig.update_xaxes(
        type="category", tickangle=-45, tickvals=timestamps[:: len(timestamps) // 10]
    )
    col.plotly_chart(fig, theme="streamlit", use_container_width=True)


def pace_plot(records):
    max_std_dev = st.slider(
        "Outlier removal", min_value=0.0, max_value=5.0, value=0.0, step=1.0
    )
    activity = st.session_state.selected_activity
    speeds = np.array(list(map(lambda x: x.speed, records)))
    mean, std_dev = np.mean(speeds), np.std(speeds)
    speeds_zero_based = np.abs(speeds - mean)
    values = list(map(lambda x: compute_pace(x, numeric=True), speeds))
    timestamps = np.array(
        list(
            map(
                lambda x: timedelta_to_seconds(x.timestamp - activity["start_time"]),
                records,
            )
        )
    )
    if max_std_dev != 0:
        timestamps = timestamps[
            speeds_zero_based < st.session_state.max_std_dev * std_dev
        ]
        speeds = speeds[speeds_zero_based < max_std_dev * std_dev]

    savgol_width = st.slider(
        "Smoothing window", min_value=0, max_value=len(values) // 10
    )
    savgol_order = st.slider(
        "Smoothing order",
        min_value=0,
        max_value=savgol_width if savgol_width > 0 else 1,
    )
    if savgol_width != 0:
        values = savgol_filter(values, savgol_width, savgol_order)
    values_str = list(map(lambda x: compute_pace(x), speeds))
    fig = px.line(
        pd.DataFrame(
            zip(values, values_str, timestamps),
            columns=["Pace", "Pace display", "Time"],
        ),
        y="Pace",
        x="Time",
        hover_data=["Pace display"],
    )
    fig.update_layout(font=dict(size=21), legend=dict(font=dict(size=15)))
    fig.update_xaxes(
        type="category", tickangle=-45, tickvals=timestamps[:: len(timestamps) // 10]
    )
    fig.update_yaxes(
        # type="category",
        # tickvals=list(map(lambda x: compute_pace(x.speed), records))[::50],
    )
    # st.table(pd.DataFrame(zip(values, timestamps), columns=["Pace", "Time"]))
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


def trajectory_map(records):
    lats = list(map(lambda x: x.position_lat, records))
    longs = list(map(lambda x: x.position_long, records))
    speeds = np.array(list(map(lambda x: x.speed, records)))
    df = pd.DataFrame(zip(lats, longs, speeds), columns=["Lat", "Lon", "Speed"])
    fig = px.line_mapbox(df, lat="Lat", lon="Lon")
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=13,
        mapbox_center_lat=df.Lat.mean(),
        mapbox_center_lon=df.Lon.mean(),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    st.plotly_chart(
        fig, theme="streamlit", use_container_width=True, zoom=3, height=300
    )


activities = get_activities()
st.set_page_config(page_title="Activity analysis", page_icon="📈", layout="wide")
st.markdown("# Activity")
st.markdown("## Select an activity")
print_activities(activities)
if "selected_activity" not in st.session_state:
    st.session_state.selected_activity = activities.iloc[0].to_dict()
    st.session_state.selected_activity["activity_id"] = activities.index[0]
st.markdown(f"## Activity: {st.session_state.selected_activity['name']}")
activity_summary()

st.markdown("### HR")
cols = st.columns(2)
heart_rate_zones(cols[0])
records = get_activity_records(st.session_state.selected_activity["activity_id"])
heart_rate_plot(records, cols[1])

st.markdown("### Pace")
pace_plot(records)
# st.write(records[0])
# st.write(st.session_state.selected_activity)
st.markdown("### Map")
trajectory_map(records)
