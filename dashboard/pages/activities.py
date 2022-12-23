from sqlalchemy import column
from sqlalchemy.util import pickle
import streamlit as st
import pandas as pd

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

from utils import get_sport_icon

gc_config = GarminConnectConfigManager()
db_params_dict = ConfigManager.get_db_params()


garmin_db = GarminDb(db_params_dict)
garmin_act_db = ActivitiesDb(db_params_dict)
measurement_system = Attributes.measurements_type(garmin_db)
unit_strings = fitfile.units.unit_strings[measurement_system]
distance_units = unit_strings[fitfile.units.UnitTypes.distance_long]


def __report_sport(sport_col, sport):
    records = Activities.row_count(garmin_act_db, sport_col, sport)
    if records > 0:
        sport_title = sport.title().replace("_", " ")
        total_distance = Activities.get_col_sum_for_value(
            garmin_act_db, Activities.distance, sport_col, sport
        )
        if total_distance is None:
            total_distance = 0
            average_distance = 0
        else:
            average_distance = total_distance / records
        return [
            sport_title,
            records,
            total_distance,
            average_distance,
        ]


st.markdown("# Activities")
st.markdown("## Activities Report")
st.markdown("Analysis of all activities in the database.")

summary = pd.DataFrame(
    [
        ["Total activities", Activities.row_count(garmin_act_db)],
        ["Total Lap records", ActivityLaps.row_count(garmin_act_db)],
        ["Activity records", ActivityRecords.row_count(garmin_act_db)],
        [
            "Fitness activities",
            Activities.row_count(garmin_act_db, Activities.type, "fitness"),
        ],
        [
            "Recreation activities",
            Activities.row_count(garmin_act_db, Activities.type, "recreation"),
        ],
    ],
    columns=["Type", "Count"],
).set_index("Type")
st.table(summary)


years = Activities.get_years(garmin_act_db)
years.sort()
st.markdown(f"Years with activities: {len(years)}: {years}")
sports = list_not_none(Activities.get_col_distinct(garmin_act_db, Activities.sport))
sports = list(map(lambda x: f"{x}({get_sport_icon(x, True)})", sports))
st.markdown(f"Sports: {', '.join(sports)}")
sub_sports = list_not_none(
    Activities.get_col_distinct(garmin_act_db, Activities.sub_sport)
)
st.markdown(f"SubSports: {', '.join(sub_sports)}")


def compute_pace(speed):
    km_minutes = 60 / speed
    minutes = int(km_minutes)
    seconds = (km_minutes - int(km_minutes)) * 60
    if (seconds - int(seconds)) >= 0.5:
        seconds += 1

    return f"{minutes}m{seconds:.0f}s"


def __format_activity(activity):
    if activity:
        if activity.is_steps_activity():
            steps_activity = StepsActivities.get(garmin_act_db, activity.activity_id)
            pace_minutes_km = compute_pace(activity.avg_speed)
            return [
                activity.activity_id,
                activity.name,
                # activity.type,
                get_sport_icon(activity.sport),
                f"{activity.distance:.2f}",
                activity.elapsed_time.strftime("%H:%M:%S"),
                f"{activity.avg_speed:.2f}",
                pace_minutes_km,
                activity.calories,
            ]
        return [
            activity.activity_id,
            activity.name,
            # activity.type,
            activity.sport,
            f"{activity.distance:.2f}",
            activity.elapsed_time.strftime("%H:%M:%S"),
            f"{activity.avg_speed:.2f}",
            "",
            activity.calories,
        ]
    return ["", "", "", "", "", "", "", ""]


activities = Activities.get_latest(garmin_act_db, 10)
rows = [__format_activity(activity) for activity in activities]
st.markdown("## Last Ten Activities")
last_ten_activities = pd.DataFrame(
    rows,
    columns=[
        "Id",
        "Name",
        # "Type",
        "Sport",
        f"Distance ({distance_units})",
        "Elapsed Time",
        f"Speed ({unit_strings[fitfile.units.UnitTypes.speed]})",
        f"Pace m/km",
        "Calories",
    ],
).set_index("Id")
# st.dataframe(last_ten_activities, use_container_width=True)
cols = st.columns(8)
fields = [
    "Id",
    "Name",
    "Sport",
    f"Distance ({distance_units})",
    "Elapsed Time",
    f"Speed ({unit_strings[fitfile.units.UnitTypes.speed]})",
    f"Pace m/km",
    "Calories",
]

# header
for col, field in zip(cols, fields):
    col.write("**" + field + "**")

# rows
for row in last_ten_activities.iterrows():
    cols = st.columns(8)
    with cols[0]:
        st.button("🔍", key=row[0])
    for c, r in zip(cols[1:], row[1]):
        c.write(r)

rows = []
for display_activity in gc_config.display_activities():
    name = display_activity.activity_name().capitalize()
    rows.append(
        [f"Latest {name}"]
        + __format_activity(
            Activities.get_latest_by_sport(garmin_act_db, display_activity)
        )
    )
    rows.append(
        [f"Fastest {name}"]
        + __format_activity(
            Activities.get_fastest_by_sport(garmin_act_db, display_activity)
        )
    )
    rows.append(
        [f"Slowest {name}"]
        + __format_activity(
            Activities.get_slowest_by_sport(garmin_act_db, display_activity)
        )
    )
    rows.append(
        [f"Longest {name}"]
        + __format_activity(
            Activities.get_longest_by_sport(garmin_act_db, display_activity)
        )
    )

st.markdown("## Interesting Activities")
interesting_activities = pd.DataFrame(
    rows,
    columns=[
        "What",
        "Id",
        "Name",
        # "Type",
        "Sport",
        f"Distance ({distance_units})",
        "Elapsed Time",
        f"Speed ({unit_strings[fitfile.units.UnitTypes.speed]})",
        f"Pace m/km",
        "Calories",
    ],
)
st.table(interesting_activities)

# doc.add_header("Courses", 3)
# courses = Activities.get_col_distinct(garmin_act_db, Activities.course_id)
# doc.add_paragraph(str(courses))

# display(Markdown(str(doc)))

records = ActivityRecords.get_activity(garmin_act_db, 10167314721)
st.write(records[1])
activity = pd.DataFrame(
    [
        [
            "prova",
            (255, 0, 0),
            list(map(lambda x: [x.position.long_deg, x.position.lat_deg], records)),
        ]
    ],
    columns=["name", "color", "path"],
)

import pydeck as pdk

st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=activity.iloc[0]["path"][0][1],
            longitude=activity.iloc[0]["path"][0][0],
            zoom=13,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "PathLayer",
                data=activity,
                get_color="color",
                get_path="path",
                pickable=True,
                width_scale=1,
                width_min_pixels=1,
                get_width=1,
            ),
        ],
    )
)
